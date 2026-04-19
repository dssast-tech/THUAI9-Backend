"""
Game Host 主程序 (Saiblo 协议版) — 纯 Python 引擎，无 pythonnet / C# DLL。
"""

import sys
import json
import time
from typing import Dict, Any, List

from saiblo_protocol import SaibloProtocol
from game_engine import GameEngineWrapper


class GameHost:
    """Game Host 主类"""

    def __init__(self):
        self.wrapper = GameEngineWrapper(if_log=0)
        self.replay_file = None
        self.player_types = [0, 0]
        self.round_number = 0
        self.game_over = False

    def initialize(self):
        print("[INFO] ========== 初始化阶段 ==========", file=sys.stderr)

        init_msg = SaibloProtocol.read_message()
        if not init_msg:
            print("[ERROR] 未收到初始化消息", file=sys.stderr)
            sys.exit(1)

        init_info = SaibloProtocol.parse_init_message(init_msg)
        print(f"[INFO] 收到初始化消息: {init_info}", file=sys.stderr)

        try:
            self.replay_file = open(init_info["replay"], "w", encoding="utf-8")
        except Exception as e:
            print(f"[ERROR] 无法打开回放文件: {e}", file=sys.stderr)
            sys.exit(1)

        self.wrapper.initialize(init_info["config"])
        self.player_types = init_info["player_list"]

        for saiblo_id in [0, 1]:
            default_pieces = self._get_default_pieces(saiblo_id)
            result = self.wrapper.set_player_pieces(saiblo_id, default_pieces)
            print(
                f"[INFO] SetPlayerPieces({saiblo_id}) = {result}, pieces={default_pieces}",
                file=sys.stderr,
            )

        SaibloProtocol.send_round_config(time=60, length=4096)

        print("[INFO] 初始化完成", file=sys.stderr)

    def _get_default_pieces(self, player_id: int) -> List[Dict]:
        return [
            {
                "strength": 10,
                "intelligence": 10,
                "dexterity": 10,
                "equip": {"x": 1, "y": 2},
                "pos": {"x": 5, "y": 2 if player_id == 0 else 12},
            }
        ]

    def game_loop(self):
        print("[INFO] ========== 游戏开始 ==========", file=sys.stderr)

        while not self.wrapper.is_game_over():
            self.round_number += 1

            self.wrapper.next_turn()

            state_json = self.wrapper.get_state_json()
            state_data = json.loads(state_json)

            self.replay_file.write(state_json + "\n")
            self.replay_file.flush()

            SaibloProtocol.send_watch_info(state_json)

            csharp_pid = state_data.get("currentPlayerId", 1)
            active_saiblo_id = csharp_pid - 1

            content_list = [state_json, state_json]
            SaibloProtocol.send_round_info(
                state=self.round_number,
                listen=[active_saiblo_id],
                players=[0, 1],
                content=content_list,
            )

            ai_msg = SaibloProtocol.read_message()
            if not ai_msg:
                print(f"[WARN] 回合 {self.round_number}: AI 未响应", file=sys.stderr)
                continue

            parsed_ai = SaibloProtocol.parse_ai_message(ai_msg)

            if parsed_ai["is_error"]:
                error_type = parsed_ai["error_type"]
                print(
                    f"[ERROR] 玩家 {active_saiblo_id} 发生错误: {error_type}",
                    file=sys.stderr,
                )
                continue

            if parsed_ai["player"] == active_saiblo_id:
                action_json = parsed_ai["content"]
                self.wrapper.execute_action(active_saiblo_id, action_json)

        print("[INFO] ========== 游戏结束 ==========", file=sys.stderr)
        self.finalize()

    def finalize(self):
        winner = self.wrapper.get_winner()

        scores = {"0": 1 if winner == 1 else 0, "1": 1 if winner == 2 else 0}
        states = ["OK", "OK"]

        SaibloProtocol.send_game_end(scores, states)

        if self.replay_file:
            self.replay_file.close()


if __name__ == "__main__":
    host = GameHost()
    try:
        host.initialize()
        host.game_loop()
    except Exception as e:
        print(f"[FATAL] 运行时崩溃: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
