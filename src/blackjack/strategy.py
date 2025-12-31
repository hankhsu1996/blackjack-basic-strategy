"""Basic strategy calculation - optimal action selection."""


from .config import GameConfig
from .evaluator import EVCalculator

# Action codes for the strategy tables
ACTION_STAND = "S"
ACTION_HIT = "H"
ACTION_DOUBLE = "D"
ACTION_DOUBLE_OR_HIT = "Dh"  # Double if allowed, otherwise hit
ACTION_DOUBLE_OR_STAND = "Ds"  # Double if allowed, otherwise stand
ACTION_SPLIT = "P"
ACTION_SPLIT_OR_HIT = "Ph"  # Split if DAS, otherwise hit


class BasicStrategy:
    """Calculate optimal basic strategy for all situations."""

    def __init__(self, config: GameConfig | None = None):
        self.config = config or GameConfig.default()
        self.ev_calc = EVCalculator(self.config)

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
            Action code (S, H, D, Dh, Ds, P)
        """
        evs = self.ev_calc.get_all_evs(
            player_cards, dealer_upcard, can_split, can_double
        )

        # Find best action
        best_action = max(evs, key=lambda k: evs[k])

        # Handle conditional actions
        if best_action == "double":
            # Check what we'd do without double
            stand_ev = evs["stand"]
            hit_ev = evs["hit"]
            if stand_ev >= hit_ev:
                return ACTION_DOUBLE_OR_STAND
            else:
                return ACTION_DOUBLE_OR_HIT

        if best_action == "split":
            return ACTION_SPLIT

        if best_action == "stand":
            return ACTION_STAND

        return ACTION_HIT

    def get_hard_strategy(self) -> dict[tuple[int, int], str]:
        """Generate strategy for hard hands.

        Returns:
            Dict mapping (player_total, dealer_upcard) -> action
        """
        strategy = {}

        for player_total in range(5, 22):  # Hard 5 through 21
            for dealer_upcard in range(2, 12):  # 2-10, 11=Ace
                upcard = dealer_upcard if dealer_upcard <= 10 else 11

                # Create a hard hand with this total
                if player_total <= 11:
                    cards = (player_total,)  # Simplified representation
                else:
                    # Use two cards that sum to total without ace-as-11
                    cards = (10, player_total - 10) if player_total > 11 else (player_total,)

                # For proper EV calculation, we need valid card tuples
                cards = self._make_hard_hand(player_total)

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

    def _make_hard_hand(self, total: int) -> tuple[int, ...]:
        """Create a hard hand tuple for a given total."""
        if total <= 10:
            # Single card or small cards
            if total <= 11:
                return (total,) if total >= 2 else (2,)
            return (total,)
        elif total == 11:
            return (6, 5)
        elif total <= 19:
            return (10, total - 10)
        elif total == 20:
            return (10, 10)
        else:  # 21
            return (10, 6, 5)
