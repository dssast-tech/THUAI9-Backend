数据传输思路：
┌─────────────────────────────────────┐
│   可视化层（UI组件）                 │
├─────────────────────────────────────┤
│   测试逻辑层（controller/decoder）   │
├─────────────────────────────────────┤
│   游戏状态抽象层（Game State）       │
├─────────────┬───────────────────────┤
│  真实后端    │    Mock数据源        │
│  (gRPC)     │   (JSON文件/硬编码)   │
└─────────────┴───────────────────────┘
mock源放置在data文件夹中
------------------------------
当前运行逻辑说明
------------------------------
1. `main.py` 启动时创建 `Controller`，先调用 `load_game_data(prefer_backend=True)`。
2. `DataProvider` 尝试 `load_from_backend()`：
   - 建立 gRPC 连接到 `localhost:50051`（可通过 `DataProvider` 初始化参数修改）
   - 调用 `grpc_client.message_pb2_grpc.GameServiceStub.SendInit`（带 `ping` 字段）
   - 若无异常，认为后端可用并返回后端状态/初始化信息
3. 如果后端不可用（RPC 异常、连接失败等），`get_game_data` 捕获后退并调用 `load_from_mock()`；读取本地 `data/log.json`。
4. `GameDataDecoder.decode(raw)` 解析：
   - `map`、`playerData`、`soldiersData`、`gameRounds` 
   - 归一化 `rounds` 结构用于 `Controller.run_loop`

------------------------------
控制接口与切换点
------------------------------
- `Controller.select_mode(mode)`
  - `mode` 值支持 `manual`、`half-auto`、`auto`，目前主要用于 future 行为分支。
  - `main.py` 启动为 `manual`，可改成 `half-auto` 等。
- 数据来源选择：
  - `Controller.load_game_data(prefer_backend=True)`（首选后端，失败回 mock）
  - 或直接 `Controller.load_game_data(prefer_backend=False)` 强制 mock

------------------------------
需补充部分（给可视化同学）
------------------------------
- 定义 UI 对应接口：`on_round_update(round_index, actions)`、`on_game_end()`、`on_error(message)`
- `Controller` 可在 `run_round` 中返回当前回合信息：`{'roundNumber': ..., 'actions': ...}`
- 后端对接时补充 `DataProvider.load_from_backend` 以支持完整回合流（如 `GetGameState`），替换简易 `SendInit` 探测。
