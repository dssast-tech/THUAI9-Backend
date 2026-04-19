# 项目入口文件
# 负责整合各模块，启动测试界面

import sys
import os
from typing import Optional

# 添加当前目录到路径，便于导入模块
sys.path.append(os.path.dirname(__file__))

from logic.controller import Controller

# 新增：用于被 grpc_client.py 的 --mode test 调用
def run_realtime_test():
    """启动测试环境，默认使用手动模式并优先本地玩法环境。"""
    main(mode="manual", prefer_runtime=True)
    
def main(mode: str = "manual", prefer_runtime: bool = True):
    controller = Controller(mode=mode)
    try:
        controller.select_mode(mode)
    except NotImplementedError as e:
        print(f"模式 {mode} 当前待开发：{e}")
        return

    try:
        game_data = controller.load_game_data(prefer_runtime=prefer_runtime)
        source = controller.runtime_source
        if source == "runtime_env":
            print("已加载本地玩法环境，进入手动测试一期模式")
        else:
            print(f"本地玩法环境未启用，使用 mock 数据，回合数 = {len(game_data.get('rounds', []))}")
    except Exception as e:
        print(f"加载游戏数据失败：{e}")
        return

    controller.run_loop()


if __name__ == "__main__":
    # 1. 全局手动对战: mode=manual
    # 2. 半自动（单人操作/机器对手）: mode=half-auto
    # 3. 全自动对战: mode=auto（待开发）
    main(mode="manual", prefer_runtime=True)
