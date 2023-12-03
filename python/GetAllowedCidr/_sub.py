"""Get Allowed Cidrモジュール

アクセスを許可されている国のIPアドレスリストを作成する。
"""

import os

IPLIST_FILE_PATH: str = os.environ["IPLIST_FILE_PATH"]
"""iplistを保存するファイルのパス"""
ALLOWED_COUNTRIES: tuple[str, ...] = tuple(
    (x.strip() for x in os.environ["ALLOWED_COUNTRIES"].split(","))
)
"""接続を許可する国"""
