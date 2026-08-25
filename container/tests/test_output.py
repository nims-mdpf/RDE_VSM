import os
import shutil
from typing import Union, List


def setup_inputdata_folder(inputdata_name: Union[str, List[str]], format_name: str = "mpms"):
    """テスト用でdataフォルダ群の作成とrawファイルの準備

    Args:
        inputdata_name (Union[str, List[str]]): rawファイル名
        format_name (str): 使用するフォーマット名（mpms, LakeShoreなど）
    """

    destination_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)

    destination_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(destination_path, exist_ok=True)
    os.makedirs(os.path.join(destination_path, "inputdata"), exist_ok=True)
    os.makedirs(os.path.join(destination_path, "invoice"), exist_ok=True)

    inputdata_original_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "inputdata", format_name
    )

    if isinstance(inputdata_name, list):
        for item in inputdata_name:
            shutil.copy(
                os.path.join(inputdata_original_path, format_name, item),
                os.path.join(destination_path, "inputdata"),
            )
    else:
        shutil.copy(
            os.path.join(inputdata_original_path, format_name, inputdata_name),
            os.path.join(destination_path, "inputdata"),
        )

    shutil.copy(
        os.path.join(inputdata_original_path, "invoice.json"),
        os.path.join(destination_path, "invoice"),
    )

    # tasksupport
    tasksupport_original_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", format_name, "tasksupport"
    )
    tasksupport_dest_path = os.path.join(destination_path, "tasksupport")
    os.makedirs(tasksupport_dest_path, exist_ok=True)

    for fname in ["default_value.csv", "invoice.schema.json", "metadata-def.json", "rdeconfig.yaml"]:
        shutil.copy(
            os.path.join(tasksupport_original_path, fname),
            os.path.join(tasksupport_dest_path, fname),
        )


