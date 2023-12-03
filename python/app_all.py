"""Nginx Check コンテナのメインプログラム

BASIC認証の失敗回数を検証し、接続許可国のIPリストを自動更新する。
"""

import os
from typing import ClassVar

import NginxCheck
import GetAllowedCidr


class BasicCheck(NginxCheck.CheckTask):
    """BASIC認証の失敗回数を検証する。"""

    def check(self, text: str) -> bool:
        """BASIC認証の失敗回数を検証する。"""
        return ": password mismatch," in text or (
            'user "' in text and '" was not found in "' in text
        )


class AllowedIpList(NginxCheck.TimeTask):
    """接続許可国のIPリストを更新する。"""

    def timeTask(self) -> None:
        """接続許可国のIPリストを更新する。"""
        GetAllowedCidr.getAllowedCidrFile()


class Check(NginxCheck.NginxCheck):
    if os.environ["BASIC_CHECK"] != "False" and os.environ["BASIC_CHECK"] != "false":
        BasicCheck: ClassVar[type] = BasicCheck
        """BASIC認証の失敗回数を検証する。"""

    if os.environ["IP_CHECK"] != "False" and os.environ["IP_CHECK"] != "frue":
        AllowedIpList: ClassVar[type] = AllowedIpList
        """接続許可国のIPリストを更新する。"""


def main() -> None:
    """メイン関数"""

    Check().start()


if __name__ == "__main__":
    main()
