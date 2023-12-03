"""Get Allowed Cidrモジュール

アクセスを許可されている国のIPアドレスリストを作成する。
"""

import http.client
import io
import ipaddress
import urllib.request
import os
from collections.abc import Iterator

from ._sub import *


def getCidr(
    apnic_list: list[str],
) -> Iterator[ipaddress.IPv4Network] | Iterator[ipaddress.IPv6Network]:
    """apnic形式をcidr形式に変換する。"""

    start = ipaddress.ip_address(apnic_list[3])
    end = start + int(apnic_list[4]) - 1
    return ipaddress.summarize_address_range(start, end)


def getAllowedCidr(
    apnic: str,
) -> Iterator[ipaddress.IPv4Network] | Iterator[ipaddress.IPv6Network] | None:
    """IPアドレスの国が許可されているものか判定する。"""

    apnic_list: list[str] = apnic.split("|")
    """apnic形式のIPアドレス
    """

    if (
        len(apnic_list) == 7
        and apnic_list[1] in ALLOWED_COUNTRIES
        and (apnic_list[2] == "ipv4" or apnic_list[2] == "ipv6")
    ):
        return getCidr(apnic_list)


def getAllowedCidrFile() -> None:
    """許可されたIPアドレスのリストファイルを作成する。"""

    u: http.client.HTTPResponse
    """HTTPレスポンス"""
    f: io.TextIOWrapper
    """テキストストリーム"""
    response: bytes
    """取得結果"""
    cidrs: Iterator[ipaddress.IPv4Network] | Iterator[ipaddress.IPv6Network] | None
    """取得したIPアドレス"""
    cidr: ipaddress.IPv4Network | ipaddress.IPv6Network
    """取得したIPアドレス"""

    with urllib.request.urlopen(
        "http://ftp.apnic.net/stats/apnic/delegated-apnic-latest"
    ) as u:
        os.makedirs(os.path.dirname(IPLIST_FILE_PATH), exist_ok=True)
        with open(IPLIST_FILE_PATH, "w") as f:
            for response in u:
                cidrs = getAllowedCidr(response.decode())

                if cidrs is not None:
                    for cidr in cidrs:
                        f.write(f"{cidr} 0;\n")
