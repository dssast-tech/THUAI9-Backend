import os
import sys
from typing import List, Optional, Dict, Any

# 需要让 dev_test 调用上层 client_gRPC 的 env, local_input, grpc_client 等模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from env import Environment
from local_input import InputMethodManager
from core.data_provider import DataProvider
from core.decoder import GameDataDecoder
from core.events import BasicEventLoop, EventBus, EventType


class DummyEnvironment(Environment):
    """真实环境对象：包含玩家、棋盘、回合等变量。"""
    """希望在main_ui.py中把用户交互输入打包成config字典"""
    
    def __init__(self, local_mode: bool = True, if_log: int = 1):
        super().__init__(local_mode=local_mode, if_log=if_log)
        self.custom_config: Dict[str, Any] = {}

    def apply_environment_config(self, config: Dict[str, Any]) -> None:
        """应用来自 UI 的环境配置。"""
        self.custom_config.update(config)

        board_config = config.get("board")
        if isinstance(board_config, dict):
            self.set_board_config(board_config)

        players_config = config.get("players")
        if isinstance(players_config, dict):
            for player_id, player_config in players_config.items():
                self.set_player_config(int(player_id), player_config)

        game_settings = config.get("game")
        if isinstance(game_settings, dict):
            self.set_game_settings(game_settings)

    def set_board_config(self, board_config: Dict[str, Any]) -> None:
        """设置棋盘相关参数，例如尺寸、障碍和初始布局。"""
        self.custom_config['board'] = board_config

        board_file = board_config.get('board_file')
        if board_file:
            try:
                self.board.init_from_file(board_file)
            except Exception as e:
                if self.if_log:
                    print(f"[DummyEnvironment] 读取棋盘文件失败: {e}")
                self.create_default_board()
            return

        if board_config.get('create_default', False):
            self.create_default_board()

        self.board.width = board_config.get('width', getattr(self.board, 'width', self.board.width))
        self.board.height = board_config.get('height', getattr(self.board, 'height', self.board.height))
        self.board.boarder = board_config.get('boarder', getattr(self.board, 'boarder', self.board.boarder))

        obstacles = board_config.get('obstacles', [])
        if hasattr(self.board, 'grid'):
            for obstacle in obstacles:
                if isinstance(obstacle, dict):
                    x = obstacle.get('x')
                    y = obstacle.get('y')
                elif isinstance(obstacle, (list, tuple)) and len(obstacle) >= 2:
                    x, y = obstacle[0], obstacle[1]
                else:
                    continue
                if isinstance(x, int) and isinstance(y, int) and 0 <= x < self.board.width and 0 <= y < self.board.height:
                    self.board.grid[x][y].state = -1

    def set_player_config(self, player_id: int, player_config: Dict[str, Any]) -> None:
        """设置指定玩家的参数，例如起始位置、属性、装备。"""
        self.custom_config.setdefault('players', {})
        self.custom_config['players'][str(player_id)] = player_config

        player = self.player1 if player_id == 1 else self.player2
        player.feature_total = player_config.get('feature_total', player.feature_total)
        player.piece_num = player_config.get('piece_num', player.piece_num)

    def set_game_settings(self, settings: Dict[str, Any]) -> None:
        """设置游戏运行参数，例如回合模式、是否记录日志等。"""
        self.custom_config['game'] = settings
        self.if_log = settings.get('if_log', self.if_log)
        self.mode = 0 if settings.get('local_mode', self.mode == 0) else 1

    def initialize_environment(self, board_file: Optional[str] = None) -> None:
        """初始化环境并应用当前配置。"""
        self.initialize(board_file=board_file)
        if self.custom_config:
            self.apply_environment_config(self.custom_config)

    def reset_to_defaults(self) -> None:
        """恢复环境默认配置。"""
        self.__init__(local_mode=self.mode == 0, if_log=self.if_log)

    def get_environment_snapshot(self) -> Dict[str, Any]:
        """获取当前环境状态快照，便于 UI 显示或调试。"""
        return {
            "mode": self.mode,
            "if_log": self.if_log,
            "round_number": self.round_number,
            "player1": self.player1.__dict__,
            "player2": self.player2.__dict__,
            "board": {
                "width": getattr(self.board, "width", None),
                "height": getattr(self.board, "height", None),
            },
            "custom_config": self.custom_config,
        }


class Controller:
    """游戏控制器：统一管理环境、数据和回合执行。"""

    def __init__(self, mode: str = "manual"):
        self.environment: Optional[DummyEnvironment] = None
        self.input_manager: Optional[InputMethodManager] = None
        self.game_mode: str = mode
        self.current_round: int = 0
        self.game_data: Optional[Dict[str, Any]] = None
        self.data_provider: DataProvider = DataProvider()
        self.runtime_source: str = "unknown"
        self.runtime_board_file: Optional[str] = None
        self.event_bus = EventBus()
        self.event_loop = BasicEventLoop(self.event_bus)

    def create_environment(self, local_mode: bool = True, if_log: int = 1) -> DummyEnvironment:
        self.environment = DummyEnvironment(local_mode=local_mode, if_log=if_log)
        self.input_manager = self.environment.input_manager
        return self.environment

    def _resolve_board_file(self, board_file: Optional[str] = None) -> str:
        """统一解析测试端使用的棋盘文件路径，避免回落到 env 内部默认值。"""
        if board_file:
            return str(board_file)
        if self.runtime_board_file:
            return str(self.runtime_board_file)
        return str(self.data_provider.default_board_file)

    def setup_environment(
        self,
        config: Optional[Dict[str, Any]] = None,
        board_file: Optional[str] = None,
        local_mode: bool = True,
        if_log: int = 1,
    ) -> DummyEnvironment:
        env = self.create_environment(local_mode=local_mode, if_log=if_log)
        if isinstance(config, dict):
            env.apply_environment_config(config)
        env.initialize_environment(board_file=self._resolve_board_file(board_file))
        return env

    def apply_environment_config(self, config: Dict[str, Any]) -> None:
        if self.environment is None:
            self.create_environment()
        self.environment.apply_environment_config(config)

    def initialize_environment(self, board_file: Optional[str] = None) -> None:
        if self.environment is None:
            self.create_environment()
        self.environment.initialize_environment(board_file=self._resolve_board_file(board_file))

    def reset_environment(self) -> None:
        if self.environment is None:
            self.create_environment()
            return

        local_mode = self.environment.mode == 0
        if_log = self.environment.if_log
        self.environment = DummyEnvironment(local_mode=local_mode, if_log=if_log)
        self.input_manager = self.environment.input_manager

    def set_function_input_methods(self, init_handler, action_handler) -> None:
        """为双方玩家统一设置函数式输入，便于 UI 或调试脚本接管输入。"""
        if self.environment is None:
            self.create_environment()
        if self.input_manager is None:
            raise RuntimeError("input_manager 未初始化")
        self.input_manager.set_function_input_method(1, init_handler, action_handler)
        self.input_manager.set_function_input_method(2, init_handler, action_handler)

    def get_environment_snapshot(self) -> Optional[Dict[str, Any]]:
        if self.environment is None:
            return None
        return self.environment.get_environment_snapshot()

    def list_mock_datasets(self) -> List[str]:
        return self.data_provider.list_mock_datasets()

    def load_game_data(
        self,
        prefer_runtime: bool = True,
        board_file: Optional[str] = None,
        mock_dataset: Optional[str] = None,
    ):
        raw_data = self.data_provider.get_game_data(
            prefer_runtime=prefer_runtime,
            board_file=board_file,
            mock_dataset=mock_dataset,
        )
        self.runtime_source = str(raw_data.get("source", "unknown")) if isinstance(raw_data, dict) else "unknown"

        if self.runtime_source == "runtime_env":
            self.runtime_board_file = self._resolve_board_file(raw_data.get("board_file"))
            self.create_environment(
                local_mode=bool(raw_data.get("local_mode", True)),
                if_log=int(raw_data.get("if_log", 1)),
            )
            self.game_data = raw_data
        else:
            # 切换到 mock 数据时，必须清空 runtime 环境，避免 run_round 误走 environment 分支。
            self.environment = None
            self.input_manager = None
            self.runtime_board_file = None
            if isinstance(raw_data, dict) and "map" not in raw_data:
                self.game_data = GameDataDecoder.decode(raw_data)
            else:
                self.game_data = raw_data

        self.current_round = 0
        self.event_bus.publish(
            EventType.GAME_LOADED,
            {"source": self.runtime_source, "mode": self.game_mode},
        )
        return self.game_data

    def select_mode(self, mode: str):
        if mode not in ("manual", "half-auto", "auto"):
            raise ValueError("mode must be manual/half-auto/auto")
        if mode in ("half-auto", "auto"):
            raise NotImplementedError("当前仅支持 manual，half-auto/auto 待开发")
        self.game_mode = mode

    def run_round(self):
        if self.environment is not None:
            if self.environment.is_game_over:
                self.event_bus.publish(EventType.GAME_OVER, {"source": "runtime_env"})
                print("当前环境已结束，停止执行")
                return False

            if self.environment.round_number == 0 and len(getattr(self.environment, 'action_queue', [])) == 0:
                self.environment.initialize_environment(board_file=self._resolve_board_file())

            self.event_bus.publish(
                EventType.ROUND_STARTED,
                {
                    "source": "runtime_env",
                    "round_number": int(self.environment.round_number + 1),
                },
            )

            self.environment.step()
            self.event_bus.publish(
                EventType.ROUND_FINISHED,
                {
                    "source": "runtime_env",
                    "round_number": int(self.environment.round_number),
                    "is_game_over": bool(self.environment.is_game_over),
                },
            )
            return not self.environment.is_game_over

        if self.game_data is None:
            raise RuntimeError("game_data not loaded")

        rounds = self.game_data.get("rounds", [])
        if self.current_round >= len(rounds):
            print("回合已结束，当前无更多回合")
            return False

        round_info = rounds[self.current_round]
        self.event_bus.publish(
            EventType.ROUND_STARTED,
            {
                "source": "mock",
                "round_number": int(round_info.get("roundNumber", self.current_round)),
            },
        )
        print(f"执行第 {round_info['roundNumber']} 回合，动作数量: {len(round_info['actions'])}")
        self.current_round += 1
        is_game_over = bool(self.current_round >= len(rounds))
        self.event_bus.publish(
            EventType.ROUND_FINISHED,
            {
                "source": "mock",
                "round_number": int(round_info.get("roundNumber", self.current_round)),
                "is_game_over": is_game_over,
            },
        )
        if is_game_over:
            self.event_bus.publish(EventType.GAME_OVER, {"source": "mock"})
        return not is_game_over

    def run_loop(self, max_rounds: Optional[int] = None):
        if self.environment is not None:
            print(f"开始执行本地玩法环境模式: {self.game_mode}")
            rounds_executed = self.event_loop.run_steps(self.run_round, max_steps=max_rounds)
            print(f"环境执行结束，回合数: {rounds_executed}")
            return

        print(f"开始执行模式: {self.game_mode}")
        self.event_loop.run_steps(self.run_round, max_steps=max_rounds)
        print("回合数据回放结束")


if __name__ == "__main__":
    ctrl = Controller(mode="manual")
    print("尝试优先本地玩法环境加载")
    try:
        game_data = ctrl.load_game_data(prefer_runtime=True)
        if ctrl.runtime_source == "runtime_env":
            print("本地玩法环境模式已就绪")
        else:
            print("加载游戏数据成功，回合数", len(game_data.get('rounds', [])))
    except Exception as e:
        print("本地玩法环境加载失败，降级到 mock 数据：", e)
        game_data = ctrl.load_game_data(prefer_runtime=False)

    ctrl.run_loop()
