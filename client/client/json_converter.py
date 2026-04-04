"""
将 GameEngine 返回的 JSON 状态反序列化为 Environment 对象
字段名以 GameEngine.cs 中的 DTO 为准
"""
import numpy as np
from env import (
    Environment, Board, Cell, Piece, Player,
    SpellContext, Area
)
from utils import Point, SpellFactory


def env_from_state_json(state: dict, env: Environment) -> None:
    """将 JSON 状态更新到 env 对象（in-place）"""
    env.round_number = state.get("currentRound", 0)
    env.is_game_over = state.get("isGameOver", False)

    # --- 棋盘 ---
    board_data = state.get("board")
    if board_data:
        board = Board(if_log=0)
        board.width = board_data["width"]
        board.height = board_data["height"]
        board.boarder = board_data.get("boarder", board.height // 2)

        # grid 是 flat list，按 x 主序 (x 外层, y 内层) 排列
        grid_flat = board_data.get("grid", [])
        board.grid = np.empty((board.width, board.height), dtype=object)
        for i, cell_data in enumerate(grid_flat):
            x = i // board.height
            y = i % board.height
            board.grid[x][y] = Cell(
                state=cell_data.get("state", 1),
                player_id=cell_data.get("playerId", -1),
                piece_id=cell_data.get("pieceId", -1),
            )

        # height_map 同样是 flat list，x 主序
        hmap = board_data.get("height_map", [])
        board.height_map = np.zeros((board.width, board.height), dtype=int)
        for i, val in enumerate(hmap):
            x = i // board.height
            y = i % board.height
            board.height_map[x][y] = val

        env.board = board

    # --- 行动队列 ---
    pieces = []
    for p in state.get("actionQueue", []):
        piece = Piece()
        piece.id = p.get("id", 0)
        piece.team = p.get("team", 0)
        piece.health = p.get("health", 0)
        piece.max_health = p.get("max_health", 0)
        piece.physical_resist = p.get("physical_resist", 0)
        piece.magic_resist = p.get("magic_resist", 0)
        piece.physical_damage = p.get("physical_damage", 0)
        piece.magic_damage = p.get("magic_damage", 0)
        piece.action_points = p.get("action_points", 0)
        piece.max_action_points = p.get("max_action_points", 0)
        piece.spell_slots = p.get("spell_slots", 0)
        piece.max_spell_slots = p.get("max_spell_slots", 0)
        piece.movement = p.get("movement", 0.0)
        piece.max_movement = p.get("max_movement", 0.0)
        piece.strength = p.get("strength", 0)
        piece.dexterity = p.get("dexterity", 0)
        piece.intelligence = p.get("intelligence", 0)
        pos = p.get("position", {})
        piece.position = Point(pos.get("x", 0), pos.get("y", 0))
        piece.height = p.get("height", 0)
        piece.attack_range = p.get("attack_range", 0)
        piece.spell_range = p.get("spell_range", 0.0)
        piece.is_alive = p.get("is_alive", True)
        piece.is_in_turn = p.get("is_in_turn", False)
        piece.is_dying = p.get("is_dying", False)
        piece.death_round = p.get("deathRound", -1)
        piece.queue_index = p.get("queue_index", 0)
        # 根据 attack_range 推断武器类型（法杖 range=12, 弓 range=9, 长剑 range=5, 短剑 range=3）
        atk_range = piece.attack_range
        if piece.magic_damage > 0:
            piece.type = "Mage"
        elif atk_range >= 9:
            piece.type = "Archer"
        else:
            piece.type = "Warrior"
        pieces.append(piece)

    env.action_queue = np.array(pieces, dtype=object)

    # 当前行动棋子
    current_id = state.get("currentPieceID", -1)
    env.current_piece = next(
        (p for p in env.action_queue if p.id == current_id), None
    )

    # 玩家分组
    if env.player1 is None:
        env.player1 = Player()
        env.player1.id = 1
    if env.player2 is None:
        env.player2 = Player()
        env.player2.id = 2
    env.player1.pieces = np.array(
        [p for p in env.action_queue if p.team == 1], dtype=object
    )
    env.player2.pieces = np.array(
        [p for p in env.action_queue if p.team == 2], dtype=object
    )

    # 延迟法术
    delayed = []
    for ds in state.get("delayedSpells", []):
        sc = SpellContext()
        sc.spell_lifespan = ds.get("spellLifespan", 0)
        spell_id = ds.get("spellID", 0)
        sc.spell = SpellFactory.get_spell_by_id(spell_id)
        area = ds.get("targetArea")
        if area:
            sc.target_area = Area(
                area.get("x", 0), area.get("y", 0), area.get("radius", 0)
            )
        delayed.append(sc)
    env.delayed_spells = np.array(delayed, dtype=object)


def action_to_dict(action, player_id: int) -> dict:
    """将 ActionSet 序列化为 ActionSetDto JSON（与 GameEngine.ExecuteAction 约定一致）"""
    d = {
        "move": bool(getattr(action, "move", False)),
        "attack": bool(getattr(action, "attack", False)),
        "spell": bool(getattr(action, "spell", False)),
    }

    if d["move"] and getattr(action, "move_target", None):
        d["move_target"] = {
            "x": action.move_target.x,
            "y": action.move_target.y,
        }

    if d["attack"] and getattr(action, "attack_context", None):
        ctx = action.attack_context
        d["attack_context"] = {
            "target": ctx.target.id if ctx.target else -1,
        }

    if d["spell"] and getattr(action, "spell_context", None):
        ctx = action.spell_context
        sc = {
            "spellID": ctx.spell.id if ctx.spell else 0,
            "targetType": 0,  # Single=0 默认
            "target": ctx.target.id if ctx.target else -1,
            "spellLifespan": getattr(ctx, "spell_lifespan", 0),
        }
        if getattr(ctx, "target_area", None):
            sc["targetArea"] = {
                "x": ctx.target_area.x,
                "y": ctx.target_area.y,
                "radius": ctx.target_area.radius,
            }
        d["spell_context"] = sc

    return d
