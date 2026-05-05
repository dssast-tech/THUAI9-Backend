"""
Saiblo 平台通信协议实现
负责通过 stdin/stdout 与 Saiblo Worker 通信
"""

import sys
import struct
import json
from typing import Dict, Any, Optional


class SaibloProtocol:
    """Saiblo 通信协议"""

    @staticmethod
    def read_message() -> Optional[Dict[str, Any]]:
        try:
            length_bytes = sys.stdin.buffer.read(4)
            if not length_bytes or len(length_bytes) < 4:
                return None

            length = struct.unpack(">I", length_bytes)[0]

            data_bytes = sys.stdin.buffer.read(length)
            if len(data_bytes) < length:
                print(
                    f"[ERROR] expected {length} bytes, got {len(data_bytes)}",
                    file=sys.stderr,
                )
                return None

            data_str = data_bytes.decode("utf-8")
            return json.loads(data_str)

        except Exception as e:
            print(f"[ERROR] read_message failed: {e}", file=sys.stderr)
            return None

    @staticmethod
    def write_message(data: Dict[str, Any], target: int = 0):
        try:
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")
            length = len(content)

            header = struct.pack(">Ii", length, target)

            sys.stdout.buffer.write(header)
            sys.stdout.buffer.write(content)
            sys.stdout.buffer.flush()

        except Exception as e:
            print(f"[ERROR] write_message failed: {e}", file=sys.stderr)

    @staticmethod
    def send_round_config(time: int, length: int):
        config = {"state": 0, "time": time, "length": length}
        SaibloProtocol.write_message(config, target=-1)
        print(f"[INFO] send_round_config: time={time}s, length={length} bytes", file=sys.stderr)

    @staticmethod
    def send_round_info(state: int, listen: list, players: list, content: list):
        round_info = {
            "state": state,
            "listen": listen,
            "player": players,
            "content": content,
        }
        SaibloProtocol.write_message(round_info, target=-1)
        print(f"[INFO] send_round_info state={state} listen={listen}", file=sys.stderr)

    @staticmethod
    def send_watch_info(watch_content: str):
        watch_info = {"watch": watch_content}
        SaibloProtocol.write_message(watch_info, target=-1)

    @staticmethod
    def send_game_end(end_info: Dict[str, int], end_state: list):
        game_end = {
            "state": -1,
            "end_info": json.dumps(end_info),
            "end_state": json.dumps(end_state),
        }
        SaibloProtocol.write_message(game_end, target=-1)
        print(f"[INFO] send_game_end: {end_info}, {end_state}", file=sys.stderr)

    @staticmethod
    def parse_init_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "player_list": msg.get("player_list", [1, 1]),
            "replay": msg.get("replay", "/tmp/replay.json"),
            "config": msg.get("config", {}),
        }

    @staticmethod
    def parse_ai_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        player = msg.get("player", -1)
        content = msg.get("content", "")

        if player == -1:
            try:
                error_info = json.loads(content)
                return {
                    "player": error_info.get("player", -1),
                    "content": "",
                    "is_error": True,
                    "error_type": error_info.get("error", 0),
                }
            except Exception:
                return {
                    "player": -1,
                    "content": content,
                    "is_error": True,
                    "error_type": 0,
                }
        else:
            return {
                "player": player,
                "content": content,
                "is_error": False,
                "error_type": None,
            }


class ErrorType:
    RE = 0
    TLE = 1
    OLE = 2


class EndState:
    OK = "OK"
    RE = "RE"
    TLE = "TLE"
    OLE = "OLE"
    IA = "IA"
