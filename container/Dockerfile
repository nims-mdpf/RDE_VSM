## Python Version:3.12
FROM python:3.12-slim-trixie


# appディレクトリを作成
WORKDIR /app
COPY pip.conf /etc/pip.conf

# 必要なPythonライブラリのインストール
COPY requirements.txt /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# プログラムや設定ファイルなどをコピーする
COPY main.py /app
COPY modules/ /app/modules/
COPY modules_vsm/ /app/modules_vsm/
