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
from env import Environment, InitGameMessage, Player
from utils import ActionSet


ERROR_MAP = ["RE", "TLE", "OLE"]


def _serialize_piece_args(piece_args):
    """与 server_python game_engine._piece_args_from_list 输入格式一致。"""
    out = []
    for pa in piece_args:
        out.append(
            {
                "strength": int(pa.strength),
                "intelligence": int(pa.intelligence),
                "dexterity": int(pa.dexterity),
                "equip": {"x": int(pa.equip.x), "y": int(pa.equip.y)},
                "pos": {"x": int(pa.pos.x), "y": int(pa.pos.y)},
            }
        )
    return out


def parse_args():
    parser = argparse.ArgumentParser(description="THUAI9 Saiblo Client")
    parser.add_argument(
        "--strategy",
        choices=["aggressive", "defensive", "mcts"],
        default="aggressive",
        help="AI策略 (默认: aggressive)",
    )
    parser.add_argument(
        "--mcts-simulations", type=int, default=25, help="MCTS模拟次数 (默认: 25)"
    )
    parser.add_argument(
        "--player-id",
        type=int,
        default=-1,
        help="Saiblo 座位 0/1；仅本地调试强制校验，线上以首包为准",
    )
    return parser.parse_args()


def run():
    args = parse_args()

    if args.strategy == "aggressive":
        action_strategy = StrategyFactory.get_aggressive_action_strategy()
        init_strategy = StrategyFactory.get_aggressive_init_strategy()
    elif args.strategy == "defensive":
        action_strategy = StrategyFactory.get_defensive_action_strategy()
        init_strategy = StrategyFactory.get_defensive_init_strategy()
    else:
        action_strategy = StrategyFactory.get_mcts_action_strategy(args.mcts_simulations)
        init_strategy = StrategyFactory.get_defensive_init_strategy()

    env = Environment(local_mode=False, if_log=0)
    env.init_board_only()
    player_id = -1
    handshake_done = False

    print("[INFO] 等待 judger 下发消息...", file=sys.stderr)

    while True:
        raw = SaibloClient.read_payload()
        if raw is None:
            print("[INFO] 连接关闭", file=sys.stderr)
            break

        text = raw.strip()
        if not text:
            continue

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[ERROR] 无法解析消息 JSON: {e}", file=sys.stderr)
            continue

        if isinstance(data, dict) and data.get("state") == -1:
            print("[INFO] 游戏结束", file=sys.stderr)
            break

        if isinstance(data, dict) and data.get("player") == -1:
            try:
                err = json.loads(data.get("content", "{}"))
            except Exception:
                err = {}
            etype = err.get("error", 0)
            print(
                f"[ERROR] AI异常: {ERROR_MAP[etype] if etype < len(ERROR_MAP) else 'UNKNOWN'}",
                file=sys.stderr,
            )
            break

        if not handshake_done:
            if isinstance(data, int) and data in (0, 1):
                if args.player_id in (0, 1) and int(data) != args.player_id:
                    print(
                        f"[WARN] 首回合座位 {data} 与 --player-id {args.player_id} 不一致，以服务端为准",
                        file=sys.stderr,
                    )
                player_id = int(data)
            else:
                print("[ERROR] 首回合未收到座位号（期望 JSON 数字 0 或 1）", file=sys.stderr)
                break

            handshake_done = True
            init_msg = InitGameMessage()
            init_msg.piece_cnt = Player.PIECE_CNT
            init_msg.id = player_id + 1
            init_msg.board = env.board
            piece_args = init_strategy(init_msg)
            init_body = {
                "phase": "init",
                "pieces": _serialize_piece_args(piece_args),
            }
            SaibloClient.write_message(
                {
                    "player": player_id,
                    "content": json.dumps(init_body, ensure_ascii=False),
                }
            )
            print(f"[INFO] 首回合握手完成，player_id={player_id}，已上报布阵", file=sys.stderr)
            continue

        if player_id not in (0, 1):
            print("[ERROR] 未完成握手却收到局面数据", file=sys.stderr)
            break

        if not isinstance(data, dict):
            print(f"[WARN] 非局面对象，已忽略: {type(data).__name__}", file=sys.stderr)
            continue

        if "currentRound" not in data and "board" not in data:
            print("[WARN] 收到无法识别的 JSON 对象，已忽略", file=sys.stderr)
            continue

        state_data = data
        cur_team = int(state_data.get("currentPlayerId", 0))
        if cur_team not in (1, 2):
            print("[WARN] currentPlayerId 无效，跳过本包", file=sys.stderr)
            continue

        active_saiblo = cur_team - 1
        if player_id != active_saiblo:
            continue

        env_from_state_json(state_data, env)

        if env.current_piece is None:
            print("[WARN] current_piece 为空，发送空动作", file=sys.stderr)
            empty = {
                "player": player_id,
                "content": json.dumps({"move": False, "attack": False, "spell": False}),
            }
            SaibloClient.write_message(empty)
            continue

        try:
            action = action_strategy(env)
        except Exception as e:
            print(f"[ERROR] 策略执行失败: {e}", file=sys.stderr)
            action = ActionSet()

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
