import argparse
import os
import sys
from typing import Any

# 确保可直接从 dev_test 目录运行。
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from env import ActionSet, PieceArg, Point
from logic.controller import Controller


def _auto_init_handler(init_message: Any):
    """自动初始化：生成合法棋子参数，避免调试时手工输入。"""
    piece_args = []

    width = init_message.board.width
    height = init_message.board.height
    boarder = init_message.board.boarder

    candidates = []
    for y in range(height):
        if init_message.id == 1 and y >= boarder:
            continue
        if init_message.id == 2 and y <= boarder:
            continue
        for x in range(width):
            if init_message.board.grid[x][y].state == 1:
                candidates.append((x, y))

    for i in range(init_message.piece_cnt):
        x, y = candidates[i]
        arg = PieceArg()
        arg.strength = 10
        arg.dexterity = 10
        arg.intelligence = 10
        arg.equip = Point(1, 1)
        arg.pos = Point(x, y)
        piece_args.append(arg)

    return piece_args


def _noop_action_handler(_env: Any) -> ActionSet:
    """空行动：用于验证回合推进，不依赖人工输入。"""
    action = ActionSet()
    action.move = False
    action.attack = False
    action.spell = False
    return action


def run_debug(steps: int) -> int:
    controller = Controller(mode="manual")
    try:
        controller.select_mode("manual")
        game_data = controller.data_provider.get_game_data(prefer_runtime=True)
        controller.runtime_source = str(game_data.get("source", "runtime_env"))
        env = controller.create_environment(
            local_mode=bool(game_data.get("local_mode", True)),
            if_log=int(game_data.get("if_log", 1)),
        )
        env.input_manager.set_function_input_method(1, _auto_init_handler, _noop_action_handler)
        env.input_manager.set_function_input_method(2, _auto_init_handler, _noop_action_handler)
        env.initialize_environment(board_file=game_data.get("board_file"))
        controller.environment = env
        controller.game_data = game_data

        print("[DEBUG] runtime environment initialized:")
        print(
            {
                "source": controller.runtime_source,
                "board_file": game_data.get("board_file"),
                "board": {"width": env.board.width, "height": env.board.height},
            }
        )

        for i in range(steps):
            if env.is_game_over:
                print("[DEBUG] game over detected, stop loop")
                break

            controller.run_round()
            print(
                f"[DEBUG][step={i + 1}] "
                f"round={env.round_number} "
                f"current_piece={getattr(env.current_piece, 'id', -1)} "
                f"alive_queue={len([p for p in env.action_queue if p.is_alive])} "
                f"game_over={env.is_game_over}"
            )

        return 0
    except Exception as e:
        print(f"[DEBUG] runtime environment failed: {e}")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="dev_test 本地玩法环境调试工具")
    parser.add_argument("--steps", default=5, type=int, help="抓取状态步数")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run_debug(args.steps))
