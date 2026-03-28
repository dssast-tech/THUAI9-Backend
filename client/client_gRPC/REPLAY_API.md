# 回放系统 API 使用说明

## 概述

回放系统提供了游戏状态的序列化和反序列化功能，可以将游戏过程保存为JSON文件，并支持恢复到任意回合的状态。

## 快速开始

### 1. 启用回放记录

在创建 `Environment` 时启用回放：

```python
from env import Environment

env = Environment(local_mode=True, enable_replay=True)
env.run()  # 游戏结束后会自动保存回放文件
```

### 2. 手动保存回放

```python
# 游戏结束后手动保存
if env.enable_replay and env.replay_manager:
    filepath = env.replay_manager.save_to_json("my_replay.json")
    print(f"回放已保存到: {filepath}")
```

## 核心接口

### ReplayManager 类

回放管理器，提供高级接口用于保存和恢复游戏状态。

#### 初始化

```python
from replay import ReplayManager

# 通常在 Environment 初始化时自动创建
# env.replay_manager = ReplayManager(env)
```

#### 记录回合

```python
# 每回合自动调用（在 env.step() 中）
env.replay_manager.record_round(action)
```

#### 保存到JSON文件

```python
# 自动生成文件名（格式：replay_YYYYMMDD_HHMMSS.json）
filepath = env.replay_manager.save_to_json()

# 指定文件名
filepath = env.replay_manager.save_to_json("custom_replay.json")
```

#### 从JSON文件加载

```python
from replay import ReplayManager

replay_data = ReplayManager.load_from_json("replay_20260314_222454.json")
```

#### 恢复到指定回合

```python
from replay import ReplayManager
from env import Environment

# 创建环境
env = Environment(local_mode=True, if_log=1)

# 加载回放数据
replay_data = ReplayManager.load_from_json("replay_20260314_222454.json")

# 恢复到第5回合（回合编号从1开始）
success = ReplayManager.restore_to_round(env, replay_data, target_round=5)
if success:
    print("已恢复到第5回合")
    env.visualize_board()  # 查看当前状态
else:
    print("恢复失败：回合编号超出范围")
```

#### 恢复到结束状态

```python
from replay import ReplayManager
from env import Environment

env = Environment(local_mode=True, if_log=1)
replay_data = ReplayManager.load_from_json("replay_20260314_222454.json")

success = ReplayManager.restore_to_end(env, replay_data)
if success:
    print("已恢复到游戏结束状态")
    winner = replay_data["game_info"]["winner"]
    print(f"获胜者: 玩家{winner}")
```


## 完整示例

### 示例1：保存并恢复游戏

```python
from env import Environment
from replay import ReplayManager

# 运行游戏并保存回放
env = Environment(local_mode=True, enable_replay=True)
env.run()  # 游戏结束后自动保存

# 加载回放并恢复到第3回合
replay_data = ReplayManager.load_from_json("replay_20260314_222454.json")
new_env = Environment(local_mode=True, if_log=1)
ReplayManager.restore_to_round(new_env, replay_data, target_round=3)

# 查看恢复后的状态
new_env.visualize_board()
print(f"当前回合: {new_env.round_number}")
print(f"当前行动棋子: {new_env.current_piece.id}")
```

