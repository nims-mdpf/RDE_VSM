from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from modules_vsm.interfaces import IStructuredDataProcesser


class StructuredDataProcesser(IStructuredDataProcesser):
    """Template class for parsing structured data.

    This class serves as a template for the development team to read and parse structured data.
    It implements the IStructuredDataProcesser interface. Developers can use this template class
    as a foundation for adding specific file reading and parsing logic based on the project's
    requirements.

    Example:
        csv_handler = StructuredDataProcesser()
        df = pd.DataFrame([[1,2,3],[4,5,6]])
        loaded_data = csv_handler.to_csv(df, 'file2.txt')

    """

    def hampel(self, x: np.ndarray, k: int, thr: float = 3) -> tuple[np.ndarray, np.ndarray]:
        """Apply Hampel filter to detect and replace outliers in a 1D numpy array.

        Args:
            x (np.ndarray): Input array.
            k (int): Window size on each side of the element.
            thr (float, optional): Threshold for outlier detection. Defaults to 3.

        Returns:
            tuple[np.ndarray, np.ndarray]:
                - Filtered array with outliers replaced by local median.
                - Binary array where 1 indicates an outlier.

        """
        array_size = len(x)
        idx = np.arange(array_size)
        output_x = x.copy()
        output_idx = np.zeros_like(x)

        for i in range(array_size):
            mask = (idx >= (idx[i] - k)) & (idx <= (idx[i] + k))
            kernel = x[mask]
            median = np.median(kernel)
            std = 1.4826 * np.median(np.abs(kernel - median))

            if np.abs(x[i] - median) > thr * std:
                output_idx[i] = 1
                output_x[i] = median

        return output_x, output_idx

    def _calc_slope_intersept(self, _df: pd.DataFrame) -> tuple[float, float]:
        """Calculate the slope and intercept of a line using the first two points in the DataFrame.

        Args:
            _df (pd.DataFrame): A DataFrame with at least two rows and two columns,
                                representing x and y coordinates.

        Returns:
            Tuple[float, float]: A tuple containing (slope, intercept).

        """
        a = (_df.iat[0, 1] - _df.iat[1, 1]) / (_df.iat[0, 0] - _df.iat[1, 0])
        b = _df.iat[0, 1] - a * _df.iat[0, 0]
        return a, b

    def estimate_model_from_upper_limit(
        self, df_fit: pd.DataFrame, percent: float = 80.0,
    ) -> LinearRegression:
        """Return a regression model for the upper N% region of the high magnetic field range."""
        df_fit = df_fit.copy()
        df_fit["diff"] = df_fit["x"].diff()
        df_fit.fillna(-1, inplace=True)
        xmax = df_fit["x"].max()
        df_sub = df_fit[(df_fit["x"] > xmax * (percent / 100)) & (df_fit["diff"] < 0)]

        if len(df_sub) == 0:
            error_msg = "No sample points found for linear regression (df_sub)"
            raise ValueError(error_msg)

        model = LinearRegression()
        x_ = df_sub[["x"]]
        y_ = df_sub[["y"]]
        model.fit(x_, y_)
        return model

    def estimate_max_from_upper_limit(self, df_fit: pd.DataFrame) -> float:
        """Estimate the saturation magnetic flux density (Bs) using the upper 20% of the high magnetic field range."""
        # Make a copy of the input DataFrame to avoid modifying the original.
        df_fit = df_fit.copy()
        df_fit["diff"] = df_fit["x"].diff()
        df_fit.fillna(-1, inplace=True)

        # Get the subset of data from the upper 20% of the magnetic field range.
        xmax = df_fit["x"].max()
        df_fit_20 = df_fit[(df_fit["x"] > xmax * 0.8) & (df_fit["diff"] < 0)]

        if len(df_fit_20) == 0:
            error_msg = "No sample points found for linear regression (df_fit_20)."
            raise ValueError(error_msg)

        # Perform linear regression on the selected data.
        model_1 = LinearRegression()
        x_1 = df_fit_20[["x"]]
        y_1 = df_fit_20[["y"]]
        model_1.fit(x_1, y_1)

        # Return the intercept of the regression line as the estimated Bs.
        intercept_array = model_1.intercept_
        return float(intercept_array[0])

    def mean_abs_extremes(self, values: pd.Series) -> float:  # MS(飽和磁化)
        """Calculate the mean of the absolute maximum and minimum values from the series.

        Args:
            values (pd.Series): A pandas Series containing numeric values.

        Returns:
            float: The mean of the absolute values of the series' max and min.

        """
        return float((abs(values.max()) + abs(values.min())) / 2)

    def _preprocess_data(self, x: pd.DataFrame, y: pd.DataFrame, invoice_obj: dict) -> pd.DataFrame:
        df = pd.DataFrame({
            "x": x.squeeze(),
            "y": y.squeeze(),
        })
        if invoice_obj["custom"].get("spike_removal"):
            filtered_y, outliers = self.hampel(np.asarray(df["y"]), k=2, thr=3)
            df.loc[outliers == 1, "y"] = np.nan
            df.dropna(subset=["y"], inplace=True)
            df.reset_index(drop=True, inplace=True)
        return df

    def _extract_high_field_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["diff"] = df["x"].diff().fillna(-1)
        xmax = df["x"].max()
        df_20 = df[(df["x"] > xmax * 0.8) & (df["diff"] < 0)]
        if df_20.empty:
            err_msg = "No sample points found for linear regression (df_fit_20)."
            raise ValueError(err_msg)
        return cast(pd.DataFrame, df_20)

    def _fit_linear_regression(self, df: pd.DataFrame) -> LinearRegression:
        model = LinearRegression()
        model.fit(df[["x"]], df[["y"]])
        return model

    def _calculate_physical_properties(self, df: pd.DataFrame) -> tuple[float, float]:
        bs = self.estimate_max_from_upper_limit(df)
        ms = self.mean_abs_extremes(df["y"])
        return bs, ms

    def _background_correction(self, df: pd.DataFrame, slope: float, spike_removal: bool) -> pd.DataFrame:
        df["Background"] = df["x"] * slope
        df["RM"] = df["y"] - df["Background"] if spike_removal else df["y"]
        if spike_removal:
            df.dropna(subset=["RM"], inplace=True)
            df.reset_index(drop=True, inplace=True)
        df["x"] = df["x"] / 1e4  # convert unit
        return df

    def _calculate_intercepts(self, df: pd.DataFrame) -> tuple[float, float]:
        # Br計算
        sr_m_field = df["x"]
        pm = np.sign(sr_m_field.iat[0])
        idx = sr_m_field[np.sign(sr_m_field) != pm].index.min()
        if np.isnan(idx):
            idx = len(sr_m_field)
        d = df.loc[(idx - 1): idx, ["x", "RM"]]
        a, b = self._calc_slope_intersept(d)
        br = b

        # Hc計算
        sr_r_m = df["RM"]
        pm = np.sign(sr_r_m.iat[0])
        idx = sr_r_m[np.sign(sr_r_m) != pm].index.min()
        if np.isnan(idx):
            idx = len(sr_r_m)
        d = df.loc[(idx - 1): idx, ["x", "RM"]]
        a, b = self._calc_slope_intersept(d)
        hc = -b / a
        return hc, br

    def _generic_plot(
        self,
        x: pd.DataFrame,
        y: pd.DataFrame,
        invoice_obj: dict,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Receive the data file and divide it into data parts.

        Obtain the slope of a regression line and each physical property from the data.
        Slope: non-magnetic component and slope of the magnetization curve near the coercive force point.
        (TODO: to be RdeToolKit?).

        Args:
            x (pd.DataFrame): x-axis data.
            y (pd.DataFrame): y-axis data.
            invoice_obj (dict): Invoice related information.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]:
                df_fit: Dataframe by fitting.
                characteristic_values: Hc (Coercive force), Br (Remanence), Bs (Residual magnetic flux density).

        """
        if x.empty or y.empty:
            error_msg = "no data lines"
            raise ValueError(error_msg)

        df = self._preprocess_data(x, y, invoice_obj)
        df_20 = self._extract_high_field_data(df)
        model = self._fit_linear_regression(df_20)
        slope = model.coef_[0]

        bs, ms = self._calculate_physical_properties(df)
        df = self._background_correction(df, slope, invoice_obj["custom"].get("spike_removal", False))

        hc, br = self._calculate_intercepts(df)

        return df, pd.DataFrame({
            'Hc': [hc],
            'Br': [br],
            'Bs': [bs if bs is not None else float("nan")],
            'Ms': [ms if ms is not None else float("nan")],
        })

    def parse_header(self, header: dict[str, Any]) -> dict[str, Any]:
        """Parse header dict, converting list values to comma-separated strings."""
        if header is None:
            return {}
        return {k: ",".join(v) if isinstance(v, list) else v for k, v in header.items()}

    def get_sample_size(self, header: dict[str, Any], invoice_obj: dict) -> list[float]:
        """Extract sample size dimensions from invoice or header data."""
        sample_size = []
        for key in ["sample_size_height", "sample_size_width", "sample_size_thickness"]:
            val = invoice_obj["custom"].get(key)
            if val is not None:
                sample_size.append(val)

        if len(sample_size) not in (2, 3):
            sample_size.clear()
            sample_size_str = header.get("SAMPLE_SIZE")
            if sample_size_str:
                sample_size = [float(i.strip()) for i in str(sample_size_str).split("*")]
        return sample_size

    def calculate_physical_properties(self, sample_size: list[float], characteristic_values: pd.DataFrame, invoice_obj: dict) -> dict[str, str]:
        """Calculate physical properties based on sample size and characteristic values."""
        results = {}
        correction_factor: float = invoice_obj["custom"].get("correction_factor") or 1
        sample_size_dim_2 = 2
        sample_size_dim_3 = 3
        if len(sample_size) == sample_size_dim_3:
            volume = sample_size[0] * sample_size[1] * sample_size[2]
            br_val = float(characteristic_values["Br"].iloc[-1])
            results["Br_per_volume"] = f"{(br_val / volume) * 1e9:.2e}"
            results["Br_per_volume_corrected"] = f"{(br_val / volume * correction_factor) * 1e9:.2e}"
            if "Ms" in characteristic_values.columns:
                ms_val = float(characteristic_values["Ms"].iloc[-1])
                results["Ms_per_volume"] = f"{(ms_val / volume) * 1e9:.2e}"
                results["Ms_per_volume_corrected"] = f"{(ms_val / volume * correction_factor) * 1e9:.2e}"
            if "Bs" in characteristic_values.columns:
                bs_val = float(characteristic_values["Bs"].iloc[-1])
                results["Bs_per_volume"] = f"{(bs_val / volume) * 1e9:.2e}"
        elif len(sample_size) == sample_size_dim_2:
            area = sample_size[0] * sample_size[1]
            br_val = float(characteristic_values["Br"].iloc[-1])
            results["Brt"] = f"{1000 * br_val / area:.2e}"
        return results

    def _prepare_characteristic_lists(
        self,
        characteristic_values: pd.DataFrame,
        physical_props: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        """Prepare CSV header keys and corresponding formatted values from characteristic values and physical properties.

        Args:
            characteristic_values (pd.DataFrame): DataFrame containing characteristic measurement values.
            physical_props (dict[str, str]): Calculated physical property strings.

        Returns:
            tuple[list[str], list[str]]: Tuple of two lists: header keys and their string values.

        """
        keys = ["Hc", "Br"]
        hc = abs(characteristic_values['Hc'].iloc[-1])
        br = characteristic_values['Br'].iloc[-1]
        values = [f"{hc:.2e}", f"{br:.2e}"]

        if "Ms" in characteristic_values.columns:
            ms = characteristic_values['Ms'].iloc[-1]
            keys.append("Ms")
            values.append(f"{ms:.2e}")
        if "Bs" in characteristic_values.columns:
            bs = characteristic_values['Bs'].iloc[-1]
            keys.append("Bs")
            values.append(f"{bs:.2e}")

        if physical_props.get("Brt") is not None:
            keys.append("Brt")
            values.append(physical_props["Brt"])
        if physical_props.get("Br_per_volume_corrected") is not None:
            keys.append("Br_per_volume_corrected")
            values.append(physical_props["Br_per_volume_corrected"])
        if physical_props.get("Bs_per_volume") is not None:
            keys.append("Bs_per_volume")
            values.append(physical_props["Bs_per_volume"])
        if physical_props.get("Ms_per_volume") is not None:
            keys.append("Ms_per_volume")
            values.append(physical_props["Ms_per_volume"])
        if physical_props.get("Ms_per_volume_corrected") is not None:
            keys.append("Ms_per_volume_corrected")
            values.append(physical_props["Ms_per_volume_corrected"])

        return keys, values

    def write_param_csv(
        self,
        csv_path_param: Path,
        characteristic_values: pd.DataFrame,
        invoice_obj: dict,
        physical_props: dict[str, str],
    ) -> None:
        """Write characteristic parameters and physical properties to a CSV file if feature acquisition is enabled.

        Args:
            csv_path_param (Path): Path to output CSV file.
            characteristic_values (pd.DataFrame): DataFrame containing characteristic measurement values.
            invoice_obj (dict): Dictionary containing invoice and custom parameters.
            physical_props (dict[str, str]): Calculated physical property strings.

        Returns:
            None

        """
        if not invoice_obj["custom"]["feature_acquisition"]:
            return

        keys, values = self._prepare_characteristic_lists(characteristic_values, physical_props)

        with open(csv_path_param, "w", newline="\n") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(keys)
            writer.writerow(values)

    def write_raw_csv(self, csv_path_raw: Path, df_data: pd.DataFrame, x_col: str | None, rm_col: str | None, dc_rm_col: str | None, moment_flag: bool) -> None:
        """Write physical property parameters to a CSV file."""
        df_out_raw = pd.DataFrame()
        df_out_raw[x_col] = df_data[x_col]
        if moment_flag:
            df_out_raw[rm_col] = df_data[rm_col]
        else:
            df_out_raw[dc_rm_col] = df_data[dc_rm_col]
        df_out_raw.to_csv(csv_path_raw, index=False)

    def write_graph_csv(self, csv_path_graph: Path, df_fit: pd.DataFrame) -> None:
        """Write raw measurement data to a CSV file."""
        df_out = pd.DataFrame()
        df_out["Magnetic Field (T)"] = df_fit["x"]
        df_out["Magnetization (emu)"] = df_fit["RM"]
        df_out.to_csv(csv_path_graph, index=False)

    def to_csv_3types(
            self,
            df_data: pd.DataFrame,
            csv_path_param: Path,
            csv_path_raw: Path,
            csv_path_graph: Path,
            *,
            x_col: str | None,
            rm_col: str | None,
            dc_rm_col: str | None,
            header: dict[str, Any],
            invoice_obj: dict,
    ) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
        """Measurement data (metadata) output to csv files.

        Args:
            df_data (pd.DataFrame): Measurement data.
            csv_path_param (Path): Path to param.csv file.
            csv_path_raw (Path): Path to raw.csv file.
            csv_path_graph (Path): Path to graph csv file.
            x_col (str | None): Name of the column to use as the x-axis.
            rm_col (str | None): Name of the column for moment (emu).
            dc_rm_col (str | None): Name of the column for DC Moment Fixed Ctr (emu).
            header (dict[str, Any]): Header information to include in the CSV files.
            invoice_obj (dict): Invoice data.

        Returns:
            df_fit (pd.DataFrame) : measurement data
            characteristic_values (pd.DataFrame) : Hc, Br, Bs, Brt
            moment_flag (bool) : False:DC Moment Fixed Ctr (emu), True: Moment (emu)

        """
        moment_flag = True
        if np.isnan(df_data[rm_col].iloc[-1]):
            df_data_y = df_data[[dc_rm_col]].copy()
            moment_flag = False
        else:
            df_data_y = df_data[[rm_col]].copy()

        df_data_x = df_data[[x_col]]

        df_fit, characteristic_values = self._generic_plot(df_data_x, df_data_y, invoice_obj)

        meta1 = self.parse_header(header)
        sample_size = self.get_sample_size(meta1, invoice_obj)
        physical_props = self.calculate_physical_properties(sample_size, characteristic_values, invoice_obj)

        physical_props_df = pd.DataFrame([physical_props])
        characteristic_values = pd.concat([characteristic_values.reset_index(drop=True), physical_props_df], axis=1)

        # CSV出力を分割した関数で呼ぶ
        self.write_param_csv(csv_path_param, characteristic_values, invoice_obj, physical_props)
        self.write_raw_csv(csv_path_raw, df_data, x_col, rm_col, dc_rm_col, moment_flag)
        self.write_graph_csv(csv_path_graph, df_fit)

        return df_fit, characteristic_values, moment_flag

    def to_csv(self, dataframe: pd.DataFrame, save_path: Path, *, header: list[str] | None = None) -> None:
        """Save the given DataFrame as a CSV file.

        Args:
            dataframe (pd.DataFrame): The DataFrame to be saved.
            save_path (Path): The path where the CSV file will be saved.
            header (list[str] | None, optional): A list of column headers to use.
                If None, the default headers from the DataFrame are used.

        """
        if header is not None:
            dataframe.to_csv(save_path, header=header, index=False)
        else:
            dataframe.to_csv(save_path, index=False)
