from utils import *
from dataclasses import dataclass
from typing import List, Optional


class Player:
    def __init__(self):
        self.id = -1
        self.pieces = []
class Piece:
    def __init__(self):
        self.health = 0
        self.max_health = 0
        self.physical_resist = 0
        self.magic_resist = 0
        self.physical_damage = 0
        self.magic_damage = 0
        self.action_points = 0
        self.max_action_points = 0
        self.spell_slots = 0
        self.max_spell_slots = 0
        self.movement = 0.0
        self.max_movement = 0.0
        self.strength = 0
        self.dexterity = 0
        self.intelligence = 0
        self.position = Point(0, 0)
        self.height = 0
        self.attack_range = 0
        self.spell_list = []
        self.team = 0
        self.queue_index = 0
        self.is_alive = True
        self.is_in_turn = False
        self.is_dying = False
        self.spell_range = 0.0


@dataclass
class Cell:
    """
    棋盘格子类
    state: 0-空地, 1-可行走, 2-占据, -1-禁止
    player_id: -1-无人, 1-玩家1, 2-玩家2
    piece_id: -1-无棋子, 其他值为棋子ID
    """
    state: int = 1  # 默认为可行走
    player_id: int = -1  # 默认无人
    piece_id: int = -1  # 默认无棋子


class Board:
    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height
        # 使用Cell对象初始化网格
        self.grid = [[Cell() for _ in range(height)] for _ in range(width)]
        self.height_map = [[0 for _ in range(height)] for _ in range(width)]
        self.boarder = height // 2  # 分界线为高度的一半

    def is_within_bounds(self, p: Point) -> bool:
        """检查位置是否在棋盘范围内"""
        return 0 <= p.x < self.width and 0 <= p.y < self.height

    def is_occupied(self, p: Point) -> bool:
        """检查位置是否被占据"""
        return self.grid[p.x][p.y].state == 2

    def get_height(self, p: Point) -> int:
        """获取指定位置的高度"""
        return self.height_map[p.x][p.y]


class Env:
    def __init__(self):
        self.action_queue = []
        self.current_piece = None
        self.round_number = 0
        self.delayed_spells = []
        self.player1 = None
        self.player2 = None
        self.board = Board()
        self.is_game_over = False

class InitGameMessage:
    """游戏初始化消息"""
    def __init__(self):
        self.piece_cnt: int = 0  # 棋子数量
        self.id: int = 0  # 玩家ID
        self.board: Optional[Board] = None  # 棋盘


class PieceArg:
    """棋子参数类"""
    def __init__(self):
        self.strength: int = 0  # 力量
        self.intelligence: int = 0  # 智力
        self.dexterity: int = 0  # 敏捷
        self.equip: Point = Point()  # 装备 (weapon, armor)
        self.pos: Point = Point()  # 位置


class InitPolicyMessage:
    """初始化策略消息"""
    def __init__(self):
        self.piece_args: List[PieceArg] = []


class GameMessage:
    """游戏状态消息"""
    def __init__(self):
        self.action_queue: List[Piece] = []  # 棋子的行动队列
        self.current_piece: Optional[Piece] = None  # 当前行动的棋子
        self.round_number: int = 0  # 当前回合数
        self.delayed_spells: List[SpellContext] = []  # 延时法术列表
        self.player1: Optional[Player] = None  # 玩家1
        self.player2: Optional[Player] = None  # 玩家2
        self.board: Optional[Board] = None  # 棋盘


class PolicyMessage:
    """策略消息"""
    def __init__(self):
        self.action_set: Optional[ActionSet] = None

    def __post_init__(self):
        """确保action_set有默认值"""
        if self.action_set is None:
            self.action_set = ActionSet()
