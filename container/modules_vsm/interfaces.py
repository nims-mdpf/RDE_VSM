from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

import pandas as pd
from rdetoolkit import rde2util
from rdetoolkit.models.rde2types import MetaType, RdeOutputResourcePath, RepeatedMetaType

T = TypeVar("T")


class IInputFileParser(ABC):
    """Interface for input file parsers.

    Parsers read and parse files from given resource paths, and provide
    methods for column identification and invoice overwriting.

    Methods:
        read: Parse the input files.
        identify_columns: Identify relevant columns in data.
        overwrite_invoice: Overwrite invoice information.

    """

    @abstractmethod
    def read(
        self,
        resource_paths: RdeOutputResourcePath,
        is_filename_mapping_rule: bool,
    ) -> tuple[MetaType, pd.DataFrame, list[str] | None]:
        """Read and parse input files from given resource paths.

        Args:
            resource_paths: Paths to input resources.
            is_filename_mapping_rule: Whether filename mapping rule is applied.

        Returns:
            meta: Metadata information.
            df: Parsed data as DataFrame.
            optional_columns: Optional list of string columns.

        """
        raise NotImplementedError

    @abstractmethod
    def identify_columns(
        self,
        df_data: pd.DataFrame,
    ) -> tuple[str | None, str | None, str | None]:
        """Identify relevant columns in the DataFrame.

        Args:
            df_data: Input DataFrame.

        Returns:
            A tuple of optional strings representing column names.

        """
        raise NotImplementedError

    @abstractmethod
    def overwrite_invoice(
        self,
        invoice_obj: dict,
        meta: dict,
        is_filename_mapping_rule: bool,
        fname_token: list[str] | None,
        dst_invoice_json: Path,
    ) -> None:
        """Overwrite invoice information and save to specified path.

        Args:
            invoice_obj: Invoice data dictionary.
            meta: Metadata dictionary.
            is_filename_mapping_rule: Whether filename mapping rule applies.
            fname_token: Filename tokens list or None.
            dst_invoice_json: Destination path to save invoice JSON.

        """
        raise NotImplementedError


class IStructuredDataProcesser(ABC):
    """Abstract base class (interface) for structured data parsers.

    This interface defines the contract that structured data parser
    implementations must follow. The parsers are expected to transform
    structured data, such as DataFrame, into various desired output formats.

    Methods:
        to_csv: A method that saves the given data to a CSV file.

    Implementers of this interface could transform data into various
    formats like CSV, Excel, JSON, etc.

    """

    @abstractmethod
    def to_csv(self, dataframe: pd.DataFrame, save_path: Path, *, header: list[str] | None = None) -> None:
        """Save the given DataFrame as a CSV file."""
        raise NotImplementedError


class IMetaParser(Generic[T], ABC):
    """Abstract base class (interface) for meta information parsers.

    This interface defines the contract that meta information parser
    implementations must follow. The parsers are expected to save the
    constant and repeated meta information to a specified path.

    Methods:
        save_meta: Saves the constant and repeated meta information to a specified path.
        parse: This method returns two types of metadata: const_meta_info and repeated_meta_info.

    """

    @abstractmethod
    def parse(self, meta: MetaType, characteristic_values: pd.DataFrame, invoice_obj: dict) -> tuple[MetaType, RepeatedMetaType]:
        """Parse."""
        raise NotImplementedError

    @abstractmethod
    def save_meta(
        self,
        save_path: Path,
        meta_obj: rde2util.Meta,
        *,
        const_meta_info: MetaType | None = None,
        repeated_meta_info: RepeatedMetaType | None = None,
    ) -> None:
        """Save meta."""
        raise NotImplementedError


class IGraphPlotter(Generic[T], ABC):
    """Abstract base class (interface) for graph plotting implementations.

    This interface defines the contract that graph plotting
    implementations must follow. The implementations are expected
    to be capable of plotting a simple graph using a given pandas DataFrame.

    Methods:
        simple_plot: Plots a simple graph using the provided pandas DataFrame.

    """
