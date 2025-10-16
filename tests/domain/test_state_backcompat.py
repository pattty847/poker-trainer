from backend.app.domain.poker_adapter import PokerAdapter


def test_state_back_compat_minimal():
    adapter = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100.0, seed=11, num_players=3)

    state = adapter.get_state("session")

    for key in ("hero", "villain", "action", "history"):
        assert key in state

    metadata = state["metadata"]
    assert metadata["toActSeat"] == adapter.to_act
    assert metadata["currentBet"] == round(adapter.current_bet, 2)

    players = metadata["players"]
    assert len(players) == 3

    hero_meta = players[0]
    villain_meta = players[1]
    extra_meta = players[2]

    assert hero_meta["seat"] == adapter.hero.seat == 0
    assert villain_meta["seat"] == adapter.villain.seat == 1
    assert hero_meta["cards"] == adapter.hero.cards
    assert villain_meta["cards"] == []

    assert extra_meta["seat"] == 2
    assert extra_meta["cards"] == []
    assert extra_meta["contributed"] == 0.0
    assert extra_meta["current_bet"] == 0.0
