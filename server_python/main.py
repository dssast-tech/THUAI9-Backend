"""
Game Host 主程序 (Saiblo 协议版) — 纯 Python 引擎，无 pythonnet / C# DLL。
"""

import sys
import json
import time
from typing import Dict, Any, List

from saiblo_protocol import SaibloProtocol
from game_engine import GameEngineWrapper
from env import Player


class GameHost:
    """Game Host 主类"""

    def __init__(self):
        self.wrapper = GameEngineWrapper(if_log=0)
        self.replay_file = None
        self.player_types = [0, 0]
        self.round_number = 0
        self.game_over = False
        self._proto_round = 0

    def initialize(self):
        print("[INFO] ========== init phase ==========", file=sys.stderr)

        init_msg = SaibloProtocol.read_message()
        if not init_msg:
            print("[ERROR] no init message from judger", file=sys.stderr)
            sys.exit(1)

        init_info = SaibloProtocol.parse_init_message(init_msg)
        print(f"[INFO] init message: {init_info}", file=sys.stderr)

        try:
            self.replay_file = open(init_info["replay"], "w", encoding="utf-8")
        except Exception as e:
            print(f"[ERROR] cannot open replay file: {e}", file=sys.stderr)
            sys.exit(1)

        self.wrapper.initialize(init_info["config"])
        self.player_types = init_info["player_list"]

        SaibloProtocol.send_round_config(time=60, length=4096)

        print("[INFO] init phase done", file=sys.stderr)

    def _run_init_handshake(self) -> None:
        """首回合：向双方 AI 下发其 Saiblo 座位号（JSON 数字串），并收齐初始化回执。"""
        self._proto_round += 1
        content = [
            json.dumps(0, ensure_ascii=False) + "\n",
            json.dumps(1, ensure_ascii=False) + "\n",
        ]
        SaibloProtocol.send_round_info(
            state=self._proto_round,
            listen=[0, 1],
            players=[0, 1],
            content=content,
        )
        received: Dict[int, str] = {}
        while len(received) < 2:
            ai_msg = SaibloProtocol.read_message()
            if not ai_msg:
                print("[ERROR] init round: missing AI response", file=sys.stderr)
                sys.exit(1)
            parsed = SaibloProtocol.parse_ai_message(ai_msg)
            if parsed["is_error"]:
                print(
                    f"[ERROR] init round AI error: type={parsed['error_type']}",
                    file=sys.stderr,
                )
                sys.exit(1)
            pid = int(parsed["player"])
            if pid not in (0, 1):
                print(f"[ERROR] invalid player id: {pid}", file=sys.stderr)
                sys.exit(1)
            received[pid] = parsed["content"]
            print(
                f"[INFO] init ack from player={pid}, content_bytes={len(parsed['content'].encode('utf-8'))}",
                file=sys.stderr,
            )
        for pid in sorted(received.keys()):
            try:
                pieces = self._parse_init_ack_payload(received[pid], pid)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"[ERROR] parse init ack for player {pid} failed: {e}", file=sys.stderr)
                print(f"[ERROR] raw init ack for player {pid}:", file=sys.stderr)
                print(received[pid], file=sys.stderr)
                sys.exit(1)
            ok = self.wrapper.set_player_pieces(pid, pieces)
            print(
                f"[INFO] SetPlayerPieces({pid}) = {ok}, piece_cnt={len(pieces)}",
                file=sys.stderr,
            )
            if not ok:
                print(f"[ERROR] SetPlayerPieces({pid}) failed", file=sys.stderr)
                sys.exit(1)
        print(f"[INFO] init round done (placements applied): {list(received.keys())}", file=sys.stderr)

    @staticmethod
    def _unwrap_ai_content(payload: Any) -> Any:
        """
        judger -> logic 的 AI 正常消息形如: {"player": <id>, "content": "<AI消息>"}。
        而我们的 AI 通常发送 JSON 对象 {"player": <id>, "content": "..."}，
        所以 logic 侧读到的 content 可能是“外层 JSON 字符串”，需要解一层得到真正业务内容。
        """
        if isinstance(payload, str):
            s = payload.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    d = json.loads(s)
                except json.JSONDecodeError:
                    return payload
                if isinstance(d, dict) and "content" in d and "player" in d and "phase" not in d:
                    return d.get("content")
        if isinstance(payload, dict) and "content" in payload and "player" in payload and "phase" not in payload:
            return payload.get("content")
        return payload

    @staticmethod
    def _parse_init_ack_payload(content: str, saiblo_id: int) -> List[Dict[str, Any]]:
        """解析 AI 首回合回执：{"phase":"init","pieces":[{strength,intelligence,dexterity,equip,pos},...]}"""
        d = json.loads(content)
        d = GameHost._unwrap_ai_content(d)
        if isinstance(d, str):
            d = json.loads(d)
        if not isinstance(d, dict) or d.get("phase") != "init":
            raise ValueError(f"player {saiblo_id}: expected JSON object with phase=init")
        pieces = d.get("pieces")
        if not isinstance(pieces, list) or len(pieces) != Player.PIECE_CNT:
            n = len(pieces) if isinstance(pieces, list) else -1
            raise ValueError(
                f"player {saiblo_id}: pieces must be a list of length {Player.PIECE_CNT}, got len={n}"
            )
        for i, p in enumerate(pieces):
            if not isinstance(p, dict):
                raise ValueError(f"player {saiblo_id}: pieces[{i}] must be an object")
            for k in ("strength", "intelligence", "dexterity", "equip", "pos"):
                if k not in p:
                    raise ValueError(f"player {saiblo_id}: pieces[{i}] missing field {k}")
        return pieces

    def game_loop(self):
        print("[INFO] ========== game loop start ==========", file=sys.stderr)

        self._run_init_handshake()
        self._send_watch_init()

        while not self.wrapper.is_game_over():
            self.round_number += 1

            self.wrapper.next_turn()

            state_json = self.wrapper.get_state_json()
            state_data = json.loads(state_json)

            csharp_pid = state_data.get("currentPlayerId", 1)
            active_saiblo_id = max(0, csharp_pid - 1)

            content_list = [state_json + "\n", state_json + "\n"]
            self._proto_round += 1
            SaibloProtocol.send_round_info(
                state=self._proto_round,
                listen=[active_saiblo_id],
                players=[0, 1],
                content=content_list,
            )

            ai_msg = SaibloProtocol.read_message()
            if not ai_msg:
                print(f"[WARN] round {self.round_number}: no AI response", file=sys.stderr)
                continue

            parsed_ai = SaibloProtocol.parse_ai_message(ai_msg)

            if parsed_ai["is_error"]:
                error_type = parsed_ai["error_type"]
                print(
                    f"[ERROR] player {active_saiblo_id} error: {error_type}",
                    file=sys.stderr,
                )
                continue

            if parsed_ai["player"] == active_saiblo_id:
                action_json = self._unwrap_ai_content(parsed_ai["content"])
                if not isinstance(action_json, str):
                    action_json = json.dumps(action_json, ensure_ascii=False)
                ok = self.wrapper.execute_action(active_saiblo_id, action_json)
                if ok:
                    self._send_watch_round_delta()

        print("[INFO] ========== game over ==========", file=sys.stderr)
        self.finalize()

    def _send_watch_init(self) -> None:
        """按播放器格式发送一次初始化数据（不含 gameRounds）。"""
        try:
            replay = json.loads(self.wrapper.get_replay_json())
            if not isinstance(replay, dict):
                return
            base = {
                "mapdata": replay.get("mapdata"),
                "playerData": replay.get("playerData"),
                "soldiersData": replay.get("soldiersData"),
            }
            SaibloProtocol.send_watch_info(json.dumps({"type": "init", "data": base}, ensure_ascii=False))
        except Exception:
            return

    def _send_watch_round_delta(self) -> None:
        """按播放器格式发送最近一回合增量（gameRounds[-1]）。"""
        try:
            replay = json.loads(self.wrapper.get_replay_json())
            if not isinstance(replay, dict):
                return
            rounds = replay.get("gameRounds")
            if not isinstance(rounds, list) or not rounds:
                return
            last_round = rounds[-1]
            SaibloProtocol.send_watch_info(json.dumps({"type": "round", "data": last_round}, ensure_ascii=False))
        except Exception:
            return

    def finalize(self):
        winner = self.wrapper.get_winner()

        scores = {"0": 1 if winner == 1 else 0, "1": 1 if winner == 2 else 0}
        states = ["OK", "OK"]

        # 一次性写回放（播放器期望格式：log_converter 输出）
        try:
            if self.replay_file:
                self.replay_file.seek(0)
                self.replay_file.truncate(0)
                self.replay_file.write(self.wrapper.get_replay_json())
                self.replay_file.flush()
        except Exception:
            pass

        SaibloProtocol.send_game_end(scores, states)

        if self.replay_file:
            self.replay_file.close()


if __name__ == "__main__":
    host = GameHost()
    try:
        host.initialize()
        host.game_loop()
    except Exception as e:
        print(f"[FATAL] unhandled exception: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
