import http.server
import json
from threading import Thread
from game_message import GameMessage, PolicyMessage


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

    def stop(self):
        self.is_running = False
        print("客户端监听停止")

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
            # 读取请求数据
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