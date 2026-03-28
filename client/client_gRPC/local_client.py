#!/usr/bin/env python3
"""
本地控制台游戏客户端
用于在不连接服务器的情况下运行游戏
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from env import Environment
from strategy_factory import StrategyFactory

def main():
    """主函数 - 运行本地控制台游戏"""
    print("=== 本地控制台游戏模式 ===")
    print("启动本地游戏...")
    
    # 创建游戏环境，启用回放记录
    env = Environment(local_mode=True, enable_replay=True)
    
    try:
        # 运行游戏
        # # 使用 MCTS 策略
        # init_strategy = StrategyFactory.get_defensive_init_strategy()  # MCTS只用于行动策略
        # action_strategy = StrategyFactory.get_mcts_action_strategy(simulation_count=25)  # MCTS模拟次数

        # # 玩家1：函数式输入（MCTS AI），玩家2：函数式输入（MCTS AI）
        # env.input_manager.set_function_input_method(1, init_strategy, action_strategy)
        # env.input_manager.set_function_input_method(2, init_strategy, action_strategy)
        
        env.run()

    except KeyboardInterrupt:
        print("\n游戏被用户中断")
        # 即使中断也保存回放数据
        if env.enable_replay and env.replay_manager:
            env.replay_manager.save_to_json()
    except Exception as e:
        print(f"游戏运行出错: {e}")
        # 出错时也尝试保存回放数据
        if env.enable_replay and env.replay_manager:
            env.replay_manager.save_to_json()

if __name__ == "__main__":
    main()