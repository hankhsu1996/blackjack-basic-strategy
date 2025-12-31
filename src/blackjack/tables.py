"""Strategy table generation and formatting."""

from .config import GameConfig
from .renderers import StrategyData, TableData, TextRenderer
from .strategy import BasicStrategy


class StrategyTables:
    """Generate strategy table data."""

    DEALER_HEADERS = ["", "2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    def __init__(self, config: GameConfig | None = None):
        self.config = config or GameConfig.default()
        self.strategy = BasicStrategy(self.config)

    def generate_all(self) -> tuple[dict, dict, dict]:
        """Generate all three strategy tables.

        Returns:
            Tuple of (hard_table, soft_table, pair_table)
        """
        return (
            self.strategy.get_hard_strategy(),
            self.strategy.get_soft_strategy(),
            self.strategy.get_pair_strategy(),
        )

    def get_strategy_data(self) -> StrategyData:
        """Get complete strategy data for rendering."""
        hard, soft, pair = self.generate_all()

        return StrategyData(
            config_description=str(self.config),
            hard_table=TableData(
                title="Hard Totals",
                headers=self.DEALER_HEADERS,
                rows=self._build_hard_rows(hard),
            ),
            soft_table=TableData(
                title="Soft Totals",
                headers=self.DEALER_HEADERS,
                rows=self._build_soft_rows(soft),
            ),
            pair_table=TableData(
                title="Pairs",
                headers=self.DEALER_HEADERS,
                rows=self._build_pair_rows(pair),
            ),
        )

    def _build_hard_rows(self, strategy: dict[tuple[int, int], str]) -> list[list[str]]:
        """Build rows for hard totals table."""
        rows = []
        for total in range(5, 20):
            row = [str(total)]
            for dealer in range(2, 12):
                row.append(strategy.get((total, dealer), "?"))
            rows.append(row)
        return rows

    def _build_soft_rows(self, strategy: dict[tuple[int, int], str]) -> list[list[str]]:
        """Build rows for soft totals table."""
        rows = []
        for other in range(2, 10):
            row = [f"A,{other}"]
            for dealer in range(2, 12):
                row.append(strategy.get((other, dealer), "?"))
            rows.append(row)
        return rows

    def _build_pair_rows(self, strategy: dict[tuple[int, int], str]) -> list[list[str]]:
        """Build rows for pairs table."""
        rows = []
        pair_labels = [
            "2,2",
            "3,3",
            "4,4",
            "5,5",
            "6,6",
            "7,7",
            "8,8",
            "9,9",
            "10,10",
            "A,A",
        ]
        pair_values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        for label, val in zip(pair_labels, pair_values, strict=True):
            row = [label]
            for dealer in range(2, 12):
                row.append(strategy.get((val, dealer), "?"))
            rows.append(row)
        return rows

    def print_all(self) -> None:
        """Print all strategy tables to stdout."""
        data = self.get_strategy_data()
        renderer = TextRenderer()
        print(renderer.render(data))
