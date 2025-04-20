import http.server
import json
import requests  # 用于向客户端发送请求
from threading import Thread
import time  # 用于轮询检测

# 示例 server_to_client.json 数据
SERVER_TO_CLIENT_JSON = {
    "gameState": {
        "currentRound": 1,
        "currentPlayerid": 0
    },
    "Piece": [
        {
            "health": 100,
            "max_health": 100,
            "physical_resist": 10,
            "magic_resist": 5,
            "physical_damage": 20,
            "magic_damage": 10,
            "action_points": 2,
            "max_action_points": 2,
            "spell_slots": 1,
            "max_spell_slots": 1,
            "movement": 5.0,
            "max_movement": 5.0,
            "id": 1,
            "strength": 10,
            "dexterity": 8,
            "intelligence": 6,
            "position": {"x": 3, "y": 4},
            "height": 0,
            "attack_range": 2,
            "spell_list": [],
            "team": 0,
            "queue_index": 0,
            "is_alive": True,
            "is_in_turn": True,
            "is_dying": False,
            "spell_range": 3.0
        }
    ],
    "Board": {
        "width": 10,
        "height": 10,
        "grid": [[0 for _ in range(10)] for _ in range(10)],
        "height_map": [[0 for _ in range(10)] for _ in range(10)]
    },
    "Env": {
        "action_queue": [],
        "round_number": 1,
        "delayed_spells": [],
        "isGameOver": False
    }
}


class ServerHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        # 读取客户端发送的数据
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            # 解析客户端返回的策略信息
            client_data = json.loads(post_data.decode('utf-8'))
            print("收到客户端返回的策略信息：")
            print(json.dumps(client_data, indent=4))

            # 返回响应
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"Server received the policy message successfully.")
        except Exception as e:
            # 错误处理
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))

    def do_GET(self):
        # 处理 GET 请求，向客户端发送游戏状态信息
        try:
            response_data = json.dumps(SERVER_TO_CLIENT_JSON).encode('utf-8')

            # 返回响应
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response_data)
        except Exception as e:
            # 错误处理
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))


def wait_for_client():
    """轮询检测客户端是否已启动"""
    client_url = "http://localhost:5002/receive/"
    while True:
        try:
            # 尝试向客户端发送一个简单的 GET 请求
            response = requests.get(client_url, timeout=1)
            print("客户端已连接，准备发送游戏状态...")
            return
        except requests.exceptions.ConnectionError:
            print("等待客户端连接...")
            time.sleep(1)  # 每隔 1 秒重试


def run_server():
    server_address = ('localhost', 5001)
    httpd = http.server.HTTPServer(server_address, ServerHandler)
    print("服务器已启动，监听地址：http://localhost:5001")

    # 等待客户端连接
    wait_for_client()

    # 模拟向客户端发送 GET 请求
    try:
        print("向客户端发送游戏状态...")
        response = requests.get("http://localhost:5002/receive/")
        print("收到客户端响应：")
        print(response.text)
    except Exception as e:
        print(f"向客户端发送请求失败：{e}")

    httpd.serve_forever()


if __name__ == "__main__":
    server_thread = Thread(target=run_server)
    server_thread.start()