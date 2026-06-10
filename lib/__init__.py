"""Shared utilities for Futbolstats.

`lib` is the only importable Python package in this project. Numbered folders
(`06_ingestion/`, etc.) hold scripts run as standalone files — their names
start with digits and cannot be imported as Python modules.
"""
from .io import read_parquet, write_parquet, read_entities, write_entities

__all__ = ["read_parquet", "write_parquet", "read_entities", "write_entities"]
