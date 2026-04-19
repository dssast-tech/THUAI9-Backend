# 《开发测试》项目说明与开发分工

## 项目概述
本项目为 THUAI9 游戏项目的开发测试模块，旨在通过每回合可视化界面（基于 Tkinter）对游戏玩法（如法术攻击等）进行充分测试。测试逻辑内置于后端，不涉及前端通信，主要处理后端输出的 log 文件、json、proto 数据。

## 主要功能
- 数据解析：需要清楚了解项目的玩法设计（了解有哪些数据要传），对于后端部分输出的log文件，json、proto数据，做好 前端测试部分 需要的一些处理（如必要的类型转换）。
- 事件驱动：还可能涉及的与后端组对接，编写接口、事件响应等。
- 可视化界面：详细了解Tkinter可实现的功能，简单了解测试需求，设计测试界面的UI
- 交互逻辑：与可视化合作，详细了解并明确测试需求，基于测试界面设计合理的测试逻辑（例如回合切换、暂停等逻辑）。
- 功能测试：后阶段工作，在了解整个测试项目的逻辑与功能后，编写恰当的测试用例进行验证

## 开发分工
1. **事件驱动**（core/）：
   - 负责人：邓写意
   - 任务：编写 events.py，设计事件系统（如 EventBus），定义事件类型和处理机制，确保 UI 和 Logic 间的联系。

2. **可视化开发**（ui/）：
   - 负责人：陈正阳
   - 任务：设计 Tkinter UI，编写 main_ui.py 和 components.py，实现棋盘、角色、按钮、数据板等控件。目前最需要做的是界面设计的完善，按照设计图较为还原设计设想。其中右侧已经设计的按钮可以不改，使用窗口的形式实现行动选择（在ui文件夹中寻找“窗口”这个词的注释可以看到相关代码）

3. **交互逻辑**（logic/）：
   - 负责人：许瀚元
   - 任务：与可视化合作，编写 controller.py，实现回合切换、暂停等逻辑。目前紧急要做的是针对界面做信息呈现，例如角色信息的准确呈现等。
4. **功能测试**（tests/）：
   - 负责人：吴天成
   - 任务：编写 test_cases.py，验证各模块功能。

5. **工具函数**（utils/）：
   - 按需添加
   - 任务：编写 converter.py 等辅助函数。

## 项目结构
```
dev_test/
├── data/           # 测试数据文件
├── core/           # 事件驱动
│   ├── decoder.py
│   └── events.py
├── ui/             # 可视化界面
│   ├── main_ui.py
│   └── components.py
├── logic/          # 交互逻辑
│   └── controller.py
├── tests/          # 测试用例
│   └── test_cases.py
├── utils/          # 工具函数
│   └── converter.py
├── README.md       # 本文件
└── main.py         # 项目入口
```

## 使用方法
1. 进入目录：
   - `cd THUAI9-Backend-master/client/client_gRPC/dev_test`
2. 运行项目：
   - `python main.py`

### 运行流程
- 程序先由 `logic/controller.py` 调用 `core/data_provider.py` 的 `DataProvider.get_game_data(prefer_backend=True)`
- 如果后端可用（gRPC `SendInit` 成功），则使用真实后端数据；否则回退到 `data/log.json` 的 mock 数据
- 解码器 `core/decoder.py` 解析 JSON 并标准化数据结构（map、士兵、回合）
- `controller.run_loop()` 按回合输出日志，用于 UI 调试或后续可视化播报

### 模式与数据源切换
- 数据源：`main.py` 调用 `Controller.load_game_data(prefer_backend=True)`。
  - `True` 表示优先后端；异常时自动回落 mock。
  - 若稳定要强制 mock，可改为 `prefer_backend=False`。
- 游戏模式：`Controller.select_mode(mode)`
  - 支持 `manual`、`half-auto`、`auto`（当前仅框架逻辑，实际交互可扩展）

## 开发环境
- Tkinter（内置）
- 依赖：如有需要，请新建 requirements.txt 文件并列出（暂无）

## 注意事项
- 代码注释清晰。