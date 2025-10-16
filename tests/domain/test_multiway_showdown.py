import pytest

from backend.app.domain.poker_adapter import PokerAdapter


def test_multiway_showdown_distribution_basic():
    adapter = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100.0, seed=51, num_players=3)

    hero = adapter.players[0]
    villain = adapter.players[1]
    third = adapter.players[2]

    third.folded = False
    third.active = True

    adapter.board = ["Ah", "Kh", "Qh", "2c", "2d"]
    adapter.street = "river"

    hero.cards = ["Ac", "Ad"]
    villain.cards = ["Kd", "Kc"]
    third.cards = ["Jh", "Th"]

    hero.contributed = 10.0
    villain.contributed = 10.0
    third.contributed = 5.0

    hero.stack = 90.0
    villain.stack = 90.0
    third.stack = 95.0

    adapter.pot = 25.0

    adapter._evaluate_showdown()

    assert adapter.pot == 0.0

    result_entries = [event for event in adapter.history if event["actor"] == "result"]
    assert result_entries
    result = result_entries[-1]

    pots = result["pots"]
    assert len(pots) == 2

    main_pot = pots[0]
    side_pot = pots[1]

    assert main_pot["amount"] == pytest.approx(15.0)
    assert main_pot["winners"] == [2]
    assert main_pot["share"] == pytest.approx(15.0)

    assert side_pot["amount"] == pytest.approx(10.0)
    assert side_pot["winners"] == [0]
    assert side_pot["share"] == pytest.approx(10.0)

    assert hero.stack == pytest.approx(100.0)
    assert villain.stack == pytest.approx(90.0)
    assert third.stack == pytest.approx(110.0)
