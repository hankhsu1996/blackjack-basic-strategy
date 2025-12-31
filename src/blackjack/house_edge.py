"""House edge calculation for blackjack."""

from .cards import DISTINCT_CARDS, get_card_probabilities, is_blackjack
from .config import GameConfig
from .evaluator import EVCalculator


class HouseEdgeCalculator:
    """Calculate house edge for a given configuration.

    The house edge is calculated by weighting the optimal EV for each
    possible starting hand by its probability of occurring.
    """

    def __init__(self, config: GameConfig):
        self.config = config
        # Always use peek=True for EV calculation to get conditioned EVs
        # We handle dealer BJ probability separately in _calculate_hand_ev
        config_for_ev = GameConfig(
            num_decks=config.num_decks,
            dealer_hits_soft_17=config.dealer_hits_soft_17,
            double_after_split=config.double_after_split,
            resplit_aces=config.resplit_aces,
            blackjack_pays=config.blackjack_pays,
            dealer_peeks=True,  # Always condition on no dealer BJ
        )
        self.ev_calc = EVCalculator(config_for_ev)
        self.card_probs = get_card_probabilities(config.num_decks)

    def calculate(self, verbose: bool = False) -> float:
        """Calculate house edge as a percentage.

        Returns:
            House edge as percentage (e.g., 0.5 means 0.5% house edge).
            Positive values favor the house, negative favor the player.
        """
        expected_return = 0.0
        total_hands = len(DISTINCT_CARDS) ** 3  # 10^3 = 1000 combinations
        processed = 0

        # Iterate over all possible starting hands
        # Player gets 2 cards, then we see dealer upcard
        for i, card1 in enumerate(DISTINCT_CARDS):
            if verbose:
                print(f"Processing card1={card1} ({i+1}/10)...")
            p1 = self.card_probs[card1]

            for card2 in DISTINCT_CARDS:
                p2 = self._adjusted_prob(card2, (card1,))
                player_cards = (card1, card2)
                p_player = p1 * p2

                for upcard in DISTINCT_CARDS:
                    p_upcard = self._adjusted_prob(upcard, player_cards)
                    p_total = p_player * p_upcard

                    # Calculate EV for this situation
                    ev = self._calculate_hand_ev(player_cards, upcard)
                    expected_return += p_total * ev
                    processed += 1

        # House edge is negative of expected return
        house_edge = -expected_return * 100
        return house_edge

    def _adjusted_prob(self, card: int, removed: tuple[int, ...]) -> float:
        """Get adjusted probability after removing cards."""
        if self.config.num_decks == 0:
            # Infinite deck: no adjustment needed
            return self.card_probs[card]
        else:
            adj_probs = get_card_probabilities(self.config.num_decks, removed)
            return adj_probs[card]

    def _calculate_hand_ev(self, player_cards: tuple[int, ...], upcard: int) -> float:
        """Calculate expected value for a starting hand.

        Handles blackjack cases specially.

        Note: When dealer_peeks is True, EVCalculator returns EVs that are
        conditioned on dealer NOT having blackjack. We need to weight these
        by P(no dealer BJ) and add the dealer BJ case separately.
        """
        player_bj = is_blackjack(player_cards)

        # Calculate probability of dealer blackjack given the upcard
        if upcard == 10:
            # Dealer shows 10, needs Ace for BJ
            p_dealer_bj = self._adjusted_prob(11, player_cards + (upcard,))
        elif upcard == 11:
            # Dealer shows Ace, needs 10 for BJ
            p_dealer_bj = self._adjusted_prob(10, player_cards + (upcard,))
        else:
            p_dealer_bj = 0.0

        p_no_dealer_bj = 1 - p_dealer_bj

        if player_bj:
            # Player has blackjack
            # If dealer also has BJ: push (EV = 0)
            # If dealer doesn't have BJ: win blackjack_pays
            return p_no_dealer_bj * self.config.blackjack_pays + p_dealer_bj * 0
        else:
            # Player doesn't have blackjack
            # If dealer has BJ: player loses immediately (EV = -1)
            # If dealer doesn't have BJ: play normally

            # Get optimal EV for normal play (conditioned on no dealer BJ)
            evs = self.ev_calc.get_all_evs(player_cards, upcard)
            ev_no_dealer_bj = max(evs.values())

            # Weight by probability of each scenario
            return p_no_dealer_bj * ev_no_dealer_bj + p_dealer_bj * (-1)
