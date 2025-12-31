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

        When dealer_peeks is True and upcard is 10 or A, the probabilities
        are conditioned on dealer NOT having blackjack (since player would
        have already lost).

        Args:
            upcard: Dealer's upcard value (2-11, where 11 is Ace)

        Returns:
            Dictionary with keys 17, 18, 19, 20, 21, 'bust'
            mapping to probabilities.
        """
        # Start with dealer's upcard
        initial_hand = (upcard,)
        outcomes = self._calculate_outcomes(initial_hand)

        # If dealer peeks for blackjack and shows 10 or A, condition on no BJ
        if self.config.dealer_peeks and upcard in (10, 11):
            outcomes = self._condition_on_no_blackjack(upcard, outcomes)

        return outcomes

    def _condition_on_no_blackjack(
        self, upcard: int, outcomes: dict[int, float]
    ) -> dict[int, float]:
        """Condition outcome probabilities on dealer not having blackjack.

        When dealer shows 10 or A and peeks, we know they don't have BJ.
        This removes the blackjack probability from P(21) and renormalizes.
        """
        # P(blackjack): Ace if showing 10, 10-value if showing Ace
        p_bj = self.card_probs[11] if upcard == 10 else self.card_probs[10]

        p_no_bj = 1.0 - p_bj

        # The unconditional P(21) includes blackjack
        # P(21 | no BJ) = (P(21) - P(BJ)) / P(no BJ)
        # P(other | no BJ) = P(other) / P(no BJ)
        conditioned = {}
        for key in outcomes:
            if key == 21:
                # Remove blackjack probability from 21
                conditioned[key] = (outcomes[key] - p_bj) / p_no_bj
            else:
                conditioned[key] = outcomes[key] / p_no_bj

        return conditioned

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
