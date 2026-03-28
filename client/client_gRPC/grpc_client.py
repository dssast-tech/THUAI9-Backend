import grpc
import message_pb2
import message_pb2_grpc
from strategy_factory import StrategyFactory
from env import *
from utils import *
from converter import *
from env import Environment
import threading
import argparse


def subscribe_game_state(stub, player_id, action_strategy, env):
    """订阅游戏状态更新"""
    try:
        request = message_pb2._GameStateRequest(playerID=player_id)
        for state in stub.BroadcastGameState(request):
            print(f"\n收到游戏状态更新:")
            print(f"当前回合: {state.currentRound}")
            print(f"当前行动玩家: {state.currentPlayerId}")
            print(f"当前行动棋子: {state.currentPieceID}")
            print(f"游戏是否结束: {state.isGameOver}")
            
            # 如果是当前玩家的回合，生成并发送行动
            if state.currentPlayerId == player_id:
                send_action(stub, state, player_id, action_strategy, env)

            if state.isGameOver:
                print("游戏结束！")
                break
    except grpc.RpcError as e:
        print(f"订阅中断: {e}")
    except Exception as e:
        print(f"处理游戏状态时出错: {e}")

def send_action(stub, state, player_id, action_strategy, env):
    try:
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

def start_subscription(stub, player_id, action_strategy, env):
    """在新线程中启动订阅"""
    subscribe_game_state(stub, player_id, action_strategy, env)

def parse_args():
    parser = argparse.ArgumentParser(description='gRPC游戏客户端')
    parser.add_argument('--host', type=str, default='localhost',
                      help='服务器主机名或IP地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=50051,
                      help='服务器端口号 (默认: 50051)')
    parser.add_argument('--mode', type=str, 
                      choices=['local', 'remote', 'function'],
                      default='remote',
                      help='运行模式: local-本地控制台模式, remote-远程gRPC模式, function-函数式输入模式 (默认: remote)')
    parser.add_argument('--board', type=str, default=None,
                      help='棋盘文件路径 (仅本地模式使用)')
    parser.add_argument('--strategy', type=str,
                      choices=['aggressive', 'defensive', 'mcts'],
                      default='mcts',
                      help='AI策略: aggressive-进攻型, defensive-防御型, mcts-蒙特卡洛树搜索 (默认: mcts)')
    parser.add_argument('--mcts-simulations', type=int, default=25,
                      help='MCTS模拟次数 (默认: 50)')
    return parser.parse_args()

def run():
    # 解析命令行参数
    args = parse_args()
    
    # 创建环境实例
    env = Environment(local_mode=(args.mode == 'local'))
    
    # 选择策略
    if args.strategy == 'aggressive':
        init_strategy = StrategyFactory.get_aggressive_init_strategy()
        action_strategy = StrategyFactory.get_aggressive_action_strategy()
    elif args.strategy == 'defensive':
        init_strategy = StrategyFactory.get_defensive_init_strategy()
        action_strategy = StrategyFactory.get_defensive_action_strategy()
    else:  # mcts
        init_strategy = StrategyFactory.get_defensive_init_strategy()  # MCTS只用于行动策略
        action_strategy = StrategyFactory.get_mcts_action_strategy(args.mcts_simulations)
    
    if args.mode == 'local':
        print("启动本地控制台模式...")
        env.enable_replay = True  # 启用回放记录
        env.run()
        
    elif args.mode == 'function':
        print("启动函数式输入模式...")
        env.enable_replay = True  # 启用回放记录
        
        # 设置玩家1为函数式输入（AI），玩家2为控制台输入
        env.input_manager.set_function_input_method(1, init_strategy, action_strategy)
        env.input_manager.set_console_input_method(2)
        
        # 运行游戏
        env.run()
        
    else:  # remote
        # 远程gRPC模式
        player = Player()
        server_address = f'{args.host}:{args.port}'
        print(f"连接到服务器: {server_address}")
        
        with grpc.insecure_channel(server_address) as channel:
            stub = message_pb2_grpc.GameServiceStub(channel)

            # 初始化游戏
            response = stub.SendInit(message_pb2._InitRequest(message="Hello, Server!"))
            print(f"初始化响应: {response.id}")
            player.id = response.id

            # 将protobuf响应转换为InitGameMessage并应用初始化策略
            init_message = Converter.from_proto_init_response(response)
            init_policy = init_strategy(init_message)
            
            # 将策略结果转换为protobuf消息并发送
            init_policy_proto = Converter.to_proto_piece_args(init_policy)
            init_policy_response = stub.SendInitPolicy(message_pb2._InitPolicyRequest(
                playerId=player.id, 
                pieceArgs=init_policy_proto
            ))

            print("初始化策略已发送")

            # 启动游戏状态订阅
            print("开始订阅游戏状态...")
            subscription_thread = threading.Thread(
                target=start_subscription,
                args=(stub, player.id, action_strategy, env),
                daemon=True
            )
            subscription_thread.start()
            print("已完成订阅")
            
            # 保持主线程运行
            try:
                subscription_thread.join()
            except KeyboardInterrupt:
                print("\n程序被用户中断")

if __name__ == "__main__":
    run()