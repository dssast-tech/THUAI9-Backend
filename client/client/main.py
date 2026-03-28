"""
THUAI9 Python Client - Saiblo stdin/stdout 版本
替代原 grpc_client.py
"""
import sys
import json
import argparse

from saiblo_client import SaibloClient
from json_converter import env_from_state_json, action_to_dict
from strategy_factory import StrategyFactory
from env import Environment
from utils import ActionSet


ERROR_MAP = ["RE", "TLE", "OLE"]


def parse_args():
    parser = argparse.ArgumentParser(description="THUAI9 Saiblo Client")
    parser.add_argument(
        "--strategy",
        choices=["aggressive", "defensive", "mcts"],
        default="mcts",
        help="AI策略 (默认: mcts)",
    )
    parser.add_argument(
        "--mcts-simulations", type=int, default=25, help="MCTS模拟次数 (默认: 25)"
    )
    return parser.parse_args()


def run():
    args = parse_args()

    # 选择策略
    if args.strategy == "aggressive":
        action_strategy = StrategyFactory.get_aggressive_action_strategy()
    elif args.strategy == "defensive":
        action_strategy = StrategyFactory.get_defensive_action_strategy()
    else:
        action_strategy = StrategyFactory.get_mcts_action_strategy(args.mcts_simulations)

    env = Environment(local_mode=False, if_log=0)
    player_id = -1  # 由第一条回合消息确定

    print("[INFO] 等待初始化消息...", file=sys.stderr)

    while True:
        msg = SaibloClient.read_message()
        if msg is None:
            print("[INFO] 连接关闭", file=sys.stderr)
            break

        state = msg.get("state")

        # --- 游戏结束 ---
        if state == -1:
            print("[INFO] 游戏结束", file=sys.stderr)
            break

        # --- 异常消息 (player == -1) ---
        if msg.get("player") == -1:
            try:
                err = json.loads(msg.get("content", "{}"))
            except Exception:
                err = {}
            etype = err.get("error", 0)
            print(
                f"[ERROR] AI异常: {ERROR_MAP[etype] if etype < len(ERROR_MAP) else 'UNKNOWN'}",
                file=sys.stderr,
            )
            break

        # --- 正常回合消息 ---
        # 第一条回合消息：从 player 列表和 content 推断自己的 player_id
        players = msg.get("player", [])
        content_list = msg.get("content", [])
        listen = msg.get("listen", [])

        # 确定 player_id（首次）
        if player_id == -1 and players:
            # Saiblo 会把我们的 ID 放在 player 列表里；
            # 我们只有一个进程，取第一个即可（实际由 Saiblo 分配）
            player_id = players[0]
            print(f"[INFO] 我的 player_id = {player_id}", file=sys.stderr)

        # 只在轮到我们时行动
        if player_id not in listen:
            continue

        # 取对应的状态 JSON
        idx = players.index(player_id) if player_id in players else 0
        if idx >= len(content_list):
            continue

        state_json_str = content_list[idx]
        try:
            state_data = json.loads(state_json_str)
        except Exception as e:
            print(f"[ERROR] 解析状态 JSON 失败: {e}", file=sys.stderr)
            continue

        # 更新环境
        env_from_state_json(state_data, env)

        if env.current_piece is None:
            print("[WARN] current_piece 为空，跳过", file=sys.stderr)
            continue

        # 运行策略
        try:
            action = action_strategy(env)
        except Exception as e:
            print(f"[ERROR] 策略执行失败: {e}", file=sys.stderr)
            action = ActionSet()

        # 序列化并发送
        # C# 侧 player ID 是 1-based，Saiblo 侧是 0-based
        csharp_pid = player_id + 1
        action_dict = action_to_dict(action, csharp_pid)
        response = {
            "player": player_id,
            "content": json.dumps(action_dict, ensure_ascii=False),
        }
        SaibloClient.write_message(response)
        print(
            f"[INFO] 回合 {state_data.get('currentRound', '?')}: 已发送行动",
            file=sys.stderr,
        )


if __name__ == "__main__":
    run()
