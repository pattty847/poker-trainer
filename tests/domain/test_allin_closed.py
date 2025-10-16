from backend.app.domain.poker_adapter import PokerAdapter


def test_allin_excluded_from_next_to_act_but_eligible_in_pots():
    """Test that all-in players are excluded from next_to_act but eligible in pots."""
    adapter = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=10.0, seed=61, num_players=2)

    adapter.apply_hero_action("call")

    adapter.villain.stack = 0.0
    adapter.villain.current_bet = adapter.current_bet

    next_seat = adapter.next_to_act()
    assert next_seat != adapter.villain.seat
    assert next_seat == adapter.hero.seat

    adapter.hero.contributed = 5.0
    adapter.villain.contributed = 5.0
    adapter.hero.stack = 5.0
    adapter.pot = 10.0

    pots = adapter.calculate_side_pots()
    assert any(adapter.villain.seat in pot["eligible_players"] for pot in pots)
