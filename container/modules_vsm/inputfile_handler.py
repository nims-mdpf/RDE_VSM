import datetime
import json
import re
from pathlib import Path
from typing import Any

import chardet
from rdetoolkit.models.rde2types import MetaType
from rdetoolkit.rde2util import CharDecEncoding

from modules_vsm.interfaces import IInputFileParser


class FileReader(IInputFileParser):
    """Template class for reading and overwriting input data.

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

    def read_invoice(self, raw_file_path: Path) -> Any:
        """Read invoice file.

        Args:
            raw_file_path (Path): invoice file path

        Returns:
            Any : invoice data

        """
        enc = CharDecEncoding.detect_text_file_encoding(raw_file_path)
        with open(raw_file_path, encoding=enc) as f:
            return json.load(f)

    def _overwrite_specimen(self, invoice_obj: dict, fname_token: list, dst_invoice_json: Path) -> None:
        """Overwrite the dataname.

        Args:
            invoice_obj (dict): invoice data
            fname_token (list): instrument_name, sample_name, regDataType, dataName
            dst_invoice_json (Path): Path to the invoice.json file where the features will be written.

        """
        with open(dst_invoice_json, "rb") as f:
            enc = chardet.detect(f.read())["encoding"]
        instrument_name, sample_name, *_ = fname_token
        preparation_date = re.search(r'(19|20)\d{6}', sample_name)
        invoice_obj["custom"]["sputtering_apparatus"] = instrument_name
        invoice_obj["custom"]["specimen_label"] = sample_name
        if preparation_date:
            invoice_obj["custom"]["sample_year"] = preparation_date.group()[:4]
            invoice_obj["custom"]["sample_month"] = preparation_date.group()[4:6]
        with open(dst_invoice_json, "w", encoding=enc) as fout:
            json.dump(invoice_obj, fout, indent=4, ensure_ascii=False)

    def _overwrite_measured_date(
        self,
        invoice_obj: dict,
        meta: MetaType,
        dst_invoice_json: Path,
        date_key: str,
        date_format: str,
        index: int = 0,
    ) -> None:
        """Overwrite the measured date.

        Args:
            invoice_obj (dict): Invoice data.
            meta (MetaType): Metadata.
            dst_invoice_json (Path): Path to the metadata JSON file to overwrite.
            date_key (str): Key in metadata containing the date string or list of date strings.
            date_format (str): Format string to parse the date.
            index (int, optional): Index to use if the date value is a list. Defaults to 0.

        """
        with open(dst_invoice_json, "rb") as f:
            enc = chardet.detect(f.read())["encoding"]
        value = meta[date_key]
        date_str = value[index] if isinstance(value, list) else value
        if not isinstance(date_str, str):
            date_str = str(date_str)
        tdate = datetime.datetime.strptime(date_str, date_format)
        invoice_obj["custom"]["measurement_measured_date"] = tdate.strftime("%Y-%m-%d")
        with open(dst_invoice_json, "w", encoding=enc) as fout:
            json.dump(invoice_obj, fout, indent=4, ensure_ascii=False)
