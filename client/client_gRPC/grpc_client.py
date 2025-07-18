import grpc
import message_pb2
import message_pb2_grpc
from strategy_factory import StrategyFactory
from State import *
from utils import *
from converter import *
import asyncio
import threading
import time

async def subscribe_game_state(stub, player_id, action_strategy):
    """订阅游戏状态更新"""
    try:
        request = message_pb2._GameStateRequest(playerID=player_id)
        for state in stub.BroadcastGameState(request):  # 改为普通的 for 循环
            print(f"\n收到游戏状态更新:")
            print(f"当前回合: {state.currentRound}")
            print(f"当前行动玩家: {state.currentPlayerId}")
            print(f"当前行动棋子: {state.currentPieceID}")
            print(f"游戏是否结束: {state.isGameOver}")
            
            # 如果是当前玩家的回合，生成并发送行动
            if state.currentPlayerId == player_id:
                await send_action(stub, state, player_id, action_strategy)

            if state.isGameOver:
                print("游戏结束！")
                break
    except grpc.RpcError as e:
        print(f"订阅中断: {e}")
    except Exception as e:
        print(f"处理游戏状态时出错: {e}")

async def send_action(stub, state, player_id, action_strategy):
    try:
        # 等待一小段时间，确保服务器准备好接收行动
        await asyncio.sleep(0.1)
        
        # 将游戏状态转换为策略函数需要的格式
        Converter.from_proto_game_state(state, env)
        
        # 使用策略生成行动
        action = action_strategy(env)
        # 将行动转换为protobuf格式
        action_proto = Converter.to_proto_action(action, player_id)
        
        print(f"发送行动: {action}")
        
        # 发送行动到服务器
        response = stub.SendAction(action_proto)
        
        if response.success:
            print("行动已被接受")
        else:
            print(f"行动被拒绝: {response.mes}")
            
    except Exception as e:
        print(f"发送行动时出错: {e}")
        raise  # 重新抛出异常以便查看完整的错误堆栈

def start_subscription(stub, player_id, action_strategy):
    """在新线程中启动异步订阅"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(subscribe_game_state(stub, player_id, action_strategy))
    loop.close()

def run():
    # 选择策略
    init_strategy = StrategyFactory.get_aggressive_init_strategy()
    action_strategy = StrategyFactory.get_defensive_action_strategy()
    
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_pb2_grpc.GameServiceStub(channel)

        # 初始化游戏
        response = stub.SendInit(message_pb2._InitRequest(message="Hello, Server!"))
        print(f"初始化响应: {response.id}")
        player.id = response.id

        # 获取初始化游戏状态并应用初始化策略
        init_policy = Converter.to_proto_piece_args(init_strategy(response))
        
        # 将init_policy转换为protobuf消息并发送
        init_policy_response = stub.SendInitPolicy(message_pb2._InitPolicyRequest(playerId=player.id, pieceArgs=init_policy))

        print("初始化策略已发送")

        # 启动游戏状态订阅
        print("开始订阅游戏状态...")
        subscription_thread = threading.Thread(
            target=start_subscription,
            args=(stub, player.id, action_strategy),
            daemon=True  # 设置为守护线程，这样主程序退出时会自动结束
        )
        subscription_thread.start()
        print("已完成订阅")
        # 保持主线程运行
        try:
            subscription_thread.join()
        except KeyboardInterrupt:
            print("\n程序被用户中断")

if __name__ == "__main__":
    player = Player()
    env = Env()  # 确保env是全局变量
    run()