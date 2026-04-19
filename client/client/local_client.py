#!/usr/bin/env python3
"""
本地 Environment 客户端（不连 gRPC / Saiblo）
支持 local：双方控制台输入；function：双方均为函数式（策略）输入。
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from env import Environment
from strategy_factory import StrategyFactory


def parse_args():
    parser = argparse.ArgumentParser(description="THUAI9 本地 Environment 客户端")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["local", "function"],
        default="local",
        help="local: 双方控制台输入; function: 双方均为函数式 AI 输入",
    )
    parser.add_argument(
        "--board",
        type=str,
        default=None,
        help="棋盘文件路径（默认 ./BoardCase/case1.txt）",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["aggressive", "defensive", "mcts"],
        default="aggressive",
        help="function 模式下的布阵与行动策略",
    )
    parser.add_argument(
        "--mcts-simulations",
        type=int,
        default=25,
        help="strategy=mcts 时 MCTS 模拟次数",
    )
    return parser.parse_args()


def _strategies_for(args):
    if args.strategy == "aggressive":
        return (
            StrategyFactory.get_aggressive_init_strategy(),
            StrategyFactory.get_aggressive_action_strategy(),
        )
    if args.strategy == "defensive":
        return (
            StrategyFactory.get_defensive_init_strategy(),
            StrategyFactory.get_defensive_action_strategy(),
        )
    init_s = StrategyFactory.get_defensive_init_strategy()
    action_s = StrategyFactory.get_mcts_action_strategy(args.mcts_simulations)
    return init_s, action_s


def main():
    args = parse_args()
    env = Environment(local_mode=True)
    board_file = args.board if args.board is not None else "./BoardCase/case1.txt"

    if args.mode == "function":
        init_strategy, action_strategy = _strategies_for(args)
        env.input_manager.set_function_input_method(1, init_strategy, action_strategy)
        env.input_manager.set_function_input_method(2, init_strategy, action_strategy)
        print("=== 函数式双 AI 本地模式 ===")
        print(f"策略: {args.strategy}, 棋盘: {board_file}")
    else:
        print("=== 本地控制台双人对战模式 ===")
        print(f"棋盘: {board_file}")

    try:
        env.run(board_file)
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
    except Exception as e:
        print(f"游戏运行出错: {e}")


if __name__ == "__main__":
    main()
