"""选手端 AI / 搜索用辅助函数（从 Environment 抽离，供策略与搜索使用）。"""
from __future__ import annotations

import copy
from typing import List, Optional

import numpy as np

from env import Board, Environment, Piece
from utils import ActionSet, Point


def get_state_score(env: Environment) -> float:
    if env.current_piece is None:
        return 0.0

    current_team = env.current_piece.team
    score = 0.0

    for piece in env.action_queue:
        if not piece.is_alive:
            continue

        piece_score = 0.0
        piece_score += piece.health / piece.max_health * 10
        piece_score += piece.height * 0.5
        piece_score += piece.action_points * 2
        piece_score += piece.spell_slots * 1.5
        piece_score += (piece.physical_damage + piece.magic_damage) * 0.3
        piece_score += (piece.physical_resist + piece.magic_resist) * 0.2

        if piece.team == current_team:
            score += piece_score
        else:
            score -= piece_score

    return score


def get_legal_moves(env: Environment, piece: Optional[Piece] = None) -> List[Point]:
    if piece is None:
        piece = env.current_piece

    if piece is None or not piece.is_alive:
        return []

    legal_moves: List[Point] = []
    mask = env.board.valid_target(piece, piece.movement)

    for x in range(env.board.width):
        for y in range(env.board.height):
            if mask[x][y] != -1:
                legal_moves.append(Point(x, y))

    return legal_moves


def get_attackable_targets(env: Environment, piece: Optional[Piece] = None) -> List[Piece]:
    if piece is None:
        piece = env.current_piece

    if piece is None or not piece.is_alive:
        return []

    targets: List[Piece] = []
    for target in env.action_queue:
        if (
            target.is_alive
            and target.team != piece.team
            and env.is_in_attack_range(piece, target)
        ):
            targets.append(target)

    return targets


def simulate_move(env: Environment, piece: Piece, target: Point) -> bool:
    if not piece.is_alive:
        return False

    mask = env.board.valid_target(piece, piece.movement)
    if mask[target.x][target.y] == -1:
        return False

    return True


def simulate_attack(env: Environment, attacker: Piece, target: Piece) -> float:
    if not attacker.is_alive or not target.is_alive:
        return 0.0

    if not env.is_in_attack_range(attacker, target):
        return 0.0

    attack_throw = 10.5 + env.step_modified_func(attacker.strength)
    defense_value = target.physical_resist + env.step_modified_func(target.dexterity)

    if attack_throw <= defense_value:
        return 0.0

    return max(0, attacker.physical_damage - target.physical_resist)


def step_with_action(env: Environment, action: ActionSet) -> None:
    env.round_number += 1

    for piece in env.action_queue:
        if piece.is_alive:
            piece.set_action_points(piece.max_action_points)

    env.current_piece = env.action_queue[0]

    for i in range(len(env.delayed_spells) - 1, -1, -1):
        spell = env.delayed_spells[i]
        spell.spell_lifespan -= 1

        if spell.spell_lifespan == 0:
            env.execute_spell(spell)
            env.delayed_spells = np.delete(env.delayed_spells, i)
        elif spell.spell_lifespan < 0:
            env.delayed_spells = np.delete(env.delayed_spells, i)

    env.action_queue = np.append(env.action_queue[1:], [env.current_piece])

    if action:
        env.execute_player_action(action)

    env.is_game_over = not any(p.is_alive for p in env.player1.pieces) or not any(
        p.is_alive for p in env.player2.pieces
    )

    env.last_round_dead_pieces = np.array(env.new_dead_this_round, dtype=object)
    env.new_dead_this_round = np.array([], dtype=object)


def fork_environment(env: Environment) -> Environment:
    new_env = Environment(local_mode=(env.mode == 0), if_log=0)

    new_env.mode = env.mode
    new_env.round_number = env.round_number
    new_env.is_game_over = env.is_game_over

    if env.board:
        new_env.board = Board(if_log=new_env.if_log)
        new_env.board.width = env.board.width
        new_env.board.height = env.board.height
        new_env.board.boarder = env.board.boarder
        new_env.board.grid = np.array(
            [[copy.deepcopy(cell) for cell in row] for row in env.board.grid],
            dtype=object,
        )
        new_env.board.height_map = np.copy(env.board.height_map)

    new_env.action_queue = np.array(
        [copy.deepcopy(piece) for piece in env.action_queue], dtype=object
    )
    new_env.delayed_spells = np.array(
        [copy.deepcopy(spell) for spell in env.delayed_spells], dtype=object
    )
    new_env.new_dead_this_round = np.array(
        [copy.deepcopy(piece) for piece in env.new_dead_this_round], dtype=object
    )
    new_env.last_round_dead_pieces = np.array(
        [copy.deepcopy(piece) for piece in env.last_round_dead_pieces], dtype=object
    )

    if env.current_piece:
        for piece in new_env.action_queue:
            if piece.id == env.current_piece.id:
                new_env.current_piece = piece
                break

    new_env.player1 = copy.deepcopy(env.player1)
    new_env.player2 = copy.deepcopy(env.player2)

    new_env.player1.pieces = np.array(
        [piece for piece in new_env.action_queue if piece.team == 1], dtype=object
    )
    new_env.player2.pieces = np.array(
        [piece for piece in new_env.action_queue if piece.team == 2], dtype=object
    )

    return new_env
