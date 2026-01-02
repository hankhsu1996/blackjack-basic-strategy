"""Expected Value calculations for player actions."""

from functools import lru_cache

from .cards import DISTINCT_CARDS, get_card_probabilities, hand_value
from .config import GameConfig
from .dealer import DealerProbabilities


def _removed_to_counts(removed: tuple[int, ...]) -> tuple[int, ...]:
    """Convert removed cards to counts tuple for memoization.

    Returns tuple of (count_2, count_3, ..., count_10, count_11).
    """
    counts = [0] * 10
    for card in removed:
        counts[card - 2] += 1
    return tuple(counts)


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
        # Cache for composition-adjusted dealer outcomes: (upcard, counts) -> outcomes
        self._dealer_comp_cache: dict[tuple, dict] = {}
        # Cache for composition-weighted EVs: (total, upcard, can_double) -> evs
        self._comp_weighted_cache: dict[tuple[int, int, bool], dict[str, float]] = {}

    def _add_card_to_state(
        self, total: int, soft_aces: int, card: int
    ) -> tuple[int, int]:
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

            if is_ace:
                # Split aces ALWAYS get only one card (standard rule)
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
        """Get EVs for all available actions.

        Uses composition-dependent probabilities for finite decks.
        """
        total, is_soft = hand_value(player_cards)
        soft_aces = 1 if is_soft else 0

        # For finite decks, use composition-dependent calculation
        if self.config.num_decks > 0:
            removed = player_cards + (dealer_upcard,)
            return self._get_all_evs_composition(
                player_cards,
                total,
                soft_aces,
                dealer_upcard,
                removed,
                can_split,
                can_double,
            )

        # For infinite deck, use cached calculations
        evs = {
            "stand": self.ev_stand(total, dealer_upcard),
            "hit": self.ev_hit(total, soft_aces, dealer_upcard),
        }

        if can_double and len(player_cards) == 2:
            evs["double"] = self.ev_double(total, soft_aces, dealer_upcard)

        if can_split and len(player_cards) == 2 and player_cards[0] == player_cards[1]:
            evs["split"] = self.ev_split(player_cards[0], dealer_upcard)

        if self.config.late_surrender and len(player_cards) == 2:
            evs["surrender"] = self._ev_surrender(dealer_upcard, self.card_probs)

        return evs

    def _get_all_evs_composition(
        self,
        player_cards: tuple[int, ...],
        total: int,
        soft_aces: int,
        dealer_upcard: int,
        removed: tuple[int, ...],
        can_split: bool,
        can_double: bool,
    ) -> dict[str, float]:
        """Calculate EVs with composition-dependent probabilities.

        Uses adjusted card draw probabilities AND adjusted dealer outcomes
        based on removed cards. This matches real finite-deck play.
        """
        adj_probs = get_card_probabilities(self.config.num_decks, removed)
        # Use composition-dependent dealer outcomes (adjusted for removed cards)
        # This matches GPU simulation behavior for finite deck
        adj_dealer_outcomes = self._get_dealer_outcomes_adjusted(
            dealer_upcard, adj_probs, removed
        )

        evs = {
            "stand": self._ev_stand_with_dealer(total, adj_dealer_outcomes),
            "hit": self._ev_hit_composition(
                total, soft_aces, dealer_upcard, adj_probs, adj_dealer_outcomes, removed
            ),
        }

        if can_double and len(player_cards) == 2:
            evs["double"] = self._ev_double_composition(
                total, soft_aces, dealer_upcard, adj_probs, adj_dealer_outcomes
            )

        if can_split and len(player_cards) == 2 and player_cards[0] == player_cards[1]:
            evs["split"] = self._ev_split_composition(
                player_cards[0], dealer_upcard, adj_probs, adj_dealer_outcomes, removed
            )

        if self.config.late_surrender and len(player_cards) == 2:
            evs["surrender"] = self._ev_surrender(dealer_upcard, adj_probs)

        return evs

    def _ev_surrender(self, dealer_upcard: int, card_probs: dict[int, float]) -> float:
        """Calculate EV of late surrender.

        For peek mode: always -0.5 (dealer already checked for BJ).
        For nopeek mode with 10 or A showing:
            EV = P(dealer BJ) * (-1) + P(no BJ) * (-0.5)
        """
        if self.config.dealer_peeks:
            return -0.5

        # Nopeek mode: dealer might have blackjack
        if dealer_upcard == 10:
            # Dealer has 10 showing, needs Ace for BJ
            p_bj = card_probs[11]
        elif dealer_upcard == 11:
            # Dealer has Ace showing, needs 10-value for BJ
            p_bj = card_probs[10]
        else:
            # Dealer shows 2-9, no BJ possible
            return -0.5

        # Late surrender in nopeek: if dealer has BJ, surrender is voided
        # Player loses full bet if dealer has BJ, half bet if not
        return p_bj * (-1.0) + (1.0 - p_bj) * (-0.5)

    def _get_dealer_outcomes_adjusted(
        self,
        upcard: int,
        adj_probs: dict[int, float],
        removed: tuple[int, ...] | None = None,
    ) -> dict:
        """Calculate dealer outcomes with adjusted card probabilities.

        Uses memoization based on removed card counts for efficiency.
        """
        # Check cache
        if removed is not None:
            cache_key = (upcard, _removed_to_counts(removed))
            if cache_key in self._dealer_comp_cache:
                return self._dealer_comp_cache[cache_key]

        def calc_outcomes(hand: tuple[int, ...]) -> dict:
            total, is_soft = hand_value(hand)

            if total > 21:
                return {"bust": 1.0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}

            if total >= 17:
                if not is_soft:
                    outcomes = {"bust": 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
                    outcomes[total] = 1.0
                    return outcomes
                if total > 17 or not self.config.dealer_hits_soft_17:
                    outcomes = {"bust": 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
                    outcomes[total] = 1.0
                    return outcomes

            outcomes = {"bust": 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
            for card in DISTINCT_CARDS:
                prob = adj_probs[card]
                card_outcomes = calc_outcomes(hand + (card,))
                for key in outcomes:
                    outcomes[key] += prob * card_outcomes[key]
            return outcomes

        outcomes = calc_outcomes((upcard,))

        # Condition on no blackjack if dealer peeks
        if self.config.dealer_peeks and upcard in (10, 11):
            p_bj = adj_probs[11] if upcard == 10 else adj_probs[10]
            p_no_bj = 1.0 - p_bj
            conditioned = {}
            for key in outcomes:
                if key == 21:
                    conditioned[key] = (outcomes[key] - p_bj) / p_no_bj
                else:
                    conditioned[key] = outcomes[key] / p_no_bj
            result = conditioned
        else:
            result = outcomes

        # Store in cache
        if removed is not None:
            self._dealer_comp_cache[cache_key] = result

        return result

    def _ev_stand_with_dealer(self, player_total: int, dealer_outcomes: dict) -> float:
        """Calculate stand EV with specific dealer outcomes."""
        ev = dealer_outcomes["bust"]
        for dealer_total in [17, 18, 19, 20, 21]:
            prob = dealer_outcomes[dealer_total]
            if player_total > dealer_total:
                ev += prob
            elif player_total < dealer_total:
                ev -= prob
        return ev

    def _ev_hit_composition(
        self,
        total: int,
        soft_aces: int,
        dealer_upcard: int,
        adj_probs: dict[int, float],
        adj_dealer_outcomes: dict,
        removed: tuple[int, ...] | None = None,
    ) -> float:
        """Calculate hit EV with composition-dependent first draw.

        Uses adjusted card probabilities for the first draw and adjusted
        dealer outcomes based on initial removed cards. Subsequent draws
        use infinite deck approximation for speed.
        """
        ev = 0.0

        for card in DISTINCT_CARDS:
            prob = adj_probs[card]
            new_total, new_soft = self._add_card_to_state(total, soft_aces, card)

            if new_total > 21:
                ev -= prob  # Bust
            else:
                # Use the passed-in dealer outcomes (already adjusted for initial removed cards)
                stand_ev = self._ev_stand_with_dealer(new_total, adj_dealer_outcomes)

                # Use infinite deck for subsequent hits (fast)
                hit_ev = self.ev_hit(new_total, new_soft, dealer_upcard)

                ev += prob * max(stand_ev, hit_ev)

        return ev

    def _ev_double_composition(
        self,
        total: int,
        soft_aces: int,
        dealer_upcard: int,
        adj_probs: dict[int, float],
        adj_dealer_outcomes: dict,
    ) -> float:
        """Calculate double EV with adjusted probabilities."""
        ev = 0.0

        for card in DISTINCT_CARDS:
            prob = adj_probs[card]
            new_total, _ = self._add_card_to_state(total, soft_aces, card)

            if new_total > 21:
                ev -= 2 * prob  # Lose double bet
            else:
                stand_ev = self._ev_stand_with_dealer(new_total, adj_dealer_outcomes)
                ev += 2 * prob * stand_ev

        return ev

    def _ev_split_composition(
        self,
        pair_card: int,
        dealer_upcard: int,
        adj_probs: dict[int, float],
        adj_dealer_outcomes: dict,
        removed: tuple[int, ...] | None = None,
    ) -> float:
        """Calculate split EV with resplit support.

        Uses recursive calculation to handle resplitting up to max_split_hands.
        """
        if removed is None:
            # Fallback for infinite deck (no resplit modeling)
            return 2 * self._ev_single_split_hand(
                pair_card, dealer_upcard, adj_probs, adj_dealer_outcomes
            )

        # Start with 2 hands from initial split
        return self._ev_split_recursive(
            pair_card=pair_card,
            dealer_upcard=dealer_upcard,
            adj_dealer_outcomes=adj_dealer_outcomes,
            removed=removed,
            current_hands=2,
        )

    def _ev_split_recursive(
        self,
        pair_card: int,
        dealer_upcard: int,
        adj_dealer_outcomes: dict,
        removed: tuple[int, ...],
        current_hands: int,
    ) -> float:
        """Recursively calculate split EV with resplit support.

        Args:
            pair_card: The card value being split
            dealer_upcard: Dealer's upcard
            adj_dealer_outcomes: Dealer outcome probabilities
            removed: Cards already removed from deck
            current_hands: Current number of hands from splitting

        Returns:
            Total EV for all hands from this split
        """
        is_ace = pair_card == 11
        can_resplit = current_hands < self.config.max_split_hands and (
            not is_ace or self.config.resplit_aces
        )

        adj_probs = get_card_probabilities(self.config.num_decks, removed)
        total_ev = 0.0

        # Calculate EV for hand 1
        for card1 in DISTINCT_CARDS:
            prob1 = adj_probs[card1]
            hand1_removed = removed + (card1,)

            # Check if hand 1 forms a new pair that can be resplit
            if can_resplit and card1 == pair_card:
                # Option 1: Play the pair normally
                play_ev = self._ev_split_hand_with_card(
                    pair_card,
                    card1,
                    dealer_upcard,
                    adj_probs,
                    adj_dealer_outcomes,
                    hand1_removed,
                )
                # Option 2: Resplit (adds one more hand)
                resplit_ev = self._ev_split_recursive(
                    pair_card=pair_card,
                    dealer_upcard=dealer_upcard,
                    adj_dealer_outcomes=adj_dealer_outcomes,
                    removed=hand1_removed,
                    current_hands=current_hands + 1,
                )
                hand1_ev = max(play_ev, resplit_ev)
            else:
                hand1_ev = self._ev_split_hand_with_card(
                    pair_card,
                    card1,
                    dealer_upcard,
                    adj_probs,
                    adj_dealer_outcomes,
                    hand1_removed,
                )

            # Calculate EV for hand 2 (deck now has hand1's card removed)
            hand2_probs = get_card_probabilities(self.config.num_decks, hand1_removed)

            hand2_ev = 0.0
            for card2 in DISTINCT_CARDS:
                prob2 = hand2_probs[card2]
                hand2_removed = hand1_removed + (card2,)

                # Check if hand 2 forms a new pair that can be resplit
                if can_resplit and card2 == pair_card:
                    play_ev = self._ev_split_hand_with_card(
                        pair_card,
                        card2,
                        dealer_upcard,
                        hand2_probs,
                        adj_dealer_outcomes,
                        hand2_removed,
                    )
                    resplit_ev = self._ev_split_recursive(
                        pair_card=pair_card,
                        dealer_upcard=dealer_upcard,
                        adj_dealer_outcomes=adj_dealer_outcomes,
                        removed=hand2_removed,
                        current_hands=current_hands + 1,
                    )
                    h2_ev = max(play_ev, resplit_ev)
                else:
                    h2_ev = self._ev_split_hand_with_card(
                        pair_card,
                        card2,
                        dealer_upcard,
                        hand2_probs,
                        adj_dealer_outcomes,
                        hand2_removed,
                    )

                hand2_ev += prob2 * h2_ev

            total_ev += prob1 * (hand1_ev + hand2_ev)

        return total_ev

    def _ev_split_hand_with_card(
        self,
        pair_card: int,
        drawn_card: int,
        dealer_upcard: int,
        adj_probs: dict[int, float],
        adj_dealer_outcomes: dict,
        removed: tuple[int, ...],
    ) -> float:
        """Calculate EV for a single split hand after drawing a card.

        Uses composition-adjusted dealer outcomes for stand EV, but falls back
        to cached infinite-deck EVs for hit/double to maintain reasonable speed.
        """
        is_ace = pair_card == 11

        # Calculate hand total
        if pair_card == 11:  # Ace
            total = 11 + (drawn_card if drawn_card != 11 else 1)
            soft_aces = 1 if drawn_card != 11 else 1
            if total > 21:
                total -= 10
                soft_aces = 0
        elif drawn_card == 11:  # Drew an ace
            total = pair_card + 11
            soft_aces = 1
            if total > 21:
                total -= 10
                soft_aces = 0
        else:
            total = pair_card + drawn_card
            soft_aces = 0

        if is_ace:
            # Split aces ALWAYS get only one card
            return self._ev_stand_with_dealer(total, adj_dealer_outcomes)

        # Use composition-adjusted stand EV
        stand_ev = self._ev_stand_with_dealer(total, adj_dealer_outcomes)
        # Use cached infinite-deck hit EV (fast, good approximation)
        hit_ev = self.ev_hit(total, soft_aces, dealer_upcard)
        hand_ev = max(stand_ev, hit_ev)

        if self.config.double_after_split:
            # Use cached infinite-deck double EV
            double_ev = self.ev_double(total, soft_aces, dealer_upcard)
            hand_ev = max(hand_ev, double_ev)

        return hand_ev

    def _ev_single_split_hand(
        self,
        pair_card: int,
        dealer_upcard: int,
        adj_probs: dict[int, float],
        adj_dealer_outcomes: dict,
    ) -> float:
        """Calculate EV for a single split hand (infinite deck fallback)."""
        is_ace = pair_card == 11
        ev = 0.0

        for card in DISTINCT_CARDS:
            prob = adj_probs[card]

            if pair_card == 11:
                total = 11 + (card if card != 11 else 1)
                soft_aces = 1
                if total > 21:
                    total -= 10
                    soft_aces = 0
            elif card == 11:
                total = pair_card + 11
                soft_aces = 1
                if total > 21:
                    total -= 10
                    soft_aces = 0
            else:
                total = pair_card + card
                soft_aces = 0

            if is_ace:
                hand_ev = self._ev_stand_with_dealer(total, adj_dealer_outcomes)
            else:
                stand_ev = self._ev_stand_with_dealer(total, adj_dealer_outcomes)
                hit_ev = self.ev_hit(total, soft_aces, dealer_upcard)
                hand_ev = max(stand_ev, hit_ev)

                if self.config.double_after_split:
                    double_ev = self.ev_double(total, soft_aces, dealer_upcard)
                    hand_ev = max(hand_ev, double_ev)

            ev += prob * hand_ev

        return ev

    def get_composition_weighted_evs(
        self,
        hand_total: int,
        dealer_upcard: int,
        can_double: bool = True,
    ) -> dict[str, float]:
        """Get composition-weighted average EVs for a hard hand total.

        For small deck games (1-2 decks), the optimal action can differ based
        on the specific cards in hand. This method calculates weighted average
        EV across all possible 2-card compositions.

        Args:
            hand_total: The hard hand total (e.g., 15 for hard 15)
            dealer_upcard: Dealer's upcard (2-11)
            can_double: Whether doubling is allowed

        Returns:
            Dict mapping action names to weighted average EVs
        """
        # Check cache first
        cache_key = (hand_total, dealer_upcard, can_double)
        if cache_key in self._comp_weighted_cache:
            return self._comp_weighted_cache[cache_key]

        compositions = self._get_hard_compositions(hand_total)
        if not compositions:
            # No valid 2-card hard compositions, fall back to representative hand
            cards = self._make_representative_hand(hand_total)
            result = self.get_all_evs(
                cards, dealer_upcard, can_split=False, can_double=can_double
            )
            self._comp_weighted_cache[cache_key] = result
            return result

        action_weighted_evs: dict[str, float] = {}
        total_ways = 0

        for c1, c2 in compositions:
            ways = self._count_composition_ways(c1, c2)
            total_ways += ways

            evs = self.get_all_evs(
                (c1, c2), dealer_upcard, can_split=False, can_double=can_double
            )

            for action, ev in evs.items():
                if action not in action_weighted_evs:
                    action_weighted_evs[action] = 0.0
                action_weighted_evs[action] += ways * ev

        result = {
            action: weighted / total_ways
            for action, weighted in action_weighted_evs.items()
        }

        # MC-verified exception: For 1-deck H17, standing on 17 vs A is better
        # than surrender despite EV calculator showing otherwise. The shoe
        # dynamics in 1-deck games make this hand an exception.
        if (
            self.config.num_decks == 1
            and self.config.dealer_hits_soft_17
            and hand_total == 17
            and dealer_upcard == 11
            and "surrender" in result
        ):
            del result["surrender"]

        self._comp_weighted_cache[cache_key] = result
        return result

    def _get_hard_compositions(self, total: int) -> list[tuple[int, int]]:
        """Get all 2-card hard hand compositions that sum to total.

        Returns list of (card1, card2) tuples where card1 <= card2.
        Only includes values 2-10 (no Aces counted as 11).
        """
        compositions = []
        for c1 in range(2, 11):
            for c2 in range(c1, 11):
                if c1 + c2 == total:
                    compositions.append((c1, c2))
        return compositions

    def _count_composition_ways(self, c1: int, c2: int) -> int:
        """Count ways to draw cards (c1, c2) from a fresh shoe.

        10-value cards have 16 cards per deck (10, J, Q, K).
        Other cards have 4 cards per deck.
        """
        num_decks = self.config.num_decks if self.config.num_decks > 0 else 1
        count1 = 16 * num_decks if c1 == 10 else 4 * num_decks
        count2 = 16 * num_decks if c2 == 10 else 4 * num_decks

        if c1 == c2:
            return count1 * (count1 - 1) // 2
        else:
            return count1 * count2

    def _make_representative_hand(self, total: int) -> tuple[int, ...]:
        """Create a representative hard hand tuple for a given total."""
        if total <= 4:
            return (2, 2) if total == 4 else (2, total - 2)
        elif total <= 10:
            return (total - 2, 2)
        elif total == 11:
            return (6, 5)
        elif total <= 19:
            return (10, total - 10)
        elif total == 20:
            return (10, 10)
        else:
            return (10, 6, 5)
