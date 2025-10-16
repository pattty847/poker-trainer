from backend.app.domain.poker_adapter import PokerAdapter


def test_btn_rotates_on_reset():
    adapter = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100.0, seed=31, num_players=2)
    first_button = adapter.btn_seat

    adapter.reset_hand()

    assert adapter.btn_seat != first_button
    assert adapter.players[adapter.btn_seat].position == "btn"
    assert adapter.players[1 - adapter.btn_seat].position == "bb"
    assert adapter.to_act == adapter.btn_seat
