from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from rdetoolkit.models.rde2types import MetaType, RdeOutputResourcePath
from rdetoolkit.rde2util import CharDecEncoding

from modules_vsm.inputfile_handler import FileReader as txtFileReader


class FileReader(txtFileReader):
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
        """Read raw file.

        Args:
            raw_file_path (Path): raw data file path

        Returns:
            tuple[MetaType, pd.DataFrame]: metadata and measurement data

        """
        meta: MetaType = {}
        df_data: pd.DataFrame = pd.DataFrame()

        enc = CharDecEncoding.detect_text_file_encoding(raw_file_path)
        with open(raw_file_path, encoding=enc) as f:
            skiprows: int = 0
            for lines in f.readlines():
                tokens = re.split(": {1,}| {2,}|\t", lines)
                tokens = [tok.strip() for tok in tokens]
                if len(tokens) == 0 or tokens[0].startswith(";"):
                    continue
                if tokens[0].startswith(("***", "H ")):
                    if tokens[0] == "***DATA***":
                        df_data = pd.read_csv(raw_file_path, skiprows=skiprows + 1, delim_whitespace=True)
                        break
                    continue
                meta_key: None | str = None
                for token in tokens:
                    if token and meta_key is None:
                        meta_key = token
                    elif meta_key is not None:
                        # 値をすべてstrとして扱うが必要ならここで変換を追加可能
                        meta[meta_key] = token
                        meta_key = None
                    elif token in ("***DATA***", "H [kOe]"):
                        break
                skiprows += 1

        return meta, df_data

    def read(
        self,
        resource_paths: RdeOutputResourcePath,
        is_filename_mapping_rule: bool = False,
    ) -> tuple[MetaType, pd.DataFrame, list[str] | None]:
        """Read txt file.

        Args:
            resource_paths (RdeOutputResourcePath): resource paths.
            is_filename_mapping_rule (bool): filename mapping rule.

        Returns:
            tuple[dict[str, str | int | float | list[object] | bool], pd.DataFrame, list[str] | None]:
                Metadata, measurement data, and optional fname_token .

        """
        raw_file = resource_paths.rawfiles[0]

        error_msg = "Invalid file extension. Only .txt files are allowed."
        if raw_file.suffix.lower() != ".txt":
            raise ValueError(error_msg)

        meta, df_data = self._read_raw_data(raw_file)
        fname_token: list[str] | None = None

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
        column_mapping: dict[str, list[str | None]] = {
            "x": ["Field(Oe)"],
            "RM": ["Moment(emu)"],
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
            meta (MetaType): metadata
            is_filename_mapping_rule (bool): filename mapping rule
            fname_token  (list): instrumentName, sampleName, regDataType, dataName
            dst_invoice_json (Path): Path to the invoice.json file where the features will be written.

        """
        invoice_obj["basic"]["dataName"] = "${filename}"

        if (
            meta is not None
            and meta.get("Start Time")
            and invoice_obj["custom"].get("measurement_measured_date") is None
        ):
            self._overwrite_measured_date(
                invoice_obj,
                meta,
                dst_invoice_json,
                date_key="Start Time",
                date_format="%m/%d/%Y %I:%M:%S %p",
            )
