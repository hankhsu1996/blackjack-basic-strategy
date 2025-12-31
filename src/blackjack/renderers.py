"""Data structures for strategy tables."""

from dataclasses import dataclass, field


@dataclass
class TableData:
    """Data structure for a single strategy table."""

    title: str
    headers: list[str]
    rows: list[list[str]]


@dataclass
class StrategyData:
    """Complete strategy data."""

    config_description: str
    hard_table: TableData
    soft_table: TableData
    pair_table: TableData
    legend: str = field(
        default="S=Stand, H=Hit, Dh=Double/Hit, Ds=Double/Stand, P=Split"
    )
