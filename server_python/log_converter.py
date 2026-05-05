"""
与 C# LogConverter / FrontClasses 对齐的回放 JSON 构建器。
序列化字段名与 System.Text.Json 默认（属性名原样）一致。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from utils import SpellEffectType


def _vec3(x: int, height: int, z: int) -> Dict[str, int]:
    """对齐 C# Vector3Serializable：y 存 height+1。"""
    return {"x": int(x), "y": int(height) + 1, "z": int(z)}


class LogConverter:
    """对齐 Server.LogConverter。"""

    def __init__(self) -> None:
        self.gamedata: Optional[Dict[str, Any]] = None

    def init(self, init_queue: List[Any], board: Any) -> None:
        self.gamedata = {
            "mapdata": {
                "mapWidth": int(board.width),
                "rows": self._convert_height_map_to_rows(board),
            },
            "playerData": {"player1": "Red", "player2": "Blue"},
            "soldiersData": self._convert_piece_to_soldier(init_queue),
            "gameRounds": [],
        }

    def _convert_height_map_to_rows(self, board: Any) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for i in range(board.width):
            row_vals: List[int] = []
            for j in range(board.height):
                h = int(board.height_map[i, j]) if hasattr(board.height_map, "shape") else int(board.height_map[i][j])
                row_vals.append(h + 1)
            rows.append({"row": row_vals})
        return rows

    def _convert_piece_to_soldier(self, pieces: List[Any]) -> List[Dict[str, Any]]:
        soldiers: List[Dict[str, Any]] = []
        for piece in pieces:
            wt = int(getattr(piece, "weapon_type", 0) or 0)
            soldiers.append(
                {
                    "ID": int(piece.id),
                    "soldierType": wt,
                    "camp": "Red" if int(piece.team) == 1 else "Blue",
                    "position": _vec3(
                        int(piece.position.x),
                        int(piece.height),
                        int(piece.position.y),
                    ),
                    "stats": {
                        "health": int(piece.health),
                        "strength": int(piece.strength),
                        "intelligence": int(piece.intelligence),
                    },
                }
            )
        return soldiers

    def add_round(self, round_cnt: int, pieces: List[Any]) -> None:
        assert self.gamedata is not None
        self.gamedata["gameRounds"].append(
            {
                "roundNumber": int(round_cnt),
                "actions": [],
                "stats": None,
                "score": None,
                "end": None,
            }
        )

    def finish_round(
        self,
        round_cnt: int,
        pieces: List[Any],
        red_left: int,
        blue_left: int,
        is_game_over: bool,
        piece_cnt: int = 3,
    ) -> None:
        assert self.gamedata is not None
        cur = self.gamedata["gameRounds"][-1]
        temp_stat: List[Dict[str, Any]] = []
        for piece in pieces:
            temp_stat.append(
                {
                    "soldierId": int(piece.id),
                    "position": _vec3(
                        int(piece.position.x),
                        int(piece.height),
                        int(piece.position.y),
                    ),
                    "survived": "true",
                    "Stats": {
                        "health": int(piece.health),
                        "strength": int(piece.strength),
                        "intelligence": int(piece.intelligence),
                    },
                }
            )
        cur["stats"] = temp_stat
        cur["score"] = {
            "redScore": int(piece_cnt - blue_left),
            "blueScore": int(piece_cnt - red_left),
        }
        cur["end"] = "true" if is_game_over else "false"

    def add_move(self, p: Any, path: List[Any], board: Any) -> None:
        assert self.gamedata is not None
        path_vec: List[Dict[str, int]] = []
        for pt in path or []:
            hx = int(pt.x)
            hy = int(pt.y)
            hmap = int(board.height_map[hx, hy]) if hasattr(board.height_map, "shape") else int(board.height_map[hx][hy])
            path_vec.append(_vec3(hx, hmap, hy))
        act: Dict[str, Any] = {
            "actionType": "Movement",
            "soldierId": int(p.id),
            "path": path_vec,
            "remainingMovement": int(p.movement),
        }
        self.gamedata["gameRounds"][-1]["actions"].append(act)

    def add_attack(self, context: Any) -> None:
        assert self.gamedata is not None
        tgt = context.target
        dmg = int(getattr(context, "damage_dealt", 0) or 0)
        temp: Dict[str, Any] = {
            "actionType": "Attack",
            "soldierId": int(context.attacker.id),
            "targetId": int(tgt.id) if tgt is not None else -1,
            "damageDealt": [{"targetId": int(tgt.id), "damage": dmg}] if tgt is not None else [],
        }
        self.gamedata["gameRounds"][-1]["actions"].append(temp)

    def add_spell(self, context: Any, board: Any) -> None:
        assert self.gamedata is not None
        spell = context.spell
        if spell is None:
            return
        et = spell.effect_type
        if et == SpellEffectType.DAMAGE:
            spell_type = 1
        elif et == SpellEffectType.HEAL:
            spell_type = -1
        else:
            spell_type = 0
        base = int(spell.base_value)

        temp: Dict[str, Any] = {
            "actionType": "Ability",
            "soldierId": int(context.caster.id),
            "damageDealt": [],
        }
        tgt = context.target
        if tgt is not None:
            temp["targetPosition"] = _vec3(
                int(tgt.position.x),
                int(tgt.height),
                int(tgt.position.y),
            )
            temp["damageDealt"].append(
                {"targetId": int(tgt.id), "damage": base * spell_type}
            )
        else:
            ta = context.target_area
            if ta is None:
                return
            hx = int(board.height_map[ta.x, ta.y]) if hasattr(board.height_map, "shape") else int(board.height_map[ta.x][ta.y])
            temp["targetPosition"] = _vec3(int(ta.x), hx, int(ta.y))
            hit_list = getattr(context, "hit_pieces", None) or getattr(context, "hitPiecies", None) or []
            for piece in hit_list:
                temp["damageDealt"].append(
                    {"targetId": int(piece.id), "damage": base * spell_type}
                )
        self.gamedata["gameRounds"][-1]["actions"].append(temp)

    def add_death(self, p: Any) -> None:
        assert self.gamedata is not None
        self.gamedata["gameRounds"][-1]["actions"].append(
            {"actionType": "Death", "soldierId": int(p.id)}
        )

    def to_json(self) -> str:
        if self.gamedata is None:
            return "{}"
        return json.dumps(self.gamedata, ensure_ascii=False, indent=2)
