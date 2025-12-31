"""Dealer outcome probability calculations."""

from functools import lru_cache

from .cards import DISTINCT_CARDS, get_card_probabilities, hand_value
from .config import GameConfig


class DealerProbabilities:
    """Calculate dealer final outcome probabilities."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.card_probs = get_card_probabilities(config.num_decks)

    @lru_cache(maxsize=1024)
    def get_outcome_probs(self, upcard: int) -> dict[int, float]:
        """Get probability distribution of dealer final totals.

        Args:
            upcard: Dealer's upcard value (2-11, where 11 is Ace)

        Returns:
            Dictionary with keys 17, 18, 19, 20, 21, 'bust'
            mapping to probabilities.
        """
        # Start with dealer's upcard
        initial_hand = (upcard,)
        return self._calculate_outcomes(initial_hand)

    def _calculate_outcomes(self, hand: tuple[int, ...]) -> dict[int, float]:
        """Recursively calculate outcome probabilities for a dealer hand."""
        total, is_soft = hand_value(hand)

        # Check if dealer must stand
        if total > 21:
            return {"bust": 1.0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}

        if total >= 17:
            # Stand on hard 17+
            if not is_soft:
                return self._outcome_dict(total)
            # Soft 17: depends on H17/S17 rule
            if total > 17 or not self.config.dealer_hits_soft_17:
                return self._outcome_dict(total)
            # H17: dealer hits on soft 17

        # Dealer must hit - calculate outcomes for each possible card
        outcomes: dict[int, float] = {"bust": 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}

        for card in DISTINCT_CARDS:
            prob = self.card_probs[card]
            new_hand = hand + (card,)
            card_outcomes = self._calculate_outcomes(new_hand)

            for key in outcomes:
                outcomes[key] += prob * card_outcomes[key]

        return outcomes

    def _outcome_dict(self, total: int) -> dict[int, float]:
        """Create outcome dict for a standing hand."""
        outcomes = {"bust": 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
        if total > 21:
            outcomes["bust"] = 1.0
        else:
            outcomes[total] = 1.0
        return outcomes

    def get_bust_probability(self, upcard: int) -> float:
        """Get probability that dealer busts given upcard."""
        outcomes = self.get_outcome_probs(upcard)
        return outcomes["bust"]
