"""
纯 Python 游戏引擎封装，接口对齐原 C# GameEngine + game-host GameEngineWrapper。
逻辑委托给 env.Environment（复用现有战斗/棋盘实现）。
"""
import json
import os
import numpy as np
from typing import Any, Dict, List, Optional

from utils import (
    ActionSet,
    InitPolicyMessage,
    PieceArg,
    Point,
    SpellFactory,
    TargetType,
    Area,
)

from env import Environment, SpellContext, AttackContext


def _default_board_path() -> str:
    return os.path.join(os.path.dirname(__file__), "BoardCase", "case1.txt")


def _piece_args_from_list(pieces: List[Dict[str, Any]]) -> List[PieceArg]:
    out: List[PieceArg] = []
    for item in pieces:
        pa = PieceArg()
        pa.strength = int(item["strength"])
        pa.intelligence = int(item["intelligence"])
        pa.dexterity = int(item["dexterity"])
        eq = item["equip"]
        pa.equip = Point(int(eq["x"]), int(eq["y"]))
        pos = item["pos"]
        pa.pos = Point(int(pos["x"]), int(pos["y"]))
        out.append(pa)
    return out


def _action_set_from_json(action_json: str, env: Environment) -> Optional[ActionSet]:
    d = json.loads(action_json) if isinstance(action_json, str) else action_json
    act = ActionSet()
    act.move = bool(d.get("move"))
    mt = d.get("move_target")
    if mt:
        act.move_target = Point(int(mt["x"]), int(mt["y"]))
    act.attack = bool(d.get("attack"))
    if act.attack and d.get("attack_context"):
        tid = int(d["attack_context"]["target"])
        ctx = AttackContext()
        ctx.attacker = env.current_piece
        ctx.target = next((p for p in env.action_queue if p.id == tid), None)
        act.attack_context = ctx
    act.spell = bool(d.get("spell"))
    if act.spell and d.get("spell_context"):
        st = d["spell_context"]
        spell = SpellFactory.get_spell_by_id(int(st.get("spellID", 0)))
        if spell is None:
            return None
        sc = SpellContext()
        sc.caster = env.current_piece
        sc.spell = spell
        tt_idx = int(st.get("targetType", 0))
        members = list(TargetType)
        sc.target_type = members[tt_idx] if 0 <= tt_idx < len(members) else TargetType.SINGLE
        tid = st.get("target")
        if tid is not None:
            tid = int(tid)
            sc.target = next((p for p in env.action_queue if p.id == tid), None)
        ta = st.get("targetArea")
        if ta:
            sc.target_area = Area(int(ta["x"]), int(ta["y"]), int(ta.get("radius", 0)))
        sc.spell_lifespan = int(st.get("spellLifespan", spell.base_lifespan))
        sc.is_delay_spell = bool(spell.is_delay_spell)
        sc.spell_cost = int(spell.spell_cost)
        act.spell_context = sc
    return act


def _serialize_board(board) -> Dict[str, Any]:
    dto: Dict[str, Any] = {
        "width": board.width,
        "height": board.height,
        "boarder": board.boarder,
        "grid": [],
        "height_map": [],
    }
    for x in range(board.width):
        for y in range(board.height):
            cell = board.grid[x][y]
            dto["grid"].append(
                {
                    "state": int(cell.state),
                    "playerId": int(cell.player_id),
                    "pieceId": int(cell.piece_id),
                }
            )
            dto["height_map"].append(int(board.height_map[x, y]))
    return dto


def _serialize_piece(p: Any, env: Environment) -> Dict[str, Any]:
    cur = env.current_piece
    return {
        "health": int(p.health),
        "max_health": int(p.max_health),
        "physical_resist": int(p.physical_resist),
        "magic_resist": int(p.magic_resist),
        "physical_damage": int(p.physical_damage),
        "magic_damage": int(p.magic_damage),
        "action_points": int(p.action_points),
        "max_action_points": int(p.max_action_points),
        "spell_slots": int(p.spell_slots),
        "max_spell_slots": int(p.max_spell_slots),
        "movement": float(p.movement),
        "max_movement": float(p.max_movement),
        "id": int(p.id),
        "strength": int(p.strength),
        "dexterity": int(p.dexterity),
        "intelligence": int(p.intelligence),
        "position": {"x": int(p.position.x), "y": int(p.position.y)},
        "height": int(p.height),
        "attack_range": int(p.attack_range),
        "spell_list": [int(x) for x in (getattr(p, "spell_list", []) or [])],
        "weapon_type": int(getattr(p, "weapon_type", 0)),
        "deathRound": int(getattr(p, "death_round", -1)),
        "team": int(p.team),
        "queue_index": int(p.queue_index),
        "is_alive": bool(p.is_alive),
        "is_in_turn": cur is not None and int(p.id) == int(cur.id),
        "is_dying": bool(p.is_dying),
        "spell_range": float(p.spell_range),
    }


