from __future__ import annotations

import csv
import os
import re
from pathlib import Path

import chardet
import pandas as pd
from rdetoolkit.models.rde2types import MetaType, RdeOutputResourcePath

from modules_vsm.inputfile_handler import FileReader as vsmFileReader


class FileReader(vsmFileReader):
    """Template class for reading and parsing input data.

    This class serves as a template for the development team to read and parse input data.
    It implements the IInputFileParser interface. Developers can use this template class
    as a foundation for adding specific file reading and parsing logic based on the project's
    requirements.

    Args:
        raw_file_paths (tuple[Path, ...]): Paths to input source files.

    Returns:
        Any: The loaded data from the input file(s).

    Example:
        file_reader = FileReader()
        loaded_data = file_reader.read(('file1.txt', 'file2.txt'))
        file_reader.to_csv('output.csv')

    """

    def _read_raw_data(self, raw_file_path: Path) -> tuple[MetaType, pd.DataFrame]:
        """Read raw VSM data file and extract metadata and measurement DataFrame.

        Args:
            raw_file_path (Path): Path to the raw VSM data file.

        Returns:
            Tuple[MetaType, pd.DataFrame]: Parsed metadata and measurement data.

        """
        meta: MetaType = {}
        df_data: pd.DataFrame = pd.DataFrame()

        _header_with_date = ["DATE", "H(Oe)", "M(emu)", "Angle(degree)"]
        _header = ["H(Oe)", "M(emu)", "Angle(degree)"]

        # エンコーディングを検出
        with open(raw_file_path, "rb") as f:
            enc = chardet.detect(f.read())["encoding"]

        # ファイルを読み込み、解析
        with open(raw_file_path, encoding=enc) as f:
            for tokens in csv.reader(f):
                stripped_tokens = [tok.strip() for tok in tokens]
                if not stripped_tokens:
                    continue
                if stripped_tokens[0].startswith("DATE"):
                    df_data = pd.read_csv(f, header=None, names=_header_with_date)
                    break
                if stripped_tokens[0].startswith("H(Oe)"):
                    df_data = pd.read_csv(f, header=None, names=_header)
                    break
                meta[stripped_tokens[0].replace("=", "")] = stripped_tokens[1:]

        return meta, df_data

    def read(
        self,
        resource_paths: RdeOutputResourcePath,
        is_filename_mapping_rule: bool,
    ) -> tuple[MetaType, pd.DataFrame, list[str] | None]:
        """Read VSM file.

        Args:
            resource_paths (RdeOutputResourcePath): resource paths
            is_filename_mapping_rule (bool): filename mapping rule

        Returns:
            Tuple containing:
                - meta (MetaType): metadata dictionary
                - df_data (pd.DataFrame): measurement data
                - fname_token (list[str] | None): parsed filename tokens, if applicable

        """
        filename_token_min_length = 4
        fname_token: list[str] | None = None

        for candidate_rawfile in resource_paths.rawfiles:
            if is_filename_mapping_rule:
                if candidate_rawfile.suffix.lower() != ".vsm":
                    error_msg = "Invalid file extension. Only .vsm files are allowed."
                    raise ValueError(error_msg)

                src_base_name = os.path.basename(candidate_rawfile)
                fname_token = [tok.strip() for tok in src_base_name.split("_", filename_token_min_length)]
                if len(fname_token) < filename_token_min_length:
                    error_msg = f'Unknown filename pattern("{src_base_name}")'
                    raise ValueError(error_msg)

                preparation_date = re.search(r'(19|20)\d{6}', fname_token[1])
                if preparation_date is None:
                    error_msg = f'Unknown filename pattern("{src_base_name}")'
                    raise ValueError(error_msg)

            meta, df_data = self._read_raw_data(candidate_rawfile)
            break

        return meta, df_data, fname_token

    def identify_columns(self, df_data: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
        """Identify actual column names for x, RM, and DC_RM from the DataFrame.

        Args:
            df_data (pd.DataFrame): The input DataFrame from the raw file.

        Returns:
            tuple[str | None, str | None, str | None]:
                Matched column names for x, RM, and DC_RM respectively.

        Raises:
            ValueError: If required columns are not found in the DataFrame.

        """
        column_mapping = {
            "x": ["H(Oe)"],
            "RM": ["M(emu)"],
            "DC_RM": [],
        }

        x_col = next((col for col in column_mapping["x"] if col in df_data.columns), None)
        rm_col = next((col for col in column_mapping["RM"] if col in df_data.columns), None)
        dc_rm_col = next((col for col in column_mapping["DC_RM"] if col in df_data.columns), None)

        return x_col, rm_col, dc_rm_col

    def overwrite_invoice(
        self,
        invoice_obj: dict,
        meta: dict,
        is_filename_mapping_rule: bool,
        fname_token: list | None,
        dst_invoice_json: Path,
    ) -> None:
        """Overwrite the invoice data if necessary.

        Args:
            invoice_obj (dict): invoice data
            meta (dict): metadata
            is_filename_mapping_rule (bool): filename mapping rule
            fname_token (list | None): instrumentName, sampleName, regDataType, dataName
            dst_invoice_json (Path): Path to the invoice.json file where the features will be written.

        """
        if is_filename_mapping_rule and fname_token is not None:
            self._overwrite_specimen(invoice_obj, fname_token, dst_invoice_json)

        if (
            meta is not None
            and meta.get("date") is not None
            and invoice_obj["custom"]["measurement_measured_date"] is None
        ):
            self._overwrite_measured_date(
                invoice_obj,
                meta,
                dst_invoice_json,
                date_key="date",
                date_format="%Y/%m/%d",
            )
