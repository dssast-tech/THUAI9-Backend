import http.server
import json
from threading import Thread
import time

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
    def do_GET(self):
        """处理客户端发送的 GET 请求，返回初始局面"""
        try:
            response_data = json.dumps(SERVER_TO_CLIENT_JSON).encode('utf-8')

            # 返回响应
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response_data)
            print("已向客户端发送初始局面")
        except Exception as e:
            # 错误处理
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))

    def do_POST(self):
        """处理客户端发送的 POST 请求，接收决策"""
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


def run_server():
    server_address = ('localhost', 5001)
    httpd = http.server.HTTPServer(server_address, ServerHandler)
    print("服务器已启动，监听地址：http://localhost:5001")
    httpd.serve_forever()


if __name__ == "__main__":
    server_thread = Thread(target=run_server)
    server_thread.start()