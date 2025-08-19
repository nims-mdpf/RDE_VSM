from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd
from rdetoolkit.models.rde2types import MetaType, RdeOutputResourcePath
from rdetoolkit.rde2util import CharDecEncoding

from modules_vsm.inputfile_handler import FileReader as datFileReader


class FileReader(datFileReader):
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

    def _parse_tokens(self, tokens: list[str], min_token_length: int) -> tuple[str, str | list[str] | None]:
        if not tokens:
            return "", None

        k = tokens[0].upper()
        if k == "INFO":
            kk = tokens[-1]
            vv: str | list[str] = ",".join(tokens[1:-1])
        elif k == "DATATYPE":
            kk = tokens[1]
            vv = tokens[2]
        elif k == "STARTUPAXIS":
            if len(tokens) < min_token_length:
                return "", None
            kk = "_".join(tokens[0:2])
            vv = "".join(tokens[2:])
        elif k == "FIELDGROUP":
            if len(tokens) < min_token_length:
                return "", None
            kk = "_".join(tokens[0:2])
            vv = tokens[2:]
        else:
            kk = k
            vv = tokens[1:]
        return kk, vv

    def _read_raw_data(
        self,
        raw_file_path: Path,
    ) -> tuple[MetaType, pd.DataFrame | None]:
        """Read raw file.

        Args:
            raw_file_path (Path): raw data file path

        Returns:
            dict[str, str | list[str]]: meta data
            pd.DataFrame | None: measurement data or None if not found

        """
        min_token_length = 3

        meta: MetaType = {}
        df_data: pd.DataFrame | None = None

        enc = CharDecEncoding.detect_text_file_encoding(raw_file_path)
        with open(raw_file_path, encoding=enc) as f:
            for line_tokens in csv.reader(f):
                tokens = [tok.strip() for tok in line_tokens]
                if not tokens or tokens[0].startswith(";"):
                    continue
                if tokens[0].startswith("["):
                    if tokens[0].lower() == "[data]":
                        df_data = pd.read_csv(f)
                        break
                    continue

                kk, vv = self._parse_tokens(tokens, min_token_length)
                if kk and vv is not None:
                    meta[kk] = vv

        return meta, df_data

    def read(
        self,
        resource_paths: RdeOutputResourcePath,
        is_filename_mapping_rule: bool = False,
    ) -> tuple[MetaType, pd.DataFrame, list[str]]:
        """Read dat file.

        Args:
            resource_paths (RdeOutputResourcePath): resource paths
            is_filename_mapping_rule (bool): filename mapping rule

        Returns:
            dict[str, str | list[str]]: meta data
            pd.DataFrame: measurement data
            list[str]: fname_token parsed from filename

        """
        token_length_expected = 4
        raw_file = resource_paths.rawfiles[0]

        if raw_file.suffix.lower() != ".dat":
            error_msg = "Invalid file extension. Only .dat files are allowed."
            raise ValueError(error_msg)

        src_base_name = raw_file.name
        fname_token = [tok.strip() for tok in src_base_name.split("_", 3)]
        if len(fname_token) != token_length_expected:
            error_msg = f'Unknown filename pattern("{src_base_name}")'
            raise ValueError(error_msg)

        preparation_date = re.search(r'(19|20)\d{6}', fname_token[1])
        if preparation_date is None:
            error_msg = f'Unknown filename pattern("{src_base_name}")'
            raise ValueError(error_msg)

        meta, df_data = self._read_raw_data(raw_file)
        if df_data is None:
            error_msg = f"Failed to read data from {raw_file}"
            raise ValueError(error_msg)

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
            "x": ["Magnetic Field (Oe)"],
            "RM": ["Moment (emu)"],
            "DC_RM": ["DC Moment Fixed Ctr (emu)"],
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
            invoice_obj (dict): Invoice data.
            meta (dict): Metadata.
            is_filename_mapping_rule (bool): Filename mapping rule flag.
            fname_token (list | None): List of tokens [instrumentName, sampleName, regDataType, dataName] or None.
            dst_invoice_json (Path): Path to the invoice.json file where the features will be written.

        """
        date_index = 1  # This assumes the second element is the date (e.g., "01/01/2020")
        min_fileopentime_length = 2  # Minimum length required for FILEOPENTIME

        invoice_obj["basic"]["dataName"] = "${filename}"
        if fname_token is not None:
            self._overwrite_specimen(invoice_obj, fname_token, dst_invoice_json)

        if (
            meta is not None
            and meta.get("FILEOPENTIME") is not None
            and len(meta["FILEOPENTIME"]) >= min_fileopentime_length
            and invoice_obj["custom"].get("measurement_measured_date") is None
        ):
            self._overwrite_measured_date(
                invoice_obj,
                meta,
                dst_invoice_json,
                date_key="FILEOPENTIME",
                date_format="%m/%d/%Y",
                index=date_index,
            )
