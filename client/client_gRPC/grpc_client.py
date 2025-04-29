import grpc
import message_pb2
import message_pb2_grpc
import Player

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_pb2_grpc.GameServiceStub(channel)

        # 初始化游戏
        response = stub.SendInit(message_pb2._InitRequest(message="Hello, Server!"))
        print(f"初始化响应: {response.id}")
        player.id = response.id

        # 获取游戏状态
        InitResponse = stub.SendInitPolicy(message_pb2._InitPolicyRequest(id=player.id))
        # print(f"当前游戏状态: {game_state}")

        # 发送动作
        action = message_pb2.ActionRequest(
            action_set=message_pb2.ActionSet(
                move_target=message_pb2.MoveTarget(x=3, y=5),
                attack=False
            )
        )
        action_response = stub.SendAction(action)
        print(f"动作响应: {action_response.message}")

if __name__ == "__main__":
    player = Player()
    run()