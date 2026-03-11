#!/usr/bin/env python3
"""
本地控制台游戏客户端
用于在不连接服务器的情况下运行游戏
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from env import Environment

def main():
    """主函数 - 运行本地控制台游戏"""
    print("=== 本地控制台游戏模式 ===")
    print("启动本地游戏...")
    
    # 创建游戏环境
    env = Environment(local_mode=True)
    
    try:
        # 运行游戏
        env.run()
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
    except Exception as e:
        print(f"游戏运行出错: {e}")

if __name__ == "__main__":
    main()