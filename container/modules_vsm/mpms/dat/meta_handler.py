import pandas as pd
from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType

from modules_vsm.meta_handler import MetaParser as datMetaParser


class MetaParser(datMetaParser):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    """

    def parse(
        self,
        meta: MetaType,
        characteristic_values: pd.DataFrame,
        invoice_obj: dict,
    ) -> tuple[MetaType, RepeatedMetaType]:
        """Parse and extract constant and repeated metadata from the provided data."""
        meta1 = self._parse_const_meta(meta)
        sample_size = self._resolve_sample_size(invoice_obj, meta1)
        meta2 = self._parse_repeated_meta(characteristic_values, invoice_obj, sample_size)

        self.const_meta_info = meta1
        self.repeated_meta_info = meta2

        return meta1, meta2

    def _parse_const_meta(self, meta: MetaType) -> MetaType:
        if not meta:
            return {}
        result = {**meta}
        for k, v in meta.items():
            if isinstance(v, list):
                result[k] = ",".join(v)
        return result

    def _resolve_sample_size(self, invoice_obj: dict, meta1: MetaType) -> list[float]:
        keys = ['sample_size_height', 'sample_size_width', 'sample_size_thickness']
        sample_size = [
            invoice_obj["custom"].get(k) for k in keys if invoice_obj["custom"].get(k) is not None
        ]
        if len(sample_size) not in (2, 3):
            sample_size.clear()
            if meta1.get("SAMPLE_SIZE"):
                try:
                    sample_size = [float(s.strip()) for s in str(meta1["SAMPLE_SIZE"]).split("*")]
                except ValueError:
                    sample_size = []
        return sample_size

    def _parse_repeated_meta(
        self,
        characteristic_values: pd.DataFrame,
        invoice_obj: dict,
        sample_size: list,
    ) -> RepeatedMetaType:
        meta2: dict = {}

        if not invoice_obj["custom"].get("feature_acquisition"):
            return meta2

        meta2["hc"] = f"{abs(characteristic_values['Hc'].iloc[-1]):.2e}"
        meta2["br"] = f"{characteristic_values['Br'].iloc[-1]:.2e}"
        meta2["bs"] = f"{characteristic_values['Bs'].iloc[-1]:.2e}"

        if "Bs_per_volume" in characteristic_values:
            meta2["bs_per_volume"] = str(characteristic_values["Bs_per_volume"].iloc[-1])
        if "Brt" in characteristic_values:
            meta2["brt"] = str(characteristic_values["Brt"].iloc[-1])

        keys = ['sample_size_height', 'sample_size_width', 'sample_size_thickness']
        for i, val in enumerate(sample_size):
            if i < len(keys):
                meta2[keys[i]] = val

        return meta2
