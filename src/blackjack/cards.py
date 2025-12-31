"""Card values and deck probability calculations."""


# Card values: 2-9 face value, 10/J/Q/K = 10, A = 1 or 11
CARD_VALUES: dict[str, int] = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11,
}

# For calculations, we only care about distinct values
# 10, J, Q, K all have value 10
DISTINCT_CARDS: list[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # 11 represents Ace


def get_card_probabilities(num_decks: int = 0) -> dict[int, float]:
    """Get probability of drawing each card value.

    Args:
        num_decks: Number of decks. 0 for infinite deck approximation.

    Returns:
        Dictionary mapping card value to probability.
        Note: Ace is represented as 11.
    """
    if num_decks == 0:
        # Infinite deck: 4/52 for 2-9 and A, 16/52 for 10-value
        probs = {}
        for card in range(2, 10):
            probs[card] = 4 / 52  # ~0.0769
        probs[10] = 16 / 52  # ~0.3077 (10, J, Q, K)
        probs[11] = 4 / 52  # Ace ~0.0769
        return probs
    else:
        # Finite deck (same ratios, but could be extended for card removal)
        total_cards = 52 * num_decks
        probs = {}
        for card in range(2, 10):
            probs[card] = (4 * num_decks) / total_cards
        probs[10] = (16 * num_decks) / total_cards
        probs[11] = (4 * num_decks) / total_cards
        return probs


def hand_value(cards: tuple[int, ...]) -> tuple[int, bool]:
    """Calculate the value of a hand.

    Args:
        cards: Tuple of card values (Ace = 11)

    Returns:
        Tuple of (total value, is_soft)
        is_soft is True if an Ace is being counted as 11
    """
    total = sum(cards)
    aces = cards.count(11)

    # Convert aces from 11 to 1 as needed to avoid bust
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    is_soft = aces > 0 and total <= 21
    return total, is_soft


def is_bust(cards: tuple[int, ...]) -> bool:
    """Check if hand is busted."""
    value, _ = hand_value(cards)
    return value > 21


def is_blackjack(cards: tuple[int, ...]) -> bool:
    """Check if hand is a natural blackjack (A + 10-value, 2 cards only)."""
    if len(cards) != 2:
        return False
    value, _ = hand_value(cards)
    return value == 21


def is_pair(cards: tuple[int, ...]) -> bool:
    """Check if hand is a pair (for splitting)."""
    return len(cards) == 2 and cards[0] == cards[1]
