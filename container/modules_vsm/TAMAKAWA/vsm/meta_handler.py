import pandas as pd
from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType

from modules_vsm.meta_handler import MetaParser as vsmMetaParser


class MetaParser(vsmMetaParser):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    """

    def parse(self, meta: MetaType, characteristic_values: pd.DataFrame, invoice_obj: dict) -> tuple[MetaType, RepeatedMetaType]:
        """Parse and extract constant and repeated metadata from the provided data."""
        self.const_meta_info = self._parse_const_meta(meta)
        self.repeated_meta_info = self._parse_repeated_meta(characteristic_values, invoice_obj)

        return self.const_meta_info, self.repeated_meta_info

    def _parse_const_meta(self, meta: MetaType) -> MetaType:
        meta1 = {}
        meta_key_values = {
            "sample name": "sample_name",
            "meas. seq. filename": "applied_magnetic_field",
            "temperature(max)": "temperature",
            "max magnetic field": "max_magnetic_field",
            "calibration value": "calibration_value",
            "sample thickness": "sample_thickness",
            "Sample Area": "sample_cross_section",
            "correction(demagnetization field)": "correction_of_demagnetization_field",
            "correction(diamagnetism)": "correction_of_diamagnetism",
            "correction(subtraction)": "add-subtract_process",
            "correction(addition)": "segment_processing",
            "correction(spline)": "spline_interpolation",
            "correction(smoothing)": "smoothing_process",
            "correction(image effect)": "correction_of_image_effect",
        }

        for k, v in meta.items():
            if isinstance(v, list):
                key = meta_key_values.get(k, k)
                meta1[key] = v[0]
        return meta1

    def _parse_repeated_meta(
        self,
        characteristic_values: pd.DataFrame,
        invoice_obj: dict,
    ) -> RepeatedMetaType:
        meta2: dict = {}

        if not invoice_obj["custom"].get("feature_acquisition"):
            return meta2

        hc = characteristic_values['Hc'].iloc[-1]
        br = characteristic_values['Br'].iloc[-1]
        ms = characteristic_values['Ms'].iloc[-1]

        if hc != 0:
            meta2["hc"] = f"{abs(hc):.2e}"
        if br != 0:
            meta2["br"] = f"{br:.2e}"
        if ms != 0:
            meta2["bs"] = f"{ms:.2e}"

        optional_keys = [
            ("Br_per_volume", "br_per_volume"),
            ("Br_per_volume_corrected", "br_per_volume_corrected"),
            ("Ms_per_volume", "bs_per_volume"),
            ("Ms_per_volume_corrected", "bs_per_volume_corrected"),
        ]

        for df_key, meta_key in optional_keys:
            if df_key in characteristic_values:
                meta2[meta_key] = str(characteristic_values[df_key].iloc[-1])

        return meta2
