import grpc
import message_pb2
import message_pb2_grpc
from strategy_factory import StrategyFactory
from State import *
from utils import *
from converter import *

def run():
    # 选择策略
    init_strategy = StrategyFactory.get_aggressive_init_strategy()
    # action_strategy = StrategyFactory.get_defensive_action_strategy()
    
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_pb2_grpc.GameServiceStub(channel)

        # 初始化游戏
        response = stub.SendInit(message_pb2._InitRequest(message="Hello, Server!"))
        print(f"初始化响应: {response.id}")
        player.id = response.id

        # 获取初始化游戏状态并应用初始化策略
        init_policy = Converter.to_proto_piece_args(init_strategy(response))
        
        # 将init_policy转换为protobuf消息并发送
        init_policy_response = message_pb2._InitPolicyRequest(playerId=player.id, pieceArgs=init_policy)

        print("初始化策略已发送")


if __name__ == "__main__":
    player = Player()
    run()