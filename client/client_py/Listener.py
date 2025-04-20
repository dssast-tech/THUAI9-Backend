import http.server
import json
from threading import Thread
from game_message import GameMessage, PolicyMessage
import requests  # 用于向服务器发送 GET 请求


class ClientListener:
    def __init__(self, url_prefix, get_action_callback):
        """
        :param url_prefix: 客户端监听的 URL 前缀
        :param get_action_callback: 回调函数，用于处理接收到的 GameMessage 并返回 PolicyMessage
        """
        self.url_prefix = url_prefix
        self.is_running = False
        self.get_action_callback = get_action_callback

    def start(self):
        self.is_running = True
        print(f"客户端监听启动: {self.url_prefix}")

        def run_server():
            server = http.server.HTTPServer(('localhost', 5002), self.RequestHandlerFactory(self.get_action_callback))
            while self.is_running:
                server.handle_request()

        self.server_thread = Thread(target=run_server)
        self.server_thread.start()

        # 在启动监听器后，主动向服务器发送 GET 请求获取初始局面
        self.request_initial_state()

    def stop(self):
        self.is_running = False
        print("客户端监听停止")

    def request_initial_state(self):
        """向服务器发送 GET 请求以获取初始局面"""
        try:
            print("向服务器请求初始局面...")
            response = requests.get("http://localhost:5001")
            game_state = response.json()
            print("收到服务器返回的初始局面：")
            print(json.dumps(game_state, indent=4))

            # 调用回调函数生成策略
            policy_message = self.get_action_callback(GameMessage.from_dict(game_state))

            # 将策略通过 POST 请求发送回服务器
            self.send_policy_to_server(policy_message)
        except Exception as e:
            print(f"请求初始局面失败：{e}")

    def send_policy_to_server(self, policy_message):
        """通过 POST 请求将策略发送回服务器"""
        try:
            print("向服务器发送策略...")
            response = requests.post("http://localhost:5001", json=policy_message.to_dict())
            print("服务器响应：", response.text)
        except Exception as e:
            print(f"发送策略失败：{e}")

    class RequestHandlerFactory:
        def __init__(self, get_action_callback):
            self.get_action_callback = get_action_callback

        def __call__(self, *args, **kwargs):
            return ClientListener.RequestHandler(self.get_action_callback, *args, **kwargs)

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        def __init__(self, get_action_callback, *args, **kwargs):
            self.get_action_callback = get_action_callback
            super().__init__(*args, **kwargs)

        def do_POST(self):
            """处理服务器发送的 POST 请求"""
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                # 解析 JSON 数据
                message_data = json.loads(post_data.decode('utf-8'))
                game_message = GameMessage.from_dict(message_data)

                # 调用回调函数获取策略
                policy_message = self.get_action_callback(game_message)

                # 将策略转换为 JSON 格式
                response_data = json.dumps(policy_message.to_dict()).encode('utf-8')

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