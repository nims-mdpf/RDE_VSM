from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter

from modules_vsm.interfaces import IGraphPlotter


class GraphPlotter(IGraphPlotter[pd.DataFrame]):
    """Template class for creating graphs and visualizations.

    This class serves as a template for the development team to create graphs and visualizations.
    It implements the IGraphPlotter interface. Developers can use this template class as a
    foundation for adding specific graphing logic and customizations based on the project's
    requirements.

    Args:
        df (pd.DataFrame): The DataFrame containing data to be plotted.
        save_path (Path): The path where the generated graph will be saved.

    Keyword Args:
        header (Optional[list[str]], optional): A list of column names to use as headers in the graph.
            Defaults to None.

    Example:
        graph_plotter = GraphPlotter()
        data = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
        graph_plotter.plot(data, 'graph.png', header=['X Axis', 'Y Axis'])

    """

    def __init__(self, config: dict[str, str | None]):
        self.config: dict = config

    def _init_figure(self) -> tuple[Figure, Axes]:
        fig, ax = plt.subplots(1, 1)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        ax.grid(ls=":")
        return fig, ax

    def _plot_original(self, bname: str, figfmt: str, outdir: str, df_raw: pd.DataFrame) -> None:
        """Plottting raw measurement data.

        Args:
            bname (str) : filename
            figfmt (str) : figure format (png)
            outdir (str) : output file path
            df_raw (pd.DataFrame) : dataframe

        """
        fig, ax = self._init_figure()
        ax.set_xlabel(df_raw.columns[0])
        ax.set_ylabel(df_raw.columns[1])
        ax.set_title(f"{bname}_raw")
        ax.plot(df_raw.iloc[:, 0], df_raw.iloc[:, 1], marker='o', markersize=2)
        fig.tight_layout()
        graph_raw = os.path.join(outdir, f"{bname}_raw.{figfmt}")
        fig.savefig(graph_raw)
        plt.close(fig)

    def _plot_corrected(
        self,
        bname: str,
        figfmt: str,
        outdir: str,
        df: pd.DataFrame,
        characteristic_values: pd.DataFrame,
        invoice_obj: dict,
        m_key: str,
    ) -> None:
        """Plot the magnetization curve (hysteresis curve) with physical characteristics.

        Args:
            bname (str): filename
            figfmt (str): figure format (e.g., png)
            outdir (str): output directory
            df (pd.DataFrame): data for plotting
            characteristic_values (pd.DataFrame): physical parameters
            invoice_obj (dict): metadata from invoice
            m_key (str): "Bs" or "Ms" to indicate which magnetization value to plot

        """
        hc = characteristic_values['Hc'].iloc[-1]
        br = characteristic_values['Br'].iloc[-1]
        m_val = characteristic_values[m_key].iloc[-1]
        m_label = m_key

        # NaN チェック：M_val が NaN の場合はプロットをスキップ
        # if pd.isna(M_val):
        #    print(f"[Warning] {m_key} is NaN — skipping plot for {bname}_{m_key.lower()}")
        #    return

        fig, ax = self._init_figure()
        ax.set_xlabel(df.columns[0])
        ax.set_ylabel(df.columns[1])
        ax.set_title(f"{bname}_{m_key.lower()}")

        if invoice_obj["custom"]["background_removal"] and invoice_obj["custom"]["spike_removal"]:
            ax.set_ylim(-1.5 * abs(m_val), 1.5 * abs(m_val))

        ax.plot(df.iloc[:, 0], df.iloc[:, 1])

        if invoice_obj["custom"]["feature_acquisition"]:
            if hc != 0:
                ax.plot(hc, 0, marker="o", label=f"Hc : {abs(hc):.2e}[T]")
            if br != 0:
                ax.plot(0, br, marker="o", label=f"Br : {br:.2e}[emu]")
            if m_val != 0:
                ax.plot(0, m_val, marker="o", label=f"{m_label} : {m_val:.2e}[emu]")
            ax.legend()

        fig.tight_layout()
        graph_hyst = os.path.join(outdir, f"{bname}_{m_key.lower()}.{figfmt}")
        fig.savefig(graph_hyst)
        plt.close(fig)

    def plot_corrected_original(
        self,
        df_data: pd.DataFrame,
        fit_data: pd.DataFrame,
        characteristic_values: pd.DataFrame,
        raw_basename: str,
        invoice_obj: dict,
        out_dir_main_img: Path,
        out_dir_other_img: Path,
        moment_flag: bool,
        x_col: str | None,
        rm_col: str | None,
        dc_rm_col: str | None,
    ) -> None:
        """Draw graph.

        Args:
            df_data (pd.DataFrame): measurement data
            fit_data (pd.DataFrame): slope of a regression line
            characteristic_values (pd.DataFrame): each physical properties
            raw_basename (str): rawFilePath name
            invoice_obj (dict): invoice data
            out_dir_main_img (Path): output main image directory
            out_dir_other_img (Path): output other image directory
            moment_flag (bool): flag indicating whether moment data should be used
            x_col (str | None): column name for magnetic field data in df_data
            rm_col (str | None): column name for moment (emu) data in df_data
            dc_rm_col (str | None): column name for demagnetization-corrected moment data in df_data

        """
        df_original = pd.DataFrame()
        df_original["Magnetic Field (Oe)"] = df_data[x_col]
        if moment_flag:
            df_original["Moment (emu)"] = df_data[rm_col]
        else:
            df_original[dc_rm_col] = df_data[dc_rm_col]
        self._plot_original(raw_basename, "png", str(out_dir_other_img), df_original)

        # corrected データ生成
        df_corrected = pd.DataFrame()
        df_corrected["Magnetic Field (T)"] = fit_data["x"]
        df_corrected["Magnetization (emu)"] = fit_data["RM"]

        main_key = self.config['vsm'].get('main_image_settings', '').strip().lower()
        plot_bs = self.config['vsm'].get('plot_bs_curve', True)
        plot_ms = self.config['vsm'].get('plot_ms_curve', True)

        if "Ms" in characteristic_values.columns and plot_ms:
            out_dir = out_dir_main_img if main_key == "ms" else out_dir_other_img
            self._plot_corrected(raw_basename, "png", str(out_dir), df_corrected, characteristic_values, invoice_obj, m_key="Ms")

        if "Bs" in characteristic_values.columns and plot_bs:
            out_dir = out_dir_main_img if main_key == "bs" else out_dir_other_img
            self._plot_corrected(raw_basename, "png", str(out_dir), df_corrected, characteristic_values, invoice_obj, m_key="Bs")
