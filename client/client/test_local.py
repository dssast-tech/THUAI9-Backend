#!/usr/bin/env python3
"""
测试本地游戏功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from env import Environment, Player, Board, Piece

def test_local_game():
    """测试本地游戏功能"""
    print("=== 测试本地游戏功能 ===")
    
    # 创建环境
    env = Environment(local_mode=True)
    
    # 测试初始化
    try:
        env.initialize()
        print("✓ 游戏初始化成功")
        
        # 检查玩家和棋盘
        assert env.player1 is not None, "玩家1未创建"
        assert env.player2 is not None, "玩家2未创建"
        assert env.board is not None, "棋盘未创建"
        assert len(env.action_queue) > 0, "行动队列为空"
        
        print("✓ 玩家和棋盘创建成功")
        print(f"✓ 玩家1棋子数: {len(env.player1.pieces)}")
        print(f"✓ 玩家2棋子数: {len(env.player2.pieces)}")
        print(f"✓ 行动队列棋子数: {len(env.action_queue)}")
        
        # 检查第一个棋子
        first_piece = env.action_queue[0]
        print(f"✓ 第一个棋子: ID={first_piece.id}, 团队={first_piece.team}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_local_game()
    if success:
        print("\n=== 所有测试通过 ===")
        print("可以尝试运行: python local_client.py")
    else:
        print("\n=== 测试失败 ===")