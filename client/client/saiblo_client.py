"""
Saiblo stdin/stdout 通信协议客户端（对齐平台文档）

- judger → AI：**不进行任何封装**（无 4 字节长度头）。本实现按「一条消息一行 UTF-8」读取（readline），
  正文为 judger 转发的 content 原文；空行跳过，EOF 返回 None。
- AI → judger：**4+n**（4 字节大端长度 + JSON 正文）。
"""
import sys
import struct
import json
from typing import Optional


class SaibloClient:
    @staticmethod
    def read_payload() -> Optional[str]:
        """读取 judger 下发的一条 content（UTF-8 文本，无长度头；以换行作为消息边界）。"""
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            text = line.decode("utf-8").rstrip("\r\n")
            if text:
                return text

    @staticmethod
    def read_message() -> Optional[dict]:
        raw = SaibloClient.read_payload()
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    def write_message(data: dict):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        header = struct.pack(">I", len(content))
        sys.stdout.buffer.write(header + content)
        sys.stdout.buffer.flush()
