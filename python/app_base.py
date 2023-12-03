"""Nginx Check コンテナのメインプログラム

検証機能を搭載していないため、オーバーライドしての使用を想定。
"""

import NginxCheck


def main() -> None:
    """メイン関数"""

    NginxCheck.NginxCheck().start()


if __name__ == "__main__":
    main()
