"""NginxCheckモジュール

Nginxのログ出力をPythonで検証する。
Dockerコンテナでの使用を想定
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ._sub import *


class NginxCheck:
    """Nginxのログ出力を監視・検証する。"""

    tasks: tuple[Task, ...]
    """開始時に実行するタスク"""
    timeTasks: tuple[TimeTask, ...]
    """一定時間毎に実行するタスク"""
    checkTasks: tuple[CheckTask, ...]
    """結果の検証に使用するタスク"""
    _event: threading.Event
    """サブプロセスの終了時、プログラム終了タイミングを調整するイベント"""
    _proc: subprocess.Popen[Any]
    """Nginxを実行するサブプロセス"""
    _errorWait: ErrorWait
    """サブスレッドでのエラー発生時に、プログラムを終了させる。"""
    _resetThread: ErrorWaitThread
    """一定時間毎にタスクを実行するスレッド"""
    _watchThread: ErrorWaitThread
    """Nginxの結果を監視・検証するスレッド"""
    _waitThread: ErrorWaitThread
    """Nginxの終了を検知するスレッド"""

    def __init__(self) -> None:
        taskList: list[Task] = []
        """開始時に実行するタスク"""
        timeTaskList: list[TimeTask] = []
        """一定時間毎に実行するタスク"""
        checkTaskList: list[CheckTask] = []
        """結果の検証に使用する。"""
        taskClass: Any
        """クラス変数"""

        baseClass: type
        key: str
        val: Any
        allDict: dict[str, Any] = {}
        
        for baseClass in self.__class__.__mro__:
            for key, val in baseClass.__dict__.items():
                if key not in allDict:
                    allDict[key] = val

        for taskClass in allDict.values():
            try:
                if issubclass(taskClass, Task):
                    taskList.append(taskClass())
                    if issubclass(taskClass, TimeTask):
                        timeTaskList.append(taskList[-1])  # type: ignore
                        if issubclass(taskClass, CheckTask):
                            checkTaskList.append(taskList[-1])  # type: ignore
            except TypeError:
                pass
        self.tasks = tuple(taskList)
        self.timeTasks = tuple(timeTaskList)
        self.checkTasks = tuple(checkTaskList)
        self._event = threading.Event()
        self._event.set()

    def _reset(self) -> None:
        """一定時間毎に``_timeTasks``を実行する。"""

        wait: float
        """待つ時間"""
        now: float = float(time.time())
        """今の時間"""

        wait = 3600 - (now % 3600)
        time.sleep(wait)
        self._timeTasks()
        subprocess.Popen(
            ["nginx", "-s", "reload"], stdout=sys.stdout, stderr=sys.stderr
        )

    def _resetRoop(self) -> None:
        """``_reset``を繰り返し実行する。"""

        while True:
            self._reset()

    def _timeTasks(self) -> None:
        """``timeTasks``を全て実行する。"""

        task: TimeTask
        """実行するタスク"""

        for task in self.timeTasks:
            task.timeTask()

    def _tasks(self) -> None:
        """``tasks``を全て実行する。"""

        task: Task
        """実行するタスク"""

        for task in self.tasks:
            task.setupTask()

    def _doChecks(self, text: str) -> CheckResult:
        """``checkTasks``を全て検証する。

        Args:
            text: 検証するテキスト

        Returns:
            検証結果
        """

        task: CheckTask
        """検証するタスク"""
        result: CheckResult
        """検証結果"""
        ans: CheckResult = CheckResult.NORMAL
        """関数の返り値"""

        for task in self.checkTasks:
            result = task.doCheck(text)
            if result == CheckResult.NORMAL:
                pass
            elif result == CheckResult.ERROR:
                ans = result
            else:
                return result

        return ans

    def _watch(self, r: int) -> None:
        """Nginxの出力を監視する。

        Args:
            r: パイプの読み込みポインタ
        """

        f: io.TextIOWrapper
        """テキストストリーム"""
        text: str
        """Nginxの出力"""
        result: CheckResult
        """検証結果"""

        with open(r, "r") as f:
            for text in f:
                print(text.rstrip("\n"), file=sys.stderr)
                result = self._doChecks(text)
                if result == CheckResult.NORMAL:
                    pass
                elif result == CheckResult.ERROR:
                    print("error", file=sys.stderr)
                else:
                    self._event.clear()
                    self._proc.kill()
                    print("error exit", file=sys.stderr)
                    break

    def _wait(self) -> None:
        """Nginxの終了を待って、プログラムを終了させる。"""

        self._proc.wait()
        self._event.wait()
        sys.exit(self._proc.returncode)

    def start(self) -> None:
        """監視・検証を開始する。"""

        r: int
        """パイプの読み込みポインタ"""
        w: int
        """パイプの書き込みポインタ"""

        try:
            os.remove(INPUT_SOCKET)

        except FileNotFoundError:
            os.makedirs(os.path.dirname(INPUT_SOCKET), exist_ok=True)

        os.makedirs(os.path.dirname(OUTPUT_SOCKET), exist_ok=True)

        self._tasks()
        self._timeTasks()

        self._errorWait = ErrorWait()

        self._resetThread = self._errorWait.makeThread(
            target=self._resetRoop, daemon=True
        )
        self._resetThread.start()

        r, w = os.pipe()

        self._proc = subprocess.Popen(
            ["/docker-entrypoint.sh", "nginx", "-g", "daemon off;"],
            stdout=sys.stdout,
            stderr=w,
        )

        self._watchThread = self._errorWait.makeThread(
            target=self._watch, kwargs={"r": r}, daemon=True
        )
        self._watchThread.start()

        self._waitThread = self._errorWait.makeThread(target=self._wait, daemon=True)
        self._waitThread.start()

        self._errorWait.wait()


class Task(ABC):
    """開始時に実行するタスク"""

    @abstractmethod
    def setupTask(self) -> None:
        """開始時に実行するタスク"""


class TimeTask(Task, ABC):
    """一定時間毎に実行するタスク"""

    @abstractmethod
    def timeTask(self) -> None:
        """一定時間毎に実行するタスク"""

    def setupTask(self) -> None:
        """開始時に実行するタスク"""


class CheckTask(TimeTask, ABC):
    """Nginxの出力を検証するタスク"""

    MAX_TIME: ClassVar[int] = 100

    file: str
    lock: threading.RLock
    count: int

    def __init__(self) -> None:
        os.makedirs(BASE_PASS, exist_ok=True)
        self.file = os.path.join(BASE_PASS, f"{self.__class__.__name__}.txt")
        self.lock = threading.RLock()
        self._setCount()

    @abstractmethod
    def check(self, text: str) -> bool:
        """Nginxの出力を検証するルール

        Args:
            text: 検証するテキスト

        Returns:
            検証結果
        """

    def doCheck(self, text: str) -> CheckResult:
        """Nginxの出力検証を実行する。

        Args:
            text: 検証するテキスト

        Returns:
            検証結果
        """

        if self.check(text):
            with self.lock:
                self._setCount()
                self.count += 1
                self._saveCount()

                if self.__class__.MAX_TIME <= self.count:
                    return CheckResult.EXIT

                return CheckResult.ERROR
        return CheckResult.NORMAL

    def _setCount(self) -> None:
        """ファイルから``count``をセットする。"""

        with self.lock:
            if not hasattr(self, "count"):
                self.count = 0
            try:
                with open(self.file, "r") as f:
                    self.count = max(self.count, int(f.read())) + 1
            except FileNotFoundError:
                pass

    def _saveCount(self) -> None:
        """ファイルに``count``を保存する。"""

        with self.lock:
            with open(self.file, "w") as f:
                f.write(str(self.count))

    def timeTask(self) -> None:
        """一定時間毎に``count``をリセットする。"""

        with self.lock:
            self._setCount()
            if self.__class__.MAX_TIME <= self.count:
                while True:
                    time.sleep(2**31 - 1)
            else:
                self.count = 0
                self._saveCount()
