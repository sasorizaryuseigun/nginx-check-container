# Nginx Check コンテナ

Nginx の出力を Python を用いて検証し、不正なアクセスが一定回数を超えたらサーバーを停止する Docker コンテナ

## BASE イメージ

基本モジュールのみを搭載し、検証内容を指定していないコンテナ。オーバーライドしての使用を想定。

## ALL イメージ

BASIC 認証の失敗回数を検証する機能と、接続許可国の IP リストを自動更新する機能を搭載。

## 環境変数

| 環境変数 | 初期値 |  |
| ------------- | ------------- | ------------- |
| INPUT_SOCKET | /sockets/input/nginx.sock | コンテナに接続するUNIXドメインソケット |
| OUTPUT_SOCKET | /sockets/output/nginx.sock | コンテナが接続するUINXドメインソケット |
| BASE_PASS | /count | カウント結果を保存するフォルダのパス |
| IPLIST_FILE_PATH | /iplist/iplist | iplistを保存するファイルのパス |
| BASIC_NAME | Auth | BASIC認証の名前 |
| BASIC_CHECK | True | BASIC認証を行うか |
| IP_CHECK | True | IPによる制限を行うか |
| ALLOWED_COUNTRIES | JP | 許可する国(複数指定する場合はカンマで区切る) |
