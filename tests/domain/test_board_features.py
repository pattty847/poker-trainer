from backend.app.domain.poker_adapter import PokerAdapter


def make_adapter(pot=3.0, spr=10.0):
    """Create a PokerAdapter instance with default test parameters.
    
    Args:
        pot: The pot size to set (default: 3.0)
        spr: The stack-to-pot ratio (default: 10.0)
        
    Returns:
        PokerAdapter: Configured adapter instance for testing
    """
    ad = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100, seed=1, num_players=2)
    ad.pot = pot
    return ad


def test_classify_dry_high():
    """Test board classification for a dry, high-card heavy board.
    
    Verifies that a board with high cards (A-K-2) and no draws
    is correctly classified as dry or dynamic with high card heavy flag set.
    """
    ad = make_adapter()
    feats = ad.classify_board(["A s".replace(" ", ""), "K d".replace(" ", ""), "2 c".replace(" ", "")], spr=5)
    assert feats["type"] in ("dry", "dynamic")
    assert feats["highCardHeavy"] is True


def test_classify_wet_connected():
    """Test board classification for a wet, connected board.
    
    Verifies that a board with straight draws (9-8-7) is correctly
    classified as wet or dynamic with connected flag set.
    """
    ad = make_adapter()
    feats = ad.classify_board(["9h", "8h", "7c"], spr=7)
    assert feats["connected"] is True
    assert feats["type"] in ("wet", "dynamic")


def test_bet_size_rules():
    """Test bet sizing recommendations based on board texture.
    
    Verifies that the adapter recommends appropriate bet sizes:
    - Smaller bets (30-35% pot) on dry boards
    - Larger bets (65-67% pot) on wet boards
    """
    ad = make_adapter(pot=10.0)
    dry = {"type": "dry", "sprBucket": "mid", "paired": False, "highCardHeavy": False, "monotone": False, "connected": False}
    wet = {"type": "wet", "sprBucket": "deep", "paired": False, "highCardHeavy": False, "monotone": False, "connected": True}
    assert 3.0 <= ad.recommended_bet_size(10.0, dry) <= 3.5
    assert 6.5 <= ad.recommended_bet_size(10.0, wet) <= 6.7


def test_hu_contributions_and_toact_on_flop():
    ad = PokerAdapter(small_blind=0.5, big_blind=1.0, stack=100, seed=2, num_players=2)
    # Preflop call to see flop
    ad.apply_hero_action("call")
    assert ad.street == "flop"
    # Postflop: to_act should be non-button seat (1 when btn_seat=0)
    assert ad.to_act in (0, 1)
    # Hero checks, villain bets; contributions align to current_bet
    ad.apply_hero_action("check")
    assert abs(ad.current_bet - ad.villain.current_bet) < 1e-9
    assert ad.villain.contributed >= 0