def _serialize_spell_context(ctx: Any) -> Dict[str, Any]:
    ta = getattr(ctx, "target_area", None)
    tt = getattr(ctx, "target_type", None)
    members = list(TargetType)
    tt_idx = members.index(tt) if tt in members else 0
    return {
        "caster": ctx.caster.id if ctx.caster else -1,
        "spellID": ctx.spell.id if ctx.spell else 0,
        "targetType": tt_idx,
        "target": ctx.target.id if ctx.target else -1,
        "targetArea": None
        if ta is None
        else {"x": ta.x, "y": ta.y, "radius": ta.radius},
        "spellLifespan": int(getattr(ctx, "spell_lifespan", 0)),
    }


def _as_list(seq) -> List[Any]:
    if seq is None:
        return []
    if isinstance(seq, np.ndarray):
        return list(seq)
    return list(seq)


def _serialize_state(env: Environment) -> str:
    dto: Dict[str, Any] = {
        "currentRound": env.round_number,
        "currentPlayerId": env.current_piece.team if env.current_piece else 0,
        "currentPieceID": env.current_piece.id if env.current_piece else -1,
        "isGameOver": env.is_game_over,
        "board": _serialize_board(env.board),
        "actionQueue": [_serialize_piece(p, env) for p in _as_list(env.action_queue)],
        "delayedSpells": [_serialize_spell_context(s) for s in _as_list(env.delayed_spells)],
    }
    return json.dumps(dto, ensure_ascii=False)


class PythonGameEngine:
    """与 game-host.GameEngineWrapper 同构的对外 API。"""

    def __init__(self, use_mock: bool = False, if_log: int = 0):
        self._env = Environment(local_mode=True, if_log=if_log)
        self.use_mock = use_mock

    @property
    def env(self) -> Environment:
        return self._env

    def initialize(self, config: Dict[str, Any]) -> None:
        del config  # 与 C# 一致：当前版本不使用 config
        self._env.init_board_only(_default_board_path())

    def set_player_pieces(self, player_id: int, pieces: List[Dict[str, Any]]) -> bool:
        try:
            pid = player_id
            if pid in (0, 1):
                pid += 1
            policy = InitPolicyMessage()
            policy.piece_args = _piece_args_from_list(pieces)
            self._env.apply_init_policy(pid, policy)
            if (
                len(self._env.player1.pieces) > 0
                and len(self._env.player2.pieces) > 0
                and not self._env.is_battle_initialized
            ):
                self._env.setup_battle_host()
            return True
        except Exception:
            return False

    def next_turn(self) -> None:
        self._env.begin_turn_host()

    def get_state_json(self) -> str:
        return _serialize_state(self._env)

    def execute_action(self, player_id: int, action_json: str) -> bool:
        try:
            pid = player_id
            if pid in (0, 1):
                pid += 1
            if not self._env.is_battle_initialized or self._env.is_game_over:
                return False
            if self._env.current_piece is None or pid != self._env.current_piece.team:
                return False
            act = _action_set_from_json(action_json, self._env)
            if act is None:
                return False
            self._env.apply_action_host(act)
            self._env.end_turn_host()
            return True
        except Exception:
            return False

    def is_game_over(self) -> bool:
        return bool(self._env.is_game_over)

    def get_winner(self) -> int:
        p1_alive = any(p.is_alive for p in self._env.player1.pieces)
        p2_alive = any(p.is_alive for p in self._env.player2.pieces)
        if p1_alive and not p2_alive:
            return self._env.player1.id
        if not p1_alive and p2_alive:
            return self._env.player2.id
        return -1

    def get_replay_json(self) -> str:
        ld = getattr(self._env, "logdata", None)
        if ld is not None:
            return ld.to_json()
        return "{}"


# 与 game-host 中名称一致，便于 main 直接替换 import
GameEngineWrapper = PythonGameEngine
