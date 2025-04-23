import grpc
from concurrent import futures
import message_pb2
import message_pb2_grpc

class GameService(message_pb2_grpc.GameServiceServicer):
    def Initialize(self, request, context):
        # 初始化游戏状态
        return message_pb2.InitializationResponse(success=True, message="Game initialized")

    def SendAction(self, request, context):
        # 处理客户端发送的动作
        print(f"收到客户端动作: {request}")
        return message_pb2.ActionResponse(success=True, message="Action received")

    def GetGameState(self, request, context):
        # 返回当前游戏状态
        game_state = message_pb2.GameStateResponse(
            game_state=message_pb2.GameState(current_round=1, current_player_id=0),
            piece=message_pb2.Piece(health=100, max_health=100, id=1),
            board=message_pb2.Board(width=10, height=10),
            env=message_pb2.Env(round_number=1, is_game_over=False)
        )
        return game_state

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_pb2_grpc.add_GameServiceServicer_to_server(GameService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC 服务器已启动，监听地址：localhost:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()