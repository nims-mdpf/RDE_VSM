# VSM用テンプレート

## 概要
VSM(磁気特性)をご利用の方に適したテンプレートです。以下の装置メーカーに対応しています。
- DT0015
    - TAMAKAWA
- DT0016
    - LakeShore
- DT0017
    - MPMS

VSMの専門家によって監修されたメタ情報を上記ファイルから自動的にRDEが抽出します。
- MPMSの.datフォーマット、LakeShoreの.txtフォーマット、TAMAKAWAの.VSMフォーマットに対応したメタ情報の抽出、ヒステリシス曲線の出力を行う。
- MultiDataTile対応（１つの送り状で複数のデータ登録を行う）
- ファイル命名規則に従っている場合は所定のマッピングを行う
- 出力画像はB-H曲線、M-H曲線、生データプロット画像を作成する
- 代表画像はB-H曲線（初期設定によりM-H曲線に変更可能）

## メタ情報
- [メタ情報](docs/要件定義_VSM.xlsx)

## 基本情報

### データ登録方法
- 送り状画面をひらいて入力ファイルに関する情報を入力する
- 「登録ファイル」欄に登録したいファイルをドラッグアンドドロップする。
  - 登録したいファイルのフォーマットは、\*.dat(MPMS)、\*.txt(LakeShore)、\*.VSM(TAMAKAWA) のどれか一つとなります。
  - 複数のファイルを入力し一度に複数のデータを登録することが可能。
  - 複数のファイルを入力する場合は、「データ名」に「${filename}」と入力し「データ名」に入力ファイル名をマッピングさせることができる
- 「登録開始」ボタンを押して（確認画面経由で）登録を開始する

## 構成

### レポジトリ構成

```
vsm
├── container
│   ├── Dockerfile
│   ├── Dockerfile_nims (NIMSイントラ用)
│   ├── data (入出力(下記参照))
│   ├── main.py 
│   ├── modules (ソースコード)
│   │   ├── __init__.py
│   │   └── datasets_process.py
│   ├── modules_vsm
│   │   ├── LakeShore
│   │   │   └── txt
│   │   │       ├── __init__.py
│   │   │       ├── inputfile_handler.py
│   │   │       └── meta_handler.py
│   │   ├── TAMAKAWA
│   │   │   └── vsm
│   │   │       ├── __init__.py
│   │   │       ├── inputfile_handler.py
│   │   │       └── meta_handler.py
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── graph_handler.py
│   │   ├── inputfile_handler.py
│   │   ├── interfaces.py
│   │   ├── meta_handler.py
│   │   ├── mpms
│   │   │   └── dat
│   │   │       ├── __init__.py
│   │   │       ├── inputfile_handler.py
│   │   │       └── meta_handler.py
│   │   └── structured_handler.py
│   ├── pip.conf
│   ├── pyproject.toml
│   ├── requirements-test.txt
│   ├── requirements.txt
│   ├── tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_meta.py
│   │   └── test_output.py
│   └── tox.ini
├── docs (ドキュメント)
│   ├── manual (マニュアル)
│   └── 要件定義_VSM.xlsx (要件定義)
├── inputdata (サンプルデータ)
│   ├── mpms (MPMS向け)
│   │   ├── BGULVAC_T20221013-2_VSM_P20221016.dat
│   │   └── EIKO@643_O20230125-3_VSM_In20230126.dat
│   ├── LakeShore (LakeShore向け)
│   │   ├── BGULVAC_T20221013-2_VSM_P20221016.dat
│   │   └── EIKO@643_O20230125-3_VSM_In20230126.dat
│   └── TAMAKAWA (TAMAKAWA向け)
│       ├── BGULVAC_T20221013-2_VSM_P20221016.dat
│       └── EIKO@643_O20230125-3_VSM_In20230126.dat
└── template (テンプレート群)
     ├── mpms (MPMS向け)
     │   ├── batch.yaml
     │   ├── catalog.schema.json (カタログ項目定義)
     │   ├── invoice.schema.json (送り状項目定義)
     │   ├── jobs.template.yaml
     │   ├── metadata-def.json (メタデータ定義(RDE画面表示用))
     │   └── tasksupport
     │       ├── invoice.schema.json (送り状項目定義)
     │       ├── metadata-def.json (メタデータ定義(datフォーマット用))
     │       └── rdeconfig.yaml (設定ファイル)
     └── LakeShore (LakeShore向け)
     │   ├── batch.yaml
     │   ├── catalog.schema.json (カタログ項目定義)
     │   ├── invoice.schema.json (送り状項目定義)
     │   ├── jobs.template.yaml
     │   ├── metadata-def.json (メタデータ定義(RDE画面表示用))
     │   └── tasksupport
     │       ├── invoice.schema.json (送り状項目定義)
     │       ├── metadata-def.json (メタデータ定義(txtフォーマット用))
     │       └── rdeconfig.yaml (設定ファイル)
     └── TAMAKAWA (TAMAKAWA向け)
         ├── batch.yaml
         ├── catalog.schema.json (カタログ項目定義)
         ├── invoice.schema.json (送り状項目定義)
         ├── jobs.template.yaml
         ├── metadata-def.json (メタデータ定義(RDE画面表示用))
         └── tasksupport
             ├── invoice.schema.json (送り状項目定義)
             ├── metadata-def.json (メタデータ定義(txtフォーマット用))
             └── rdeconfig.yaml (設定ファイル)
```

### 動作環境ファイル入出力

```
│   ├── container/data
│   │   ├── attachment
│   │   ├── inputdata
│   │   │   └── 登録ファイル欄にドラッグアンドドロップした任意のファイル
│   │   ├── invoice
│   │   │   └── invoice.json (送り状ファイル)
│   │   ├── main_image
│   │   │   └── (メイン)プロット画像
│   │   ├── meta
│   │   │   └── metadata.json (主要パラメータメタ情報ファイル)
│   │   ├── nonshared_raw
│   │   │   └── inputdataからコピーした入力ファイル
│   │   ├── other_image
│   │   │   └── (メイン以外の)プロット画像
│   │   ├── structured
│   │   │   ├── *_raw.csv (プロット画像元データ)
│   │   │   ├── *_param.csv (プロット画像元データ)
│   │   │   └── *.csv (プロット画像元データ)
│   │   ├── tasksupport (テンプレート群)
│   │   │   ├── invoice.schema.json
│   │   │   ├── metadata-def.json
│   │   │   └── rdeconfig.yaml
│   │   └── thumbnail
│   │       └── (サムネイル用)プロット画像
```

## データ閲覧
- データ一覧画面を開く。
- ギャラリー表示タブでは１データがタイル状に並べられている。データ名をクリックして詳細を閲覧する。
- ツリー表示タブではタクソノミーにしたがってデータを階層表示する。データ名をクリックして詳細を閲覧する。

### 動作環境
- Python: 3.11
- RDEToolKit: 1.3.0
