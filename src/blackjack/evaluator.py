"""Expected Value calculations for player actions."""

from functools import lru_cache

from .cards import DISTINCT_CARDS, get_card_probabilities, hand_value
from .config import GameConfig
from .dealer import DealerProbabilities


class EVCalculator:
    """Calculate expected values for each player action.

    Uses (total, soft_aces) state representation for efficiency.
    soft_aces = number of aces still counted as 11.
    """

    def __init__(self, config: GameConfig):
        self.config = config
        self.card_probs = get_card_probabilities(config.num_decks)
        self.dealer_probs = DealerProbabilities(config)
        # Pre-compute dealer outcomes for all upcards
        self._dealer_cache: dict[int, dict] = {}
        for upcard in range(2, 12):
            self._dealer_cache[upcard] = self.dealer_probs.get_outcome_probs(upcard)

    def _add_card_to_state(self, total: int, soft_aces: int, card: int) -> tuple[int, int]:
        """Add a card to a (total, soft_aces) state."""
        if card == 11:  # Ace
            new_total = total + 11
            new_soft = soft_aces + 1
        else:
            new_total = total + card
            new_soft = soft_aces

        # Convert soft aces to hard if bust
        while new_total > 21 and new_soft > 0:
            new_total -= 10
            new_soft -= 1

        return new_total, new_soft

    @lru_cache(maxsize=4096)
    def ev_stand(self, player_total: int, dealer_upcard: int) -> float:
        """Calculate EV of standing."""
        dealer_outcomes = self._dealer_cache[dealer_upcard]

        ev = dealer_outcomes["bust"]  # Win if dealer busts

        for dealer_total in [17, 18, 19, 20, 21]:
            prob = dealer_outcomes[dealer_total]
            if player_total > dealer_total:
                ev += prob
            elif player_total < dealer_total:
                ev -= prob
            # Push adds 0

        return ev

    @lru_cache(maxsize=4096)
    def ev_hit(self, total: int, soft_aces: int, dealer_upcard: int) -> float:
        """Calculate EV of hitting using (total, soft_aces) state."""
        ev = 0.0

        for card in DISTINCT_CARDS:
            prob = self.card_probs[card]
            new_total, new_soft = self._add_card_to_state(total, soft_aces, card)

            if new_total > 21:
                ev -= prob  # Bust
            else:
                # Choose best of stand or hit
                stand_ev = self.ev_stand(new_total, dealer_upcard)
                hit_ev = self.ev_hit(new_total, new_soft, dealer_upcard)
                ev += prob * max(stand_ev, hit_ev)

        return ev

    @lru_cache(maxsize=4096)
    def ev_double(self, total: int, soft_aces: int, dealer_upcard: int) -> float:
        """Calculate EV of doubling down (2x bet, one card only)."""
        ev = 0.0

        for card in DISTINCT_CARDS:
            prob = self.card_probs[card]
            new_total, _ = self._add_card_to_state(total, soft_aces, card)

            if new_total > 21:
                ev -= 2 * prob  # Lose double bet
            else:
                stand_ev = self.ev_stand(new_total, dealer_upcard)
                ev += 2 * prob * stand_ev

        return ev

    @lru_cache(maxsize=4096)
    def ev_split(self, pair_card: int, dealer_upcard: int) -> float:
        """Calculate EV of splitting a pair.

        Simplified model: assumes we play optimally after split,
        using the EV of a single-card hand.
        """
        is_ace = pair_card == 11
        ev = 0.0

        for card in DISTINCT_CARDS:
            prob = self.card_probs[card]

            # After split, we have (pair_card, new_card)
            if pair_card == 11:  # Ace
                total = 11 + (card if card != 11 else 1)
                soft_aces = 1 if card != 11 else 1
                if total > 21:
                    total -= 10
                    soft_aces = 0
            elif card == 11:  # Drew an ace
                total = pair_card + 11
                soft_aces = 1
                if total > 21:
                    total -= 10
                    soft_aces = 0
            else:
                total = pair_card + card
                soft_aces = 0

            if is_ace and not self.config.resplit_aces:
                # Only one card on split aces
                hand_ev = self.ev_stand(total, dealer_upcard)
            else:
                # Can play normally
                stand_ev = self.ev_stand(total, dealer_upcard)
                hit_ev = self.ev_hit(total, soft_aces, dealer_upcard)
                hand_ev = max(stand_ev, hit_ev)

                if self.config.double_after_split:
                    double_ev = self.ev_double(total, soft_aces, dealer_upcard)
                    hand_ev = max(hand_ev, double_ev)

            ev += prob * hand_ev

        # Two hands from the split
        return 2 * ev

    def get_all_evs(
        self,
        player_cards: tuple[int, ...],
        dealer_upcard: int,
        can_split: bool = True,
        can_double: bool = True,
    ) -> dict[str, float]:
        """Get EVs for all available actions."""
        total, is_soft = hand_value(player_cards)
        soft_aces = 1 if is_soft else 0

        evs = {
            "stand": self.ev_stand(total, dealer_upcard),
            "hit": self.ev_hit(total, soft_aces, dealer_upcard),
        }

        if can_double and len(player_cards) == 2:
            evs["double"] = self.ev_double(total, soft_aces, dealer_upcard)

        if can_split and len(player_cards) == 2 and player_cards[0] == player_cards[1]:
            evs["split"] = self.ev_split(player_cards[0], dealer_upcard)

        return evs
