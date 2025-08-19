from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from rdetoolkit.exceptions import StructuredError

from modules_vsm.graph_handler import GraphPlotter
from modules_vsm.inputfile_handler import FileReader as VsmFileReader
from modules_vsm.LakeShore.txt.inputfile_handler import FileReader as txtFileReader
from modules_vsm.LakeShore.txt.meta_handler import MetaParser as txtMetaParser
from modules_vsm.meta_handler import MetaParser as VsmMetaParser
from modules_vsm.mpms.dat.inputfile_handler import FileReader as datFileReader
from modules_vsm.mpms.dat.meta_handler import MetaParser as datMetaParser
from modules_vsm.structured_handler import StructuredDataProcesser
from modules_vsm.TAMAKAWA.vsm.inputfile_handler import FileReader as vsmFileReader
from modules_vsm.TAMAKAWA.vsm.meta_handler import MetaParser as vsmMetaParser

MPMS_SUFFIX_CLASS_MAPPING = {
    "mpms": {
        ".dat": (datFileReader, datMetaParser),
    },
}

TAMAKAWA_SUFFIX_CLASS_MAPPING = {
    "TAMAKAWA": {
        ".vsm": (vsmFileReader, vsmMetaParser),
    },
}

LakeShore_SUFFIX_CLASS_MAPPING = {
    "LakeShore": {
        ".txt": (txtFileReader, txtMetaParser),
    },
}


class VsmFactory:
    """Obtain a variety of data for use in the VSM's Structured processing."""

    def __init__(
        self,
        file_reader: VsmFileReader,
        meta_parser: VsmMetaParser,
        graph_plotter: GraphPlotter,
        structured_processer: StructuredDataProcesser,
    ):
        self.file_reader = file_reader
        self.meta_parser = meta_parser
        self.graph_plotter = graph_plotter
        self.structured_processer = structured_processer

    @staticmethod
    def get_config(rawfile: Path, path_tasksupport: Path) -> Any:
        """Obtain a variety of data.

        Obtain configuration data.

        Args:
            rawfile (Path): measurement file.
            path_tasksupport (Path): tasksupport path.

        Returns:
            config (Any): config data.

        """
        rdeconfig_file = path_tasksupport.joinpath("rdeconfig.yaml")

        # Get the graph scale of the representative image from rdeconfig.yaml.
        # TODO: Processes that should be moved to rdetoolkit in the future.
        if not rdeconfig_file.exists():
            err_msg = f"File not found: {rdeconfig_file}"
            raise StructuredError(err_msg)
        try:
            with open(rdeconfig_file) as file:
                config = yaml.safe_load(file)
        except Exception:
            err_msg = f"Invalid configuration file: {rdeconfig_file}"
            raise StructuredError(err_msg) from None

        return config

    @staticmethod
    def get_objects(rawfile: Path, path_tasksupport: Path, config: dict) -> VsmFactory:
        """Obtain a variety of data.

        Retrieve the class to be executed.
        Obtain the metadata definition file to be used.

        Args:
            rawfile (Path): measurement file.
            path_tasksupport (Path): tasksupport path.
            config (dict): config data.

        Returns:
            metadata_def (Path): Metadata file path.
            module (Any): classes
                FilaReader (class): Reads and processes structured files into data and metadata blocks.
                MetaParser (class): Parses metadata and saves it to a specified path.
                GraphPlotter (class): Utility for plotting data using various types of plots.
                StructuredDataProcessor (class): Template class for parsing structured data.

        """
        suffix = rawfile.suffix.lower()

        # (Only on manufacturer: rigaku, bruker) Input file extension check
        valid_extensions = {
            "mpms": {".dat"},
            "TAMAKAWA": {".vsm"},
            "LakeShore": {".txt"},
        }
        manufacturer = config['vsm']['manufacturer']
        if suffix not in valid_extensions.get(manufacturer, set()):
            err_msg = f"Format Error: Input data extension is incorrect: {suffix}"
            raise StructuredError(err_msg)

        # Obtain classes according to manufacturer and file extension
        class_filereader, class_metaparser = get_classes(manufacturer, suffix)

        return VsmFactory(
            class_filereader(),
            class_metaparser(config=config),
            GraphPlotter(config=config),
            StructuredDataProcesser(),
        )


def get_classes(manufacturer: str, suffix: str) -> tuple[type[VsmFileReader], type[VsmMetaParser]]:
    """Get the appropriate FileReader, MetaParser classes based on the manufacturer and file suffix."""
    try:
        match manufacturer:
            case "mpms":
                return MPMS_SUFFIX_CLASS_MAPPING[manufacturer][suffix]
            case "TAMAKAWA":
                return TAMAKAWA_SUFFIX_CLASS_MAPPING[manufacturer][suffix]
            case "LakeShore":
                return LakeShore_SUFFIX_CLASS_MAPPING[manufacturer][suffix]
            case _:
                raise KeyError
    except KeyError:
        err_msg = f"Unsupported combination of manufacturer '{manufacturer}' and file extension '{suffix}'"
        raise StructuredError(err_msg) from None
