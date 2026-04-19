# controller.py 文档

## 概述

`controller.py` 主要包含两个核心类：

- `DummyEnvironment`：基于项目现有 `Environment` 实现的可配置测试环境，用于接受来自 UI 的自定义配置并初始化游戏环境。
- `Controller`：统一管理游戏环境、输入、数据加载与执行流程，支持环境驱动的回合执行和游戏数据回放两种模式。

该文件属于 `client/client_gRPC/dev_test/logic` 目录，旨在将测试可视化环境与后端/模拟数据接口连接起来。

---

## DummyEnvironment

### 继承关系

- 继承自 `env.Environment`

### 作用

`DummyEnvironment` 提供一个可定制的测试环境，允许 UI 将用户输入包装成配置字典，并将其应用于环境。它同时保留来自 `Environment` 的游戏逻辑、棋盘管理和回合执行能力。

### 属性

- `custom_config: Dict[str, Any]`
  - 存储来自 UI 或外部模块的配置字典。

### 方法

#### `__init__(self, local_mode: bool = True, if_log: int = 1)`

- 初始化 `DummyEnvironment`。
- 通过 `super().__init__()` 创建父类 `Environment`。
- 初始化 `custom_config` 用于后续配置存储。

#### `apply_environment_config(self, config: Dict[str, Any]) -> None`

- 将外部传入配置整合到 `custom_config`。
- 支持三类配置字典：
  - `board`：棋盘相关配置，交给 `set_board_config()` 处理。
  - `players`：玩家参数配置，交给 `set_player_config()` 处理。
  - `game`：整体游戏设置，交给 `set_game_settings()` 处理。

#### `set_board_config(self, board_config: Dict[str, Any]) -> None`

- 将 `board_config` 保存到 `custom_config`。
- 尝试按配置读取棋盘文件：
  - 如果 `board_file` 存在，调用 `self.board.init_from_file()`。
  - 若读取失败，则 fallback 到 `create_default_board()`。
- 支持在配置中指定默认棋盘、宽高、边界、障碍列表。
- 若配置包含 `obstacles`，则会更新 `self.board.grid` 中对应坐标的 `state` 为 `-1`。

#### `set_player_config(self, player_id: int, player_config: Dict[str, Any]) -> None`

- 保存玩家配置到 `custom_config['players']`。
- 用 `player_id` 定位 `self.player1` 或 `self.player2`。
- 目前实现支持：
  - 更新 `player.feature_total`
  - 更新 `player.piece_num`

#### `set_game_settings(self, settings: Dict[str, Any]) -> None`

- 保存游戏级别设置到 `custom_config['game']`。
- 支持：
  - `if_log`：控制日志输出开关。
  - `local_mode`：控制本地/远程模式，映射到父类的 `mode`。

#### `initialize_environment(self, board_file: Optional[str] = None) -> None`

- 调用父类 `initialize()` 完成环境基础初始化。
- 若 `custom_config` 已存在，则重新应用配置，确保 UI 设置能够生效。

---

## Controller

### 作用

`Controller` 是测试环境的入口控制器，负责：

- 创建并管理 `DummyEnvironment`
- 加载游戏数据（后端优先，失败回退 mock）
- 选择运行模式
- 启动回合执行流程
- 为 UI 或测试代码提供环境快照

### 属性

- `environment: Optional[DummyEnvironment]`
  - 当前使用的环境实例。
- `input_manager: Optional[InputMethodManager]`
  - 来自环境的输入管理器对象。
- `game_mode: str`
  - 运行模式，支持 `manual`、`half-auto`、`auto`。
- `current_round: int`
  - 当前数据回放回合索引。
- `game_data: Optional[Dict[str, Any]]`
  - 原始或解码后的游戏数据。

### 方法

#### `__init__(self, mode: str = "manual")`

- 初始化 `Controller`。
- 设置默认游戏模式为 `manual`。

#### `create_environment(self, local_mode: bool = True, if_log: int = 1) -> DummyEnvironment`

- 创建新的 `DummyEnvironment` 实例。
- 关联 `self.input_manager` 为环境的输入管理器。
- 返回新创建的环境对象。

#### `setup_environment(self, config: Optional[Dict[str, Any]] = None, board_file: Optional[str] = None, local_mode: bool = True, if_log: int = 1) -> DummyEnvironment`

- 创建并初始化环境。
- 支持传入配置字典提前应用环境参数。
- 调用 `env.initialize_environment(board_file=board_file)`。
- 这是建立环境并立即准备好执行的首选方法。

#### `apply_environment_config(self, config: Dict[str, Any]) -> None`

- 将配置应用到当前环境。
- 若不存在环境实例，则先创建一个默认环境。

#### `initialize_environment(self, board_file: Optional[str] = None) -> None`

- 初始化当前环境。
- 若没有环境则先创建空环境。

#### `reset_environment(self) -> None`

- 重置当前环境为新的 `DummyEnvironment` 实例。
- 保留原环境的 `local_mode` 与 `if_log` 设置。

#### `get_environment_snapshot(self) -> Optional[Dict[str, Any]]`

- 返回当前环境的一份状态快照。
- 若未创建环境，则返回 `None`。

#### `load_game_data(self, prefer_backend: bool = True)`

- 使用 `DataProvider` 加载游戏数据。
- 支持优先从后端获取数据，失败时自动回退到本地 mock 数据。
- 如果加载的数据不包含 `map` 字段，则调用 `GameDataDecoder.decode()`。
- 初始化 `self.current_round = 0`。

#### `select_mode(self, mode: str)`

- 切换运行模式。
- 只接受 `manual`、`half-auto` 和 `auto`。

#### `run_round(self)`

- 如果存在 `DummyEnvironment`：
  - 检查环境是否已结束。
  - 如果环境尚未初始化则调用 `initialize_environment()`。
  - 执行环境单步 `self.environment.step()`。
  - 返回是否继续运行，即 `not self.environment.is_game_over`。
- 如果不存在环境，则回放 `game_data`：
  - 检查数据加载状态。
  - 如果当前回合超出总回合数，打印结束提示并返回 `False`。
  - 否则打印本回合信息并推进 `current_round`。

#### `run_loop(self, max_rounds: Optional[int] = None)`

- 启动主循环。
- 若存在环境，调用 `run_round()` 直到环境结束或达到 `max_rounds`。
- 若不存在环境，则回放游戏数据直到结束或达到 `max_rounds`。

---

## 使用建议

- 对于 UI 集成场景，推荐先调用 `Controller.setup_environment(config, board_file, local_mode, if_log)`。
- 若需要调试或重置环境，使用 `Controller.reset_environment()`。
- 若只需要展示游戏回合日志，可直接加载 `game_data` 并调用 `run_loop()`。

---

## 备注

- 该文档基于当前 `controller.py` 的最新实现生成。
- 如果后续增加更多环境或数据接口方法，建议同步维护本文档。