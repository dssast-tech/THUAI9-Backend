"""
Saiblo stdin/stdout 通信协议客户端
消息格式 (judger -> AI):  [4字节长度(大端序)] + [JSON内容]
消息格式 (AI -> judger):  [4字节长度(大端序)] + [JSON内容]
"""
import sys
import struct
import json
from typing import Optional


class SaibloClient:
    @staticmethod
    def read_message() -> Optional[dict]:
        header = sys.stdin.buffer.read(4)
        if not header or len(header) < 4:
            return None
        length = struct.unpack(">I", header)[0]
        data = sys.stdin.buffer.read(length)
        if len(data) < length:
            return None
        return json.loads(data.decode("utf-8"))

    @staticmethod
    def write_message(data: dict):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        header = struct.pack(">I", len(content))
        sys.stdout.buffer.write(header + content)
        sys.stdout.buffer.flush()
