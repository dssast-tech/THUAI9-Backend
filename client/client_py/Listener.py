import http.server
import json
from threading import Thread


class ClientListener:
    def __init__(self, url_prefix):
        self.url_prefix = url_prefix
        self.is_running = False

    def start(self):
        self.is_running = True
        print(f"客户端监听启动: {self.url_prefix}")

        def run_server():
            server = http.server.HTTPServer(('localhost', 5001), self.RequestHandler)
            while self.is_running:
                server.handle_request()

        self.server_thread = Thread(target=run_server)
        self.server_thread.start()

    def stop(self):
        self.is_running = False
        print("客户端监听停止")

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message = json.loads(post_data.decode('utf-8'))

            # 调用客户端业务逻辑
            reply = self.handle_game_message(message)

            response = json.dumps(reply).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response)

        def handle_game_message(self, msg):
            # 调用业务逻辑函数
            raise NotImplementedError()