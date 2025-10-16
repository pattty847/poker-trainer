from backend.app.domain.poker_adapter import PokerAdapter


def test_calculate_side_pots_tiers():
    adapter = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100.0, seed=41, num_players=3)

    for player in adapter.players:
        player.folded = False

    adapter.players[0].contributed = 10.0
    adapter.players[1].contributed = 6.0
    adapter.players[2].contributed = 10.0
    adapter.pot = 26.0

    pots = adapter.calculate_side_pots()

    assert len(pots) == 2
    assert pots[0]["amount"] == 18.0
    assert set(pots[0]["eligible_players"]) == {0, 1, 2}
    assert pots[1]["amount"] == 8.0
    assert set(pots[1]["eligible_players"]) == {0, 2}
