# Python Verison: 3.11
# python 3.11-slim-bullseye for linux/amd64
FROM python@sha256:fc39d2e68b554c3f0a5cb8a776280c0b3d73b4c04b83dbade835e2a171ca27ef


# appディレクトリを作成
WORKDIR /app

# 必要なPythonライブラリのインストール
COPY requirements.txt /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# プログラムや設定ファイルなどをコピーする
COPY main.py /app
COPY modules/ /app/modules/
COPY modules_vsm/ /app/modules_vsm/