class TestOutputCase1:
    """LakeShore形式のマルチファイルテスト:
       - "E1021_out.txt"
       - "VSM.txt"
    """
    inputdata = ["E1021_out.txt", "VSM.txt"]

    def test_setup(self):
        setup_inputdata_folder(self.inputdata, format_name="LakeShore")

    def test_raw_data(self, setup_main, data_path):
        assert os.path.exists(os.path.join(data_path, "nonshared_raw", "E1021_out.txt"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "nonshared_raw", "VSM.txt"))

    def test_main_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "main_image", "E1021_out_bs.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "main_image", "VSM_bs.png"))

    def test_other_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "other_image", "E1021_out_raw.png"))
        assert os.path.exists(os.path.join(data_path, "other_image", "E1021_out_ms.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "VSM_raw.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "VSM_ms.png"))

    def test_structured(self, data_path):
        assert os.path.exists(os.path.join(data_path, "structured", "E1021_out_param.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "E1021_out_raw.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "E1021_out.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "VSM_param.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "VSM_raw.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "VSM.csv"))

    def test_thumbnail(self, data_path):
        assert os.path.exists(os.path.join(data_path, "thumbnail", "E1021_out_bs.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "thumbnail", "VSM_bs.png"))

    def test_meta(self, data_path):
        assert os.path.exists(os.path.join(data_path, "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "meta", "metadata.json"))


class TestOutputCase2:
    """case1
    マルチファイルのテスト:
        "EIKO@643_DO20230908-1-1_VSM_In20230911.VSM"
        "EIKO@643_DO20230908-1-1_VSM_P20230911.VSM"

    """

    inputdata: Union[str, List[str]] = [
        "EIKO@643_DO20230908-1-1_VSM_In20230911.VSM",
        "EIKO@643_DO20230908-1-1_VSM_P20230911.VSM"
    ]

    def test_setup(self):
        setup_inputdata_folder(self.inputdata, format_name="TAMAKAWA")

    def test_raw_data(self, setup_main, data_path):
        assert os.path.exists(os.path.join(data_path, "nonshared_raw", "EIKO@643_DO20230908-1-1_VSM_In20230911.VSM"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "nonshared_raw", "EIKO@643_DO20230908-1-1_VSM_P20230911.VSM"))

    def test_main_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "main_image", "EIKO@643_DO20230908-1-1_VSM_In20230911_bs.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "main_image", "EIKO@643_DO20230908-1-1_VSM_P20230911_bs.png"))

    def test_other_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "other_image", "EIKO@643_DO20230908-1-1_VSM_In20230911_raw.png"))
        assert os.path.exists(os.path.join(data_path, "other_image", "EIKO@643_DO20230908-1-1_VSM_In20230911_ms.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "EIKO@643_DO20230908-1-1_VSM_P20230911_raw.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "EIKO@643_DO20230908-1-1_VSM_P20230911_ms.png"))

    def test_structured(self, data_path):
        assert os.path.exists(os.path.join(data_path, "structured", "EIKO@643_DO20230908-1-1_VSM_In20230911_param.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "EIKO@643_DO20230908-1-1_VSM_In20230911_raw.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "EIKO@643_DO20230908-1-1_VSM_In20230911.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "EIKO@643_DO20230908-1-1_VSM_P20230911_param.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "EIKO@643_DO20230908-1-1_VSM_P20230911_raw.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "EIKO@643_DO20230908-1-1_VSM_P20230911.csv"))

    def test_thumbnail(self, data_path):
        assert os.path.exists(os.path.join(data_path, "thumbnail", "EIKO@643_DO20230908-1-1_VSM_In20230911_bs.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "thumbnail", "EIKO@643_DO20230908-1-1_VSM_P20230911_bs.png"))

    def test_meta(self, data_path):
        assert os.path.exists(os.path.join(data_path, "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "meta", "metadata.json"))


class TestOutputCase3:
    """case3
    マルチファイルのテスト:
        "BGULVAC_T20221013-2_VSM_P20221016.dat"
        "EIKO@643_O20230125-3_VSM_In20230126.dat"

    """

    inputdata: Union[str, List[str]] = [
        "BGULVAC_T20221013-2_VSM_P20221016.dat",
        "EIKO@643_O20230125-3_VSM_In20230126.dat"
    ]

    def test_setup(self):
        setup_inputdata_folder(self.inputdata)

    def test_raw_data(self, setup_main, data_path):
        assert os.path.exists(os.path.join(data_path, "nonshared_raw", "BGULVAC_T20221013-2_VSM_P20221016.dat"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "nonshared_raw", "EIKO@643_O20230125-3_VSM_In20230126.dat"))

    def test_main_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "main_image", "BGULVAC_T20221013-2_VSM_P20221016_bs.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "main_image", "EIKO@643_O20230125-3_VSM_In20230126_bs.png"))

    def test_other_image(self, data_path):
        assert os.path.exists(os.path.join(data_path, "other_image", "BGULVAC_T20221013-2_VSM_P20221016_raw.png"))
        assert os.path.exists(os.path.join(data_path, "other_image", "BGULVAC_T20221013-2_VSM_P20221016_ms.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "EIKO@643_O20230125-3_VSM_In20230126_raw.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "other_image", "EIKO@643_O20230125-3_VSM_In20230126_ms.png"))

    def test_structured(self, data_path):
        assert os.path.exists(os.path.join(data_path, "structured", "BGULVAC_T20221013-2_VSM_P20221016_param.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "BGULVAC_T20221013-2_VSM_P20221016_raw.csv"))
        assert os.path.exists(os.path.join(data_path, "structured", "BGULVAC_T20221013-2_VSM_P20221016.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "EIKO@643_O20230125-3_VSM_In20230126_param.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "EIKO@643_O20230125-3_VSM_In20230126_raw.csv"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "structured", "EIKO@643_O20230125-3_VSM_In20230126.csv"))

    def test_thumbnail(self, data_path):
        assert os.path.exists(os.path.join(data_path, "thumbnail", "BGULVAC_T20221013-2_VSM_P20221016_bs.png"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "thumbnail", "EIKO@643_O20230125-3_VSM_In20230126_bs.png"))

    def test_meta(self, data_path):
        assert os.path.exists(os.path.join(data_path, "meta", "metadata.json"))
        assert os.path.exists(os.path.join(data_path, "divided", "0001", "meta", "metadata.json"))
