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

    def __init__(self, small_blind: float, big_blind: float, stack: float, seed: int):
        self.sb = small_blind
        self.bb = big_blind
        self.start_stack = stack
        self.rng = random.Random(seed)
        self.deck = generate_deck()
        self.rng.shuffle(self.deck)
        self.hero = PlayerState(stack=stack, position="btn")
        self.villain = PlayerState(stack=stack, position="bb")
        self.board: List[str] = []
        self.pot = 0.0
        self.history: List[Dict] = []
        self.street = "preflop"
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

    def legal_actions(self) -> Dict:
        # Minimal legal set for HU preflop facing BB: fold/call/raise
        min_raise = max(self.bb * 2.0, self.bb * 2.0)  # simple min-raise rule
        return {"toAct": "hero", "legal": ["fold", "call", "raise"], "min": round(min_raise, 2), "max": round(self.hero.stack, 2)}

    def get_state(self, session_id: str) -> Dict:
        spr = (self.hero.stack + self.villain.stack) / self.pot if self.pot else 0.0
        features = self.classify_board(self.board, spr)
        min_bet = self.recommended_bet_size(self.pot, features)
        return {
            "sessionId": session_id,
            "street": self.street,
            "hero": {"stack": round(self.hero.stack, 2), "cards": self.hero.cards, "position": self.hero.position},
            "villain": {"stack": round(self.villain.stack, 2), "position": self.villain.position},
            "board": list(self.board),
            "pot": round(self.pot, 2),
            "spr": round(spr, 2),
            "action": self.legal_actions() if self.street == "preflop" else {"toAct": "hero", "legal": ["check", "bet"], "min": round(min_bet, 2), "max": round(self.hero.stack, 2)},
            "history": list(self.history),
            "metadata": {"opponentType": "deterministic_mock", "boardFeatures": features},
        }

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
                self.pot += call_amt
                self.history.append({"actor": "hero", "move": "call", "size": round(call_amt, 2), "street": "preflop"})
                # Villain checks (completes round)
                self.history.append({"actor": "villain", "move": "check", "size": None, "street": "preflop"})
                self._advance_to_flop()
                return
            if action == "raise":
                bet = float(size or (self.bb * 2.5))
                self.hero.stack -= bet - self.sb  # additional chips beyond SB
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
                        self.pot += bet
                    self.history.append({"actor": "villain", "move": "bet", "size": round(bet, 2), "street": self.street})
                    # Deterministic hero response via pot odds
                    call_amt = bet
                    if self._hero_pot_odds_call(call_amt):
                        self.hero.stack -= call_amt
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
                self.pot += bet
                self.history.append({"actor": "hero", "move": "bet", "size": round(bet, 2), "street": self.street})
                # Villain simple pot-odds call/fold
                call_amt = bet
                call_ok = self._villain_pot_odds_call(call_amt)
                if call_ok:
                    self.villain.stack -= call_amt
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

    def _advance_to_flop(self) -> None:
        self.board += self._draw(3)
        self.street = "flop"

    def _advance_street(self) -> None:
        if self.street == "flop":
            self.board += self._draw(1)
            self.street = "turn"
        elif self.street == "turn":
            self.board += self._draw(1)
            self.street = "river"
        elif self.street == "river":
            self.street = "showdown"

    def _villain_preflop_response(self, hero_bet: float) -> None:
        to_call = hero_bet - self.bb
        call_ok = self._villain_pot_odds_call(to_call)
        if call_ok and to_call <= self.villain.stack:
            self.villain.stack -= to_call
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

    # --- Heuristics: board classification and bet sizing ---
    @staticmethod
    def _rank_to_val(card: str) -> int:
        return RANKS.index(card[0])

    @staticmethod
    def classify_board(board: List[str], spr: float) -> Dict:
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
        high_cards = sum(1 for r in ranks if r >= RANKS.index("Q"))
        feats["highCardHeavy"] = high_cards >= 2 or (ranks[-1] >= RANKS.index("A"))
        if feats["monotone"] or feats["connected"]:
            feats["type"] = "wet"
        if feats["connected"] and feats["highCardHeavy"]:
            feats["type"] = "dynamic"
        return feats

    @staticmethod
    def recommended_bet_size(pot: float, features: Dict) -> float:
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


