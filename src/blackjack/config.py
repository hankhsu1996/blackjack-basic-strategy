"""Game rules configuration for blackjack."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig:
    """Configuration for blackjack game rules.

    Attributes:
        num_decks: Number of decks (0 for infinite deck approximation)
        dealer_hits_soft_17: True if dealer hits on soft 17 (H17), False for stand (S17)
        double_after_split: True if doubling is allowed after splitting
        resplit_aces: True if player can resplit aces (one card only after split)
        blackjack_pays: Payout ratio for blackjack (1.5 for 3:2, 1.2 for 6:5)
        dealer_peeks: True if dealer peeks for blackjack with 10/A showing

    Note:
        Resplitting is not modeled (assumes max 2 hands from split).
        Surrender is not modeled.
    """

    num_decks: int = 6
    dealer_hits_soft_17: bool = False  # S17 by default
    double_after_split: bool = True
    resplit_aces: bool = False
    blackjack_pays: float = 1.5  # 3:2
    dealer_peeks: bool = True

    @classmethod
    def default(cls) -> "GameConfig":
        """Return default configuration (6 deck, S17, DAS)."""
        return cls()

    @classmethod
    def six_deck_h17(cls) -> "GameConfig":
        """Return 6 deck H17 configuration."""
        return cls(dealer_hits_soft_17=True)

    def __str__(self) -> str:
        s17_h17 = "H17" if self.dealer_hits_soft_17 else "S17"
        das = "DAS" if self.double_after_split else "NDAS"
        rsa = "RSA" if self.resplit_aces else "NRSA"
        bj_pay = "3:2" if self.blackjack_pays == 1.5 else "6:5"
        decks = "Infinite" if self.num_decks == 0 else f"{self.num_decks}"
        return f"{decks} Deck, {s17_h17}, {das}, {rsa}, BJ {bj_pay}"
