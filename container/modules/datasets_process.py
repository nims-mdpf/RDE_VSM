from __future__ import annotations

from rdetoolkit.errors import catch_exception_with_message
from rdetoolkit.models.rde2types import RdeInputDirPaths, RdeOutputResourcePath
from rdetoolkit.rde2util import Meta

from modules_vsm.factory import VsmFactory


@catch_exception_with_message()
def dataset(
    srcpaths: RdeInputDirPaths,
    resource_paths: RdeOutputResourcePath,
) -> None:
    """Execute structured processing in VSM.

    Execute structured text processing, metadata extraction, and visualization.
    It handles structured text processing, metadata extraction, and graphing.
    Other processing required for structuring may be implemented as needed.

    Args:
        srcpaths: Paths to input resources for processing.
        resource_paths: Paths to output resources for saving results.

    Returns:
        None

    Note:
        The actual function names and processing details may vary depending on the project.

    """
    # 設定とモジュール取得
    config = VsmFactory.get_config(resource_paths.rawfiles[0], srcpaths.tasksupport)
    module = VsmFactory.get_objects(resource_paths.rawfiles[0], srcpaths.tasksupport, config)

    # 拡張子・ファイル名ベース
    raw_file = resource_paths.rawfiles[0]
    raw_basename = raw_file.stem

    # 共通CSVパス
    csv_path_graph = resource_paths.struct.joinpath(f"{raw_basename}.csv")
    csv_path_param = resource_paths.struct.joinpath(f"{raw_basename}_param.csv")
    csv_path_raw = resource_paths.struct.joinpath(f"{raw_basename}_raw.csv")

    # 入力データ読み込み
    meta = df_data = fname_token = None
    is_filename_mapping_rule = False
    moment_flag = None

    if srcpaths.tasksupport.joinpath("filename_mapping_rule.txt").exists():
        is_filename_mapping_rule = True

    meta, df_data, fname_token = module.file_reader.read(resource_paths, is_filename_mapping_rule)
    x_col, rm_col, dc_rm_col = module.file_reader.identify_columns(df_data)
    invoice_obj = module.file_reader.read_invoice(resource_paths.invoice_org)

    # データ処理（CSV出力）
    fit_data, characteristic_values, moment_flag = module.structured_processer.to_csv_3types(
        df_data,
        csv_path_param,
        csv_path_raw,
        csv_path_graph,
        x_col=x_col,
        rm_col=rm_col,
        dc_rm_col=dc_rm_col,
        header=meta,
        invoice_obj=invoice_obj,
    )

    # メタデータ保存
    const_meta_info, repeated_meta_info = module.meta_parser.parse(meta, characteristic_values, invoice_obj)
    module.meta_parser.save_meta(
        resource_paths.meta.joinpath("metadata.json"),
        Meta(srcpaths.tasksupport.joinpath("metadata-def.json")),
        const_meta_info=const_meta_info,
        repeated_meta_info=repeated_meta_info,
    )

    # インボイス保存
    module.file_reader.overwrite_invoice(
        invoice_obj,
        meta,
        is_filename_mapping_rule,
        fname_token,
        resource_paths.invoice.joinpath("invoice.json"),
    )

    # グラフ描画
    module.graph_plotter.plot_corrected_original(
        df_data,
        fit_data,
        characteristic_values,
        raw_basename,
        invoice_obj,
        resource_paths.main_image,
        resource_paths.other_image,
        moment_flag,
        x_col=x_col,
        rm_col=rm_col,
        dc_rm_col=dc_rm_col,
    )
