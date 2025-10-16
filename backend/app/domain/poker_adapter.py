from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS = ["s", "h", "d", "c"]


def generate_deck() -> List[str]:
    return [r + s for r in RANKS for s in SUITS]


@dataclass
class PlayerState:
    stack: float
    position: str  # "btn" or "bb"
    cards: List[str] = field(default_factory=list)
    seat: int = 0
    folded: bool = False
    active: bool = True
    contributed: float = 0.0
    current_bet: float = 0.0
    is_ai: bool = False


@dataclass
class GameState:
    session_id: str
    street: str
    hero: PlayerState
    villain: PlayerState
    board: List[str]
    pot: float
    spr: float
    action: Dict
    history: List[Dict]
    metadata: Dict


class PokerAdapter:
    """
    Glue for PokerKit. For now, uses a deterministic internal engine while wiring.
    Replace dealing/validation with PokerKit calls as integration progresses.
    """

    def __init__(self, small_blind: float, big_blind: float, stack: float, seed: int, num_players: int = 2):
        self.sb = small_blind
        self.bb = big_blind
        self.start_stack = stack
        self.rng = random.Random(seed)
        self.deck = generate_deck()
        self.rng.shuffle(self.deck)
        # Multi-player scaffolding (back-compat: hero/villain remain)
        self.num_players = max(2, min(9, int(num_players)))
        self.players: List[PlayerState] = []
        for seat in range(self.num_players):
            # seat 0 = hero, seat 1 = AI (for now), others idle
            is_ai = (seat == 1)
            # default positions filled below for HU
            self.players.append(
                PlayerState(
                    stack=stack,
                    position="",
                    seat=seat,
                    folded=False if seat in (0, 1) else True,
                    active=True,
                    is_ai=is_ai,
                )
            )
        # Button seat and position assignment (HU default)
        self.btn_seat: int = 0
        self._assign_positions_hu()
        # Back-compat references
        self.hero = self.players[0]
        self.villain = self.players[1]
        self.board: List[str] = []
        self.pot = 0.0
        self.history: List[Dict] = []
        self.street = "preflop"
        # Turn/betting state scaffolding
        self.to_act: int = 0
        self.current_bet: float = 0.0
        self.last_aggressor: Optional[int] = None
        self.raises_this_street: int = 0
        self._post_blinds_and_deal()

    def _draw(self, n: int) -> List[str]:
        out = self.deck[:n]
        self.deck = self.deck[n:]
        return out

    def _post_blinds_and_deal(self) -> None:
        # Post blinds
        self.hero.stack -= self.sb
        self.villain.stack -= self.bb
        self.pot = self.sb + self.bb
        self.history.append({"actor": "hero", "move": "post_sb", "size": self.sb, "street": "preflop"})
        self.history.append({"actor": "villain", "move": "post_bb", "size": self.bb, "street": "preflop"})
        # Deal hole cards (hero first for determinism)
        self.hero.cards = self._draw(2)
        self.villain.cards = self._draw(2)
        # Initialize per-round contributions and current bet
        self.hero.contributed = self.sb
        self.villain.contributed = self.bb
        self.hero.current_bet = self.sb
        self.villain.current_bet = self.bb
        self.current_bet = self.bb
        # Initialize contributed/current_bet
        self.hero.contributed = self.sb
        self.villain.contributed = self.bb
        self.hero.current_bet = self.sb
        self.villain.current_bet = self.bb
        self.current_bet = self.bb
        # Set first to act preflop (HU: BTN acts first)
        self.to_act = self.btn_seat

    def reset_hand(self, seed: Optional[int] = None) -> None:
        """Start a new hand, preserving current stacks, repost blinds, and redeal."""
        if seed is not None:
            self.rng = random.Random(seed)
        self.deck = generate_deck()
        self.rng.shuffle(self.deck)
        self.board = []
        self.pot = 0.0
        self.history = []
        self.street = "preflop"
        # Rotate button seat and reassign positions (HU for now)
        self.btn_seat = (self.btn_seat + 1) % self.num_players
        self._assign_positions_hu()
        # Reset per-player round flags; keep seats >1 folded idle
        for i, p in enumerate(self.players):
            p.folded = False if i in (0, 1) else True
            p.active = True
            p.contributed = 0.0
            p.current_bet = 0.0
            p.cards = []
        # Reset betting state scaffolding
        self.current_bet = 0.0
        self.last_aggressor = None
        self.raises_this_street = 0
        self.to_act = 0
        self._post_blinds_and_deal()

    def legal_actions(self) -> Dict:
        # Minimal legal set for HU preflop facing BB: fold/call/raise
        min_raise = max(self.bb * 2.0, self.bb * 2.0)  # simple min-raise rule
        return {"toAct": "hero", "legal": ["fold", "call", "raise"], "min": round(min_raise, 2), "max": round(self.hero.stack, 2)}

    def get_state(self, session_id: str) -> Dict:
        spr = (self.hero.stack + self.villain.stack) / self.pot if self.pot else 0.0
        features = self.classify_board(self.board, spr)
        min_bet = self.recommended_bet_size(self.pot, features)
        state = {
            "sessionId": session_id,
            "street": self.street,
            "hero": {"stack": round(self.hero.stack, 2), "cards": self.hero.cards, "position": self.hero.position},
            "villain": {"stack": round(self.villain.stack, 2), "position": self.villain.position},
            "board": list(self.board),
            "pot": round(self.pot, 2),
            "spr": round(spr, 2),
            "action": (
                self.legal_actions()
                if self.street == "preflop"
                else (
                    {"toAct": None, "legal": [], "min": 0.0, "max": 0.0}
                    if self.street == "showdown"
                    else {"toAct": "hero", "legal": ["check", "bet"], "min": round(min_bet, 2), "max": round(self.hero.stack, 2)}
                )
            ),
            "history": list(self.history),
            "metadata": {
                "opponentType": "deterministic_mock",
                "boardFeatures": features,
                "players": [
                    {
                        "seat": p.seat,
                        "stack": round(p.stack, 2),
                        "position": p.position,
                        "folded": p.folded,
                        "active": p.active,
                        "contributed": round(p.contributed, 2),
                        "current_bet": round(p.current_bet, 2),
                        # Only reveal hero cards for now
                        "cards": p.cards if p is self.hero else [],
                        "is_ai": p.is_ai,
                    }
                    for p in self.players
                ],
                "toActSeat": self.to_act,
                "currentBet": round(self.current_bet, 2),
            },
        }
        return state

    def apply_hero_action(self, action: str, size: Optional[float] = None) -> None:
        if self.street == "preflop":
            if action == "fold":
                self.history.append({"actor": "hero", "move": "fold", "size": None, "street": "preflop"})
                self.street = "showdown"
                return
            if action == "call":
                call_amt = self.bb - self.sb
                call_amt = max(0.0, call_amt)
                self.hero.stack -= call_amt
                self.hero.contributed += call_amt
                self.hero.current_bet = self.bb
                self.current_bet = self.bb
                self.pot += call_amt
                self.history.append({"actor": "hero", "move": "call", "size": round(call_amt, 2), "street": "preflop"})
                # Villain checks (completes round)
                self.history.append({"actor": "villain", "move": "check", "size": None, "street": "preflop"})
                self._advance_to_flop()
                return
            if action == "raise":
                bet = float(size or (self.bb * 2.5))
                self.hero.stack -= bet - self.sb  # additional chips beyond SB
                self.hero.contributed += bet - self.sb
                self.hero.current_bet = bet
                self.current_bet = bet
                self.pot += bet - self.sb
                self.history.append({"actor": "hero", "move": "raise", "size": round(bet, 2), "street": "preflop"})
                # Villain responds deterministically via pot-odds
                self._villain_preflop_response(bet)
                return
        # Postflop handling: villain uses board-based sizing when hero checks
        if self.street in ("flop", "turn"):
            if action in ("check",):
                self.history.append({"actor": "hero", "move": action, "size": None, "street": self.street})
                features = self.classify_board(self.board, (self.hero.stack + self.villain.stack) / self.pot if self.pot else 0.0)
                v_action, v_size = self._villain_postflop_decide(features)
                if v_action == "bet":
                    bet = min(v_size, self.villain.stack)
                    if bet > 0:
                        self.villain.stack -= bet
                        self.villain.contributed += bet
                        self.villain.current_bet = bet
                        self.current_bet = bet
                        self.pot += bet
                    self.history.append({"actor": "villain", "move": "bet", "size": round(bet, 2), "street": self.street})
                    # Deterministic hero response via pot odds
                    call_amt = bet
                    if self._hero_pot_odds_call(call_amt):
                        self.hero.stack -= call_amt
                        self.hero.contributed += call_amt
                        self.hero.current_bet = bet
                        self.pot += call_amt
                        self.history.append({"actor": "hero", "move": "call", "size": round(call_amt, 2), "street": self.street})
                        self._advance_street()
                    else:
                        self.history.append({"actor": "hero", "move": "fold", "size": None, "street": self.street})
                        self.street = "showdown"
                    return
                else:
                    # Both check
                    self.history.append({"actor": "villain", "move": "check", "size": None, "street": self.street})
                    self._advance_street()
                    return
            if action == "bet":
                bet = float(size or round(self.pot * 0.33, 2))
                self.hero.stack -= bet
                self.hero.contributed += bet
                self.hero.current_bet = bet
                self.current_bet = bet
                self.pot += bet
                self.history.append({"actor": "hero", "move": "bet", "size": round(bet, 2), "street": self.street})
                # Villain simple pot-odds call/fold
                call_amt = bet
                call_ok = self._villain_pot_odds_call(call_amt)
                if call_ok:
                    self.villain.stack -= call_amt
                    self.villain.contributed += call_amt
                    self.villain.current_bet = bet
                    self.pot += call_amt
                    self.history.append({"actor": "villain", "move": "call", "size": round(call_amt, 2), "street": self.street})
                else:
                    self.history.append({"actor": "villain", "move": "fold", "size": None, "street": self.street})
                    self.street = "showdown"
                    return
                self._advance_street()
                return
        if self.street == "river":
            # Check down to showdown for simplicity
            self.history.append({"actor": "hero", "move": "check", "size": None, "street": "river"})
            self.history.append({"actor": "villain", "move": "check", "size": None, "street": "river"})
            self.street = "showdown"
            self._evaluate_showdown()

    def _advance_to_flop(self) -> None:
        self.board += self._draw(3)
        self.street = "flop"
        # Postflop first to act in HU is the non-button seat
        self.to_act = 1 - self.btn_seat

    def _advance_street(self) -> None:
        if self.street == "flop":
            self.board += self._draw(1)
            self.street = "turn"
            self.to_act = 1 - self.btn_seat
        elif self.street == "turn":
            self.board += self._draw(1)
            self.street = "river"
            self.to_act = 1 - self.btn_seat
        elif self.street == "river":
            self.street = "showdown"
            self._evaluate_showdown()

    def _villain_preflop_response(self, hero_bet: float) -> None:
        to_call = hero_bet - self.bb
        call_ok = self._villain_pot_odds_call(to_call)
        if call_ok and to_call <= self.villain.stack:
            self.villain.stack -= to_call
            self.villain.contributed += to_call
            self.villain.current_bet = hero_bet
            self.current_bet = hero_bet
            self.pot += to_call
            self.history.append({"actor": "villain", "move": "call", "size": round(to_call, 2), "street": "preflop"})
            self._advance_to_flop()
        else:
            self.history.append({"actor": "villain", "move": "fold", "size": None, "street": "preflop"})
            self.street = "showdown"

    def _villain_pot_odds_call(self, call_amount: float) -> bool:
        if call_amount <= 0:
            return True
        pot_odds = call_amount / (self.pot + call_amount)
        # Deterministic threshold
        return pot_odds <= 0.4

    # --- Multi-player scaffolding (future use) ---
    def next_to_act(self) -> int:
        """Return next active, non-folded seat index.

        Future: when wired fully, this will advance `self.to_act` and
        respect all-in closed players and betting round rules.
        """
        if self.num_players <= 1:
            return 0
        start = (self.to_act + 1) % self.num_players
        i = start
        while True:
            p = self.players[i]
            if p.active and not p.folded and not self._is_all_in(p):
                return i
            i = (i + 1) % self.num_players
            if i == start:
                # No other actionable player; keep current
                return self.to_act

    def active_players(self) -> List[int]:
        """Return seat indices for non-folded players.

        Future: include all-ins as active but closed to betting.
        """
        return [i for i, p in enumerate(self.players) if not p.folded]

    def is_betting_round_complete(self) -> bool:
        """Stubbed betting round completion check.

        Future: check contributions match current_bet or one player remains.
        """
        active = [i for i in self.active_players() if not self._is_all_in(self.players[i])]
        if len(active) <= 1:
            return True
        # All actionable players have matched current_bet
        for i in active:
            if abs(self.players[i].current_bet - self.current_bet) > 1e-9:
                return False
        return True

    def calculate_side_pots(self) -> List[Dict]:
        """Return side pots scaffolding.

        Future: compute from contributions; for now single main pot only.
        """
        return [{"amount": round(self.pot, 2), "eligible_players": self.active_players()}]

    @staticmethod
    def _is_all_in(p: PlayerState) -> bool:
        return p.stack <= 1e-9

    # --- Positions for HU (extend later for 3+) ---
    def _assign_positions_hu(self) -> None:
        """Assign HU positions based on current button seat.

        Hero is always seat 0; AI seat 1. BTN toggles between them across hands.
        """
        if self.btn_seat == 0:
            self.players[0].position = "btn"
            self.players[1].position = "bb"
        else:
            self.players[1].position = "btn"
            self.players[0].position = "bb"


    # --- Heuristics: board classification and bet sizing ---
    @staticmethod
    def _rank_to_val(card: str) -> int:
        # Map "2".."A" -> 2..14
        return RANKS.index(card[0]) + 2

    @staticmethod
    def classify_board(board: List[str], spr: float) -> Dict:
        """
        Classifies a poker board (flop) into basic strategic features for evaluating texture and playability.

        Args:
            board (List[str]): The community cards dealt so far (at least 3 for flop).
            spr (float): The stack-to-pot ratio.

        Feature explanations:
            monotone: All three flop cards are the same suit (flushes possible).
            connected: Flop cards are close together in rank (straight draws possible).
            paired: At least two flop cards have the same rank (set/boat potential).
            highCardHeavy: Flop contains two or more high cards (Q/J/K/A), meaning strong hands possible.
            type: 'dry' = little coordination/draws; 'wet' = connected or suited (draw-heavy); 
                  'dynamic' = both connected and high cards (action-heavy).
            sprBucket: 'shallow' (<3) = stacks smaller relative to pot; 'mid' (3-6); 'deep' (>6), affects strategy.
        """
        feats: Dict = {
            "monotone": False,
            "connected": False,
            "paired": False,
            "highCardHeavy": False,
            "type": "dry",
            "sprBucket": "shallow" if spr < 3 else ("mid" if spr <= 6 else "deep"),
        }
        if len(board) < 3:
            return feats
        suits = [c[1] for c in board[:3]]
        ranks = sorted([PokerAdapter._rank_to_val(c) for c in board[:3]])
        feats["monotone"] = len(set(suits)) == 1
        feats["paired"] = len(set(ranks)) < 3
        feats["connected"] = (ranks[-1] - ranks[0]) <= 4
        high_cards = sum(1 for r in ranks if r >= 12)
        feats["highCardHeavy"] = high_cards >= 2 or (ranks[-1] >= RANKS.index("A"))
        if feats["monotone"] or feats["connected"]:
            feats["type"] = "wet"
        if feats["connected"] and feats["highCardHeavy"]:
            feats["type"] = "dynamic"
        return feats

    @staticmethod
    def recommended_bet_size(pot: float, features: Dict) -> float:
        """
        Recommends a bet size based on pot size and board texture features.

        Args:
            pot (float): The current pot size.
            features (Dict): Board texture features from classify_board().

        Returns:
            float: Recommended bet size as a percentage of the pot.
        """
        if pot <= 0:
            return 0.0
        spr_bucket = features.get("sprBucket", "mid")
        board_type = features.get("type", "dry")
        base = 0.33
        if board_type in ("wet", "dynamic"):
            base = 0.66 if spr_bucket in ("mid", "deep") else 0.5
        elif features.get("paired"):
            base = 0.33
        elif features.get("highCardHeavy") and spr_bucket != "deep":
            base = 0.25
        return round(pot * base, 2)

    def _villain_postflop_decide(self, features: Dict) -> Tuple[str, float]:
        # Deterministic: bet on dry/high-card boards; check on very wet dynamic boards
        board_type = features.get("type")
        if board_type in ("dry",) or (features.get("highCardHeavy") and not features.get("monotone")):
            size = self.recommended_bet_size(self.pot, features)
            return "bet", size
        return "check", 0.0

    def _hero_pot_odds_call(self, call_amount: float) -> bool:
        if call_amount <= 0:
            return True
        pot_odds = call_amount / (self.pot + call_amount)
        return pot_odds <= 0.38

    # --- Showdown evaluation ---
    def _evaluate_showdown(self) -> None:
        """Compare 7-card hands, award pot, and append a result to history."""
        hero_best = self._best_five_from_seven(self.hero.cards + self.board)
        villain_best = self._best_five_from_seven(self.villain.cards + self.board)
        winner = "split"
        if hero_best[0] > villain_best[0]:
            winner = "hero"
        elif hero_best[0] < villain_best[0]:
            winner = "villain"
        else:
            # Same category: compare kickers tuple
            if hero_best[1] > villain_best[1]:
                winner = "hero"
            elif hero_best[1] < villain_best[1]:
                winner = "villain"

        pot_before = self.pot
        if winner == "hero":
            self.hero.stack += self.pot
            self.pot = 0.0
        elif winner == "villain":
            self.villain.stack += self.pot
            self.pot = 0.0
        else:
            # split pot heads-up
            self.hero.stack += self.pot / 2.0
            self.villain.stack += self.pot / 2.0
            self.pot = 0.0

        self.history.append({
            "actor": "result",
            "move": "showdown",
            "winner": winner,
            "heroBest": self._hand_desc(hero_best),
            "villainBest": self._hand_desc(villain_best),
            "pot": round(pot_before, 2),
        })

    # Hand evaluation helpers
    def _best_five_from_seven(self, cards: List[str]):
        # Returns (category_rank, tiebreaker_tuple, best5_cards_sorted_desc)
        # Category rank: 8=straight_flush,7=quads,6=full_house,5=flush,4=straight,3=trips,2=two_pair,1=pair,0=high
        ranks = [self._rank_to_val(c) for c in cards]
        suits = [c[1] for c in cards]

        # Counts
        rank_counts: Dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        # Flush
        suit_counts: Dict[str, int] = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        flush_suit = next((s for s, n in suit_counts.items() if n >= 5), None)
        flush_cards = [c for c in cards if c[1] == flush_suit] if flush_suit else []

        # Straight helpers
        def straight_high(rank_vals: List[int]) -> int:
            uniq = sorted(set(rank_vals))
            # Ace-low
            if 14 in uniq:
                uniq = [1] + uniq
            best = 0
            for i in range(len(uniq) - 4):
                window = uniq[i:i+5]
                if window[-1] - window[0] == 4 and len(set(window)) == 5:
                    best = max(best, window[-1])
            return best

        # Straight flush
        if flush_suit:
            sf_ranks = [self._rank_to_val(c) for c in flush_cards]
            sf_high = straight_high(sf_ranks)
            if sf_high:
                # Build kicker tuple: high of straight flush
                return (8, (sf_high,), sorted(flush_cards, key=lambda c: self._rank_to_val(c), reverse=True)[:5])

        # Quads / Trips / Pairs
        quads = [r for r, n in rank_counts.items() if n == 4]
        trips = sorted([r for r, n in rank_counts.items() if n == 3], reverse=True)
        pairs = sorted([r for r, n in rank_counts.items() if n == 2], reverse=True)
        singles = sorted([r for r, n in rank_counts.items() if n == 1], reverse=True)

        if quads:
            quad = max(quads)
            kickers = [r for r in sorted(rank_counts.keys(), reverse=True) if r != quad]
            return (7, (quad, kickers[0]), [])

        if trips and (pairs or len(trips) >= 2):
            # Full house: highest trips + highest pair (or next trips as pair)
            trip_rank = trips[0]
            pair_rank = pairs[0] if pairs else trips[1]
            return (6, (trip_rank, pair_rank), [])

        if flush_suit:
            top5 = sorted([self._rank_to_val(c) for c in flush_cards], reverse=True)[:5]
            return (5, tuple(top5), [])

        # Straight
        s_high = straight_high(ranks)
        if s_high:
            return (4, (s_high,), [])

        if trips:
            trip = trips[0]
            kickers = [r for r in singles if r != trip][:2]
            return (3, (trip, *kickers), [])

        if len(pairs) >= 2:
            high_pair, low_pair = pairs[0], pairs[1]
            kicker = max([r for r in singles if r not in (high_pair, low_pair)] or [0])
            return (2, (high_pair, low_pair, kicker), [])

        if pairs:
            pair = pairs[0]
            kickers = [r for r in singles if r != pair][:3]
            return (1, (pair, *kickers), [])

        # High card
        top5 = sorted(ranks, reverse=True)[:5]
        return (0, tuple(top5), [])

    @staticmethod
    def _hand_desc(hand_tuple) -> Dict:
        cat, tbs, _ = hand_tuple
        names = {
            8: "straight_flush",
            7: "four_of_a_kind",
            6: "full_house",
            5: "flush",
            4: "straight",
            3: "three_of_a_kind",
            2: "two_pair",
            1: "one_pair",
            0: "high_card",
        }
        return {"category": names.get(cat, "unknown"), "ranks": list(tbs)}


