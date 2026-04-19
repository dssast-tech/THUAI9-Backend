import json
from pathlib import Path
from typing import Any, Dict, Optional


class DataProvider:
    """数据提供器：优先加载本地玩法环境描述，必要时回退到 mock JSON 文件。"""

    def __init__(self, data_dir: str = None):
        base = data_dir or Path(__file__).resolve().parents[1]
        self.data_dir = Path(base) / "data"
        self.mock_sets_dir = self.data_dir / "mock_sets"
        self.backend_sets_dir = self.data_dir / "backend_sets"
        self.mock_path = self.data_dir / "log.json"
        self.default_board_file = str(self.backend_sets_dir / "backend_case_mountain_a.txt")

    @property
    def runtime_ready(self) -> bool:
        return True

    def close(self) -> None:
        # 本地运行模式无需显式关闭资源，保留接口供控制器统一调用。
        return

    def load_runtime_environment(self, board_file: Optional[str] = None) -> Dict[str, Any]:
        """返回本地玩法环境描述，用于在测试端直接创建并运行 Environment。"""
        chosen_board = board_file or self.default_board_file
        return {
            "source": "runtime_env",
            "engine": "client_python_env",
            "board_file": chosen_board,
            "local_mode": True,
            "if_log": 1,
        }

    def list_mock_datasets(self) -> list[str]:
        """返回可选 mock 数据集文件名列表。"""
        datasets = [self.mock_path.name]
        if self.mock_sets_dir.exists():
            for p in sorted(self.mock_sets_dir.glob("*.json")):
                datasets.append(p.name)
        return datasets

    def _resolve_mock_path(self, dataset_name: Optional[str] = None) -> Path:
        if not dataset_name or dataset_name == self.mock_path.name:
            return self.mock_path

        candidate = self.mock_sets_dir / dataset_name
        if candidate.exists():
            return candidate

        raise FileNotFoundError(f"未找到 mock 数据集: {dataset_name}")

    def load_from_mock(self, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """从本地 mock 数据文件加载游戏日志，供可视化开发使用。"""
        target = self._resolve_mock_path(dataset_name=dataset_name)
        if not target.exists():
            raise FileNotFoundError(f"Mock 数据文件未找到: {target}")

        with open(target, 'r', encoding='utf-8') as f:
            text = f.read()
            if not text.strip():
                raise ValueError("Mock 数据文件为空")
            payload = json.loads(text)
            payload["dataset"] = target.name
            return payload

    def get_game_data(
        self,
        prefer_runtime: bool = True,
        board_file: Optional[str] = None,
        mock_dataset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取游戏数据：优先本地玩法环境描述，否则回退 mock。"""
        if prefer_runtime:
            return self.load_runtime_environment(board_file=board_file)

        mock = self.load_from_mock(dataset_name=mock_dataset)
        mock["source"] = "mock"
        return mock
