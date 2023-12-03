"""NginxCheckモジュール

Nginxのログ出力をPythonで検証する。
Dockerコンテナでの使用を想定
"""

import enum
import os
import threading
import queue as queueModule
from typing import Any, ClassVar

INPUT_SOCKET: str = os.environ["INPUT_SOCKET"]
"""コンテナに接続するUNIXドメインソケット"""
OUTPUT_SOCKET: str = os.environ["OUTPUT_SOCKET"]
"""コンテナが接続するUNIXドメインソケット"""
BASE_PASS: str = os.environ["BASE_PASS"]
"""カウント結果を保存するフォルダのパス"""


class CheckResult(enum.Enum):
    """検証結果"""

    NORMAL: ClassVar[Any] = enum.auto()
    """検証が成功した場合"""
    ERROR: ClassVar[Any] = enum.auto()
    """検証が失敗した場合"""
    EXIT: ClassVar[Any] = enum.auto()
    """検証が失敗し、失敗回数が基準を超えた場合"""


class ErrorWait:
    """サブスレッドでのエラー発生を監視し、プログラムを終了させる。"""

    queue: queueModule.Queue[BaseException]
    """サブスレッドのエラーをメインスレッドに渡す。"""

    def __init__(self) -> None:
        self.queue = queueModule.Queue()

    def makeThread(self, *args: Any, **keywords: Any):
        """監視対象のサブスレッドを作る。"""
        return ErrorWaitThread(self.queue, *args, **keywords)

    def wait(self):
        """サブスレッドを監視する。"""
        e: BaseException = self.queue.get()
        raise e


class ErrorWaitThread(threading.Thread):  
    """``ErrorWait``の監視対象となるスレッド。"""

    queue: queueModule.Queue[BaseException]
    """サブスレッドのエラーをメインスレッドに渡す。"""

    def __init__(
        self, queue: queueModule.Queue[BaseException], *args: Any, **keywords: Any
    ) -> None:  
        self.queue = queue
        super().__init__(*args, **keywords)

    def run(self) -> Any:
        """スレッド上で実行するタスクのエラーをキャッチする。"""
        try:
            return super().run()
        except BaseException as e:
            self.queue.put(e)
            raise e
