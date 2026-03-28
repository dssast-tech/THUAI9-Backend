## THUAI8 引擎 DLL 调用流程说明（通信组使用）

### 1. 初始化阶段

- **加载 DLL（以 Python 为例）**：
  - 通过 `pythonnet` 加载 `server.dll`，获取 `Server.GameEngine` 类型。
- **创建引擎实例并初始化环境**：
  - `engine = GameEngine()`
  - `engine.Initialize(configJson)`  
    - `configJson` 为字符串，可先传入 `"{}"`。
    - 内部完成棋盘加载、`Player` 对象创建等。
- **配置双方棋子**：
  - 对于玩家 0 和 1（Saiblo 习惯）分别调用：
    - `engine.SetPlayerPieces(player_id, pieces_json)`
    - 其中 `player_id` 取值为 `0/1`，在 C# 内部会自动映射为 `1/2`。
    - `pieces_json` 是 `_pieceArg` 数组的 JSON，字段与 `Protos/message.proto` 中的 `_pieceArg` 一致：
      - `strength` / `intelligence` / `dexterity`
      - `equip`: `{ "x": 武器类型(1-4), "y": 防具类型(1-3) }`
      - `pos`: `{ "x": 初始坐标x, "y": 初始坐标y }`
  - 当两边都成功配置后，引擎内部会自动调用 `Env.SetupBattle()`：
    - 根据双方棋子属性掷骰生成初始行动队列。
    - 调用 `Board.init_pieces_location` 初始化棋盘占据。
    - 初始化日志记录器 `LogConverter`。

### 2. 单回合调用时序（强烈建议按此顺序）

每一回合，通信组应按照以下顺序与引擎交互：

1. **开始回合**：
   - 调用：`engine.NextTurn()`
   - 内部行为（Env.BeginTurn）：
     - `round_number++`
     - 为所有仍存活棋子重置行动点为 `max_action_points`
     - 选择当前应行动棋子 `current_piece = action_queue[0]`
     - 记录回合开始的日志（供回放使用）

2. **获取本回合开始时的游戏状态**：
   - 调用：`state_json = engine.GetStateJson()`
   - 语义：**“回合开始快照”**，此时行动点已重置，但本回合的行动尚未执行。
   - JSON 结构对齐 `message.proto` 中的 `_GameStateResponse`：
     - `currentRound` / `currentPlayerId` / `currentPieceID`
     - `actionQueue`: 当前行动队列（列表元素字段与 `_Piece` 对齐）
     - `board`: 包含 `width` / `height` / `grid`(展平的 `_Cell`) / `height_map` / `boarder`
     - `delayedSpells`: 延时法术列表（字段对齐 `_SpellContext`）
     - `isGameOver`
   - 通信组可将 `state_json`：
     - 写入回放文件；
     - 封装进 Saiblo 协议消息，发送给当前需要思考的 AI。

3. **接收 AI 决策并执行操作**：
   - 通信组从 Saiblo Worker 读取 AI 的决策消息，解析出动作 JSON，语义对齐 `_actionSet`：
     - `move` (bool)
     - `move_target` (`{ "x": int, "y": int }`)
     - `attack` (bool)
     - `attack_context`: `{ "attacker": (可忽略), "target": 目标棋子ID }`
     - `spell` (bool)
     - `spell_context`:
       - `caster`（可忽略）
       - `spellID`（法术 ID，见现有 `SpellFactory`）
       - `targetType`（枚举 `_TargetType` 的 int 编码）
       - `target`（目标棋子 ID）
       - `targetArea`: `{ "x": int, "y": int, "radius": int }`
       - `spellLifespan`（剩余持续回合数）
   - 调用：
     - `ok = engine.ExecuteAction(player_id, action_json)`
     - 此处 `player_id` 仍使用 `0/1`，C# 内部会映射成 `1/2` 并校验：
       - 当前行动棋子所属阵营是否与 `player_id` 一致；不一致则返回 `false`。
   - 内部行为（Env.ApplyAction + Env.EndTurn）：
     - 根据 `action_json` 构造内部 `actionSet`。
     - 对 `current_piece` 依次执行移动 / 攻击 / 施法逻辑，并推进延时法术。
     - 将 `current_piece` 从队列首移到队列末尾。
     - 判断是否有玩家全灭；如有则设置 `isGameOver = true`。
     - 若尚未结束且 `round_number >= max_rounds`，按双方总血量判定胜负或平局，并设置 `isGameOver = true`。
     - 写入当前回合的日志（供回放使用）。

4. **游戏结束判定**：
   - 每次 `ExecuteAction` 之后，通信组可以调用：
     - `engine.IsGameOver()`：返回 `true/false`。
     - 若返回 `true`，再调用 `engine.GetWinner()`：
       - 返回玩家 ID（内部 1/2），或 `-1` 表示平局。
   - 通信组可根据 Saiblo 协议，将结果打包成结束消息发送回平台。

### 3. 与旧 gRPC Broadcast 的对应关系

- 旧版 gRPC 中，`Env.step()` 在**回合初始化完成后**调用 `BroadcastGameState()`。
- 新版中，`BroadcastGameState()` 被移除，但语义等价为：
  - 在 `engine.NextTurn()` 之后、`engine.ExecuteAction()` 之前调用 `engine.GetStateJson()`。
- 因此：
  - **对 AI 来说，看见的始终是“本回合开始时”的局面**（行动点已重置，尚未行动），与旧实现一致。

### 4. 回放与调试

- 获取回放 JSON：
  - 调用：`replay_json = engine.GetReplayJson()`
  - 内容为 `LogConverter` 记录的完整对局数据（地图、单位、每回合动作与状态）。
- 注意：
  - 旧的 `LogConverter.save()` 仍会写 `log.json` 并阻塞在 `Console.ReadLine()`，在线上容器不建议直接调用。
  - 推荐通信组只使用 `GetReplayJson()`，在 Python 侧将 JSON 写文件或上传。

### 5. 典型 Python 伪代码示例

```python
# 伪代码，仅示意调用顺序
engine = GameEngine()
engine.Initialize("{}")

# 双方初始化棋子
for pid in [0, 1]:
    pieces = build_piece_args_for_player(pid)  # 返回 Python dict 列表
    pieces_json = json.dumps(pieces)
    assert engine.SetPlayerPieces(pid, pieces_json)

while not engine.IsGameOver():
    # 开始新回合
    engine.NextTurn()

    # 回合开始状态
    state_json = engine.GetStateJson()
    # 发送给 Saiblo / AI，这里省略

    # 从 AI 收到动作 JSON 字符串 action_json
    ok = engine.ExecuteAction(current_player_id, action_json)
    if not ok:
        # 处理非法动作或超时等情况
        ...

# 游戏结束
winner = engine.GetWinner()
replay_json = engine.GetReplayJson()
```


