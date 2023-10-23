# CANPracticeShell
車両系CTFの作問でCANの問題を作成する際、CANネットワーク(can,vcan)を用意するためにはOSレベルの操作(カーネルモジュールの使用)と複雑なネットワークの分離または多くのリソースが必要なことに気づきました。そのような環境で学習目的で模擬したCANネットワークを操作するためのシンプルなコマンドラインインターフェースを提供します。このシェルはPythonの`cmd.Cmd`クラスを拡張し、`pika`ライブラリを使用してRabbitMQを介して模擬cansend,cangen,candumpでCANメッセージを送受信します。TCP上のAMQPの上で動作することに注意してください。



## Dockerを使用したセットアップ

1. DockerとDocker Composeをインストールします:
   - [Docker](https://docs.docker.com/get-docker/)
   - [Docker Compose](https://docs.docker.com/compose/install/)


2. プロジェクトのルートディレクトリで以下のコマンドを実行して、Dockerコンテナをビルドし、起動します:

```
docker-compose up --build
```

## 使用方法

### 接続

1. 以下のコマンドを実行します:
    ```
    nc localhost 12345
    ```

2. 最初に、任意の文字列を入力して識別子として使用します。これにより、ユニークなexchange名が生成されます。
3. 次に、以下のコマンドを使用して仮想CANネットワークを操作します:


- `cansend`:
    ```plaintext
    cansend vcan0 CAN_ID#DATA
    ```
    例: `cansend vcan0 111#1122334455667788`

- `cangen`:
    ```plaintext
    cangen vcan0 [-I [i|r|CAN_ID]] [-D [i|r|DATA]] [-L [i|r|DATA_LENGTH]] [-g GAP]
    ```
    例: `cangen vcan0 -I i -D r -L 8 -g 1000`

- `candump`:
    ```plaintext
    candump vcan0 [-a] [-x]
    ```

## ECUクラス

`ECU`クラスは、仮想ECU (Electronic Control Unit)を模倣し、定期的またはイベントベースでCANメッセージを送信する機能を提供します。`CANShell`クラス内で`ECU`インスタンスを作成し、`exchange_name`を渡すことで、`ECU`が信号を送信できるようになります。スクリプト内で簡単にパラメータを追加できます。

## ライセンス

MIT