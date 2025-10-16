import pytest

from backend.app.domain.poker_adapter import PokerAdapter


def _make_adapter(seed: int = 21) -> PokerAdapter:
    return PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100.0, seed=seed, num_players=2)


def test_preflop_call_to_flop_and_toact():
    adapter = _make_adapter()

    adapter.apply_hero_action("call")

    assert adapter.street == "flop"
    assert len(adapter.board) == 3
    assert adapter.to_act == 1 - adapter.btn_seat


def test_postflop_check_villain_bet_contributions():
    adapter = _make_adapter(seed=22)
    adapter.apply_hero_action("call")
    adapter.board = ["As", "Kd", "2c"]

    adapter.apply_hero_action("check")

    bet_events = [e for e in adapter.history if e["actor"] == "villain" and e["move"] == "bet" and e["street"] == "flop"]
    assert bet_events, "villain should bet once hero checks on the flop"

    assert adapter.street in ("turn", "showdown")
    assert adapter.current_bet == pytest.approx(adapter.villain.current_bet)
    assert adapter.hero.contributed == pytest.approx(adapter.villain.contributed)
