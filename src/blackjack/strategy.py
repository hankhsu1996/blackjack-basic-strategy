"""Basic strategy calculation - optimal action selection."""

from .config import GameConfig
from .evaluator import EVCalculator

# Threshold for using composition-weighted average (small decks).
# For 1-2 deck games, composition effects are significant enough that
# using a single (10, X) composition can give wrong recommendations.
COMPOSITION_WEIGHTED_DECK_THRESHOLD = 2

# Minimum hand total for composition-weighted calculation.
# Only stiff hands (12+) have close decisions where composition matters.
COMPOSITION_WEIGHTED_MIN_TOTAL = 12

# Action codes for the strategy tables
ACTION_STAND = "S"
ACTION_HIT = "H"
ACTION_DOUBLE = "D"
ACTION_DOUBLE_OR_HIT = "Dh"  # Double if allowed, otherwise hit
ACTION_DOUBLE_OR_STAND = "Ds"  # Double if allowed, otherwise stand
ACTION_SPLIT = "P"
ACTION_SPLIT_OR_HIT = "Ph"  # Split if DAS, otherwise hit
ACTION_SURRENDER = "R"  # Surrender (give up half bet)


class BasicStrategy:
    """Calculate optimal basic strategy for all situations."""

    def __init__(self, config: GameConfig | None = None):
        self.config = config or GameConfig.default()
        self.ev_calc = EVCalculator(self.config)

    def _evs_to_action(self, evs: dict[str, float]) -> str:
        """Convert EV dictionary to action code.

        Args:
            evs: Dictionary mapping action names to their EVs

        Returns:
            Action code (S, H, D, Dh, Ds, P, R)
        """
        best_action = max(evs, key=lambda k: evs[k])

        if best_action == "double":
            stand_ev = evs.get("stand", float("-inf"))
            hit_ev = evs.get("hit", float("-inf"))
            return (
                ACTION_DOUBLE_OR_STAND if stand_ev >= hit_ev else ACTION_DOUBLE_OR_HIT
            )

        if best_action == "split":
            return ACTION_SPLIT

        if best_action == "surrender":
            return ACTION_SURRENDER

        if best_action == "stand":
            return ACTION_STAND

        return ACTION_HIT

    def get_action(
        self,
        player_cards: tuple[int, ...],
        dealer_upcard: int,
        can_split: bool = True,
        can_double: bool = True,
    ) -> str:
        """Get the optimal action for a given situation.

        Args:
            player_cards: Player's cards
            dealer_upcard: Dealer's upcard (2-11)
            can_split: Whether splitting is allowed
            can_double: Whether doubling is allowed

        Returns:
            Action code (S, H, D, Dh, Ds, P, R)
        """
        evs = self.ev_calc.get_all_evs(
            player_cards, dealer_upcard, can_split, can_double
        )
        return self._evs_to_action(evs)

    def get_hard_strategy(self) -> dict[tuple[int, int], str]:
        """Generate strategy for hard hands.

        Returns:
            Dict mapping (player_total, dealer_upcard) -> action

        For small deck games (1-2 decks), uses composition-weighted average
        EV across all possible 2-card combinations to determine optimal action.
        """
        strategy = {}
        use_weighted = (
            self.config.num_decks > 0
            and self.config.num_decks <= COMPOSITION_WEIGHTED_DECK_THRESHOLD
        )

        for player_total in range(5, 22):  # Hard 5 through 21
            for dealer_upcard in range(2, 12):  # 2-10, 11=Ace
                upcard = dealer_upcard if dealer_upcard <= 10 else 11

                if use_weighted and player_total >= COMPOSITION_WEIGHTED_MIN_TOTAL:
                    action = self._get_composition_weighted_action(player_total, upcard)
                else:
                    cards = self.ev_calc._make_representative_hand(player_total)
                    action = self.get_action(cards, upcard, can_split=False)

                strategy[(player_total, dealer_upcard)] = action

        return strategy

    def get_soft_strategy(self) -> dict[tuple[int, int], str]:
        """Generate strategy for soft hands (hands with Ace as 11).

        Returns:
            Dict mapping (other_card, dealer_upcard) -> action
            other_card is 2-9 (the non-ace card in A,X)
        """
        strategy = {}

        for other_card in range(2, 10):  # A2 through A9
            for dealer_upcard in range(2, 12):
                upcard = dealer_upcard if dealer_upcard <= 10 else 11
                cards = (11, other_card)  # Ace + other card

                action = self.get_action(cards, upcard, can_split=False)
                strategy[(other_card, dealer_upcard)] = action

        return strategy

    def get_pair_strategy(self) -> dict[tuple[int, int], str]:
        """Generate strategy for pairs.

        Returns:
            Dict mapping (pair_card, dealer_upcard) -> action
        """
        strategy = {}

        for pair_card in range(2, 12):  # 2,2 through A,A
            card_val = pair_card if pair_card <= 10 else 11
            for dealer_upcard in range(2, 12):
                upcard = dealer_upcard if dealer_upcard <= 10 else 11
                cards = (card_val, card_val)

                action = self.get_action(cards, upcard, can_split=True)
                strategy[(pair_card, dealer_upcard)] = action

        return strategy

    def _get_composition_weighted_action(self, total: int, dealer_upcard: int) -> str:
        """Get optimal action using composition-weighted EV average.

        Delegates to EVCalculator.get_composition_weighted_evs() for the
        weighted average calculation.
        """
        avg_evs = self.ev_calc.get_composition_weighted_evs(
            total, dealer_upcard, can_double=True
        )
        return self._evs_to_action(avg_evs)
