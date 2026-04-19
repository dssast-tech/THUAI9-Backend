## dev_test 终端调试简要教程

本教程用于快速验证：测试端是否已成功加载 client 玩法环境并能推进回合。

### 1. 推荐方式（最简单）

使用一键脚本：

- 脚本位置：`dev_test/tests/debug_tests/run_runtime_debug.bat`
- 默认执行 2 回合（可传参数修改回合数）

#### 在工作区根目录运行

```powershell
& ".\THUAI9-Backend-master\client\client_gRPC\dev_test\tests\debug_tests\run_runtime_debug.bat" 2
```

#### 在 client_gRPC 目录运行

```powershell
& ".\dev_test\tests\debug_tests\run_runtime_debug.bat" 2
```

### 2. 直接运行 Python 调试脚本（备用）

```powershell
& "e:/Dushi_SAT/THUAI9_Test/local/local devel/3.28.001/THUAI9-Test-Viz/.venv/Scripts/python.exe" \
	"THUAI9-Backend-master/client/client_gRPC/dev_test/debug_backend_bridge.py" --steps 2
```

### 3. 如何判断调试成功

出现以下信息可视为通过：

1. `runtime environment initialized`
2. 棋盘尺寸输出（例如 `width: 20, height: 20`）
3. 至少 1 条 `step` 输出（例如 `step=1`, `round=1`）
4. 进程正常结束（exit code = 0）

### 4. 常见问题与解决

#### 问题 A：找不到 bat 文件

现象：`CommandNotFoundException`

原因：当前目录和命令路径不匹配。

解决：使用上面第 1 节中与你当前目录对应的命令。

#### 问题 B：main.py 运行后卡在输入

现象：要求输入属性、装备、坐标。

原因：`main.py` 是手动流程，设计上会等待玩家输入。

解决：调试联通优先使用 `run_runtime_debug.bat`（自动动作，不需要人工输入）。

#### 问题 C：路径重复（最常见）

现象：路径里出现两次 `THUAI9-Backend-master/client/client_gRPC`。

原因：已经在该目录下，又写了完整相对子路径。

解决：在 `client_gRPC` 目录运行时，请使用短路径：

```powershell
& ".\dev_test\tests\debug_tests\run_runtime_debug.bat" 2
```



