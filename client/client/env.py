import numpy as np
import random
import math
import os
import copy
from colorama import init, Fore, Back, Style
init(autoreset=True)  # 初始化 colorama
from typing import List, Tuple, Optional, Dict, Callable
from dataclasses import dataclass
from utils import *


class Cell:
    """棋盘格子类"""
    def __init__(self, state: int = 1, player_id: int = -1, piece_id: int = -1):
        self.state = state  # 0: 空地, 1: 可行走, 2: 占据, -1: 禁止
        self.player_id = player_id  # 0: 无人, 1: 玩家1, 2: 玩家2
        self.piece_id = piece_id  # -1: 无棋子, 其他值为棋子ID


class Piece:
    """棋子类"""
    def __init__(self):
        self.if_log = 0

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
        self.id = 0
        self.type = ""
        self.strength = 0
        self.dexterity = 0
        self.intelligence = 0
        self.position = Point(0, 0)
        self.height = 0
        self.attack_range = 0
        self.spell_list = []
        self.death_round = -1
        self.team = 0
        self.queue_index = 0
        self.is_alive = True
        self.is_in_turn = False
        self.is_dying = False
        self.spell_range = 0.0

    def receive_damage(self, damage: int, damage_type: str):
        """接收伤害"""
        if damage_type == "physical":
            damage = max(0, damage - self.physical_resist)
        elif damage_type == "magic":
            damage = max(0, damage - self.magic_resist)
        else:
            raise ValueError("Invalid damage type")
        
        self.health -= damage
        if self.if_log:
            print(f"[DEBUG] damage after resist: {damage}")

    def death_check(self):
        """死亡检查"""
        return self.is_alive

    def get_accessor(self):
        """获取访问器"""
        return PieceAccessor(self)

    def set_action_points(self, action_points: int):
        """设置行动点"""
        self.action_points = action_points

    def get_action_points(self):
        """获取行动点"""
        return self.action_points


class PieceAccessor:
    """棋子访问器类"""
    def __init__(self, piece: Piece):
        self.piece = piece

    def set_health_to(self, value: int):
        self.piece.health = value

    def change_health_by(self, delta: int):
        self.piece.health += delta

    def set_max_health_to(self, value: int):
        self.piece.max_health = value

    def set_physical_resist_to(self, value: int):
        self.piece.physical_resist = value

    def set_magic_resist_to(self, value: int):
        self.piece.magic_resist = value

    def set_physical_damage_to(self, value: int):
        self.piece.physical_damage = value

    def set_magic_damage_to(self, value: int):
        self.piece.magic_damage = value

    def set_max_movement_to(self, value: float):
        self.piece.max_movement = value

    def set_max_movement_by(self, value: float):
        self.piece.max_movement += value

    def set_movement_to(self, value: float):
        self.piece.movement = value

    def set_attack_range_to(self, value: int):
        self.piece.attack_range = value

    def set_max_action_points_to(self, value: int):
        self.piece.max_action_points = value

    def set_max_spell_slots_to(self, value: int):
        self.piece.max_spell_slots = value

    def set_team_to(self, value: int):
        self.piece.team = value

    def set_range_to(self, value: int):
        self.piece.attack_range = value

    def set_max_action_points(self):
        if self.piece.strength <= 13:
            self.set_max_action_points_to(1)
        elif self.piece.strength <= 21:
            self.set_max_action_points_to(2)
        else:
            self.set_max_action_points_to(3)

    def set_max_spell_slots(self):
        if self.piece.intelligence <= 3:
            self.set_max_spell_slots_to(1)
        elif self.piece.intelligence <= 7:
            self.set_max_spell_slots_to(2)
        elif self.piece.intelligence <= 12:
            self.set_max_spell_slots_to(3)
        elif self.piece.intelligence <= 16:
            self.set_max_spell_slots_to(5)
        elif self.piece.intelligence <= 21:
            self.set_max_spell_slots_to(8)
        else:
            self.set_max_spell_slots_to(9)

    def set_strength_to(self, value: int):
        if value < 0:
            raise ValueError("Strength cannot be negative")
        self.piece.strength = value

    def set_dexterity_to(self, value: int):
        if value < 0:
            raise ValueError("Dexterity cannot be negative")
        self.piece.dexterity = value

    def set_intelligence_to(self, value: int):
        if value < 0:
            raise ValueError("Intelligence cannot be negative")
        self.piece.intelligence = value

    def set_type_to(self, value: int):
        if value < 0:
            raise ValueError("Type cannot be negative")
        elif value == 1 or value == 2:
            self.piece.type = "Warrior"
        elif value == 4:
            self.piece.type = "Mage"
        elif value == 3:
            self.piece.type = "Archer"
        else:
            raise ValueError("Type out of range")

    def set_action_points_to(self, value: int):
        self.piece.action_points = value

    def change_action_points_by(self, delta: int):
        self.piece.action_points += delta

    def set_spell_slots_to(self, value: int):
        self.piece.spell_slots = value

    def change_spell_slots_by(self, delta: int):
        self.piece.spell_slots += delta

    def set_alive(self, value: bool):
        self.piece.is_alive = value

    def set_dying(self, value: bool):
        self.piece.is_dying = value

    def set_position(self, new_pos: Point):
        self.piece.position = new_pos

    def set_height_to(self, value: int):
        self.piece.height = value

    def set_magic_resist_by(self, value: int):
        self.piece.magic_resist -= value

    def set_physic_resist_by(self, value: int):
        self.piece.physical_resist -= value

    def strength_adjustment(self):
        if self.piece.strength <= 7:
            return 1
        elif self.piece.strength <= 13:
            return 2
        elif self.piece.strength <= 16:
            return 3
        else:
            return 4

    def dexterity_adjustment(self):
        if self.piece.dexterity <= 7:
            return 1
        elif self.piece.dexterity <= 13:
            return 2
        elif self.piece.dexterity <= 16:
            return 3
        else:
            return 4

    def intelligence_adjustment(self):
        if self.piece.intelligence <= 7:
            return 1
        elif self.piece.intelligence <= 13:
            return 2
        elif self.piece.intelligence <= 16:
            return 3
        else:
            return 4


class Player:
    """玩家类"""
    PIECE_CNT = 1
    
    def __init__(self):
        self.id = 0
        self.pieces = np.array([], dtype=object)
        self.feature_total = 30
        self.piece_num = 0

    def set_weapon(self, weapon: int, piece: Piece):
        """设置武器"""
        accessor = piece.get_accessor()
        accessor.set_type_to(weapon)
        
        if weapon == 1:
            accessor.set_physical_damage_to(18)
            accessor.set_magic_damage_to(0)
            accessor.set_range_to(5)
        elif weapon == 2:
            accessor.set_physical_damage_to(24)
            accessor.set_magic_damage_to(0)
            accessor.set_range_to(3)
        elif weapon == 3:
            accessor.set_physical_damage_to(16)
            accessor.set_magic_damage_to(0)
            accessor.set_range_to(9)
        elif weapon == 4:
            accessor.set_physical_damage_to(0)
            accessor.set_magic_damage_to(22)
            accessor.set_range_to(12)
        else:
            raise ValueError("Wrong weapon type!")

    def set_armor(self, armor: int, piece: Piece):
        """设置防具"""
        accessor = piece.get_accessor()
        
        if armor == 1:
            accessor.set_physical_resist_to(8)
            accessor.set_magic_resist_to(10)
            accessor.set_max_movement_by(3)
        elif armor == 2:
            accessor.set_physical_resist_to(15)
            accessor.set_magic_resist_to(13)
        elif armor == 3:
            accessor.set_physical_resist_to(23)
            accessor.set_magic_resist_to(17)
            accessor.set_max_movement_by(-3)
        else:
            raise ValueError("Wrong armor type!")

    def local_init(self, board, player_id: int):
        """本地初始化"""
        pieces_list = []
        
        for i in range(self.PIECE_CNT):
            print(f"现在为棋手 {player_id} 的第 {i + 1} 个棋子初始化")
            piece = Piece()
            pieces_list.append(piece)
            
            accessor = piece.get_accessor()
            accessor.set_team_to(player_id)
            
            features = self.init_input(board, player_id)
            self.piece_num += 1
            
            strength, dexterity, intelligence = features[0], features[1], features[2]
            accessor.set_strength_to(strength)
            accessor.set_dexterity_to(dexterity)
            accessor.set_intelligence_to(intelligence)
            
            weapon, armor = features[3], features[4]
            
            accessor.set_max_health_to(30 + strength * 2)
            accessor.set_health_to(piece.max_health)
            
            accessor.set_max_action_points()
            accessor.set_action_points_to(piece.max_action_points)
            
            accessor.set_max_spell_slots()
            accessor.set_spell_slots_to(piece.max_spell_slots)
            
            accessor.set_max_movement_to(dexterity + 0.5 * strength + 10)
            accessor.set_movement_to(piece.max_movement)
            
            self.set_weapon(weapon, piece)
            self.set_armor(armor, piece)
            
            position = Point(features[5], features[6])
            accessor.set_position(position)
            accessor.set_height_to(board.height_map[position.x][position.y])
            
        self.pieces = np.array(pieces_list, dtype=object)

    def init_input(self, board, player_id: int):
        """初始化输入"""
        initialization_set = []
        try:
            # 属性输入
            while True:
                print(f"为棋子输入属性分配，格式为：力量 敏捷 智力 总和不超过30")
                user_input = input()
                if user_input:
                    try:
                        inputs = user_input.split()
                        nums = [int(x) for x in inputs]
                        if len(nums) != 3:
                            print("输入的整数不是3个")
                            continue
                        
                        strength, dexterity, intelligence = nums
                        
                        if any(n < 0 for n in nums):
                            print("输入的整数不能为负数！")
                            continue
                            
                        if sum(nums) > 30:
                            print("输入的整数之和多于30！")
                            continue
                            
                        initialization_set.extend(nums)
                        break
                    except ValueError:
                        print("输入的不是整数")
                        continue

            # 显示武器防具表
            print("\n武器防具表展示如下：")
            print("武器:         物伤值      法伤值     范围")
            print("1~长剑       18           0         5")
            print("2~短剑       24           0         3")
            print("3~弓         16           0         9")
            print("4~法杖        0           22        12")
            print("防具:         物豁免值      法豁免值   行动力影响")
            print("1~轻甲         8            10        +3")
            print("2~中甲         15           13        0")
            print("3~重甲         23           17        -3")

            # 装备选择
            while True:
                print("\n现在输入武器和防具，格式为：武器类型(1-4) 防具类型(1-3)")
                user_input = input()
                if user_input:
                    try:
                        inputs = user_input.split()
                        if len(inputs) != 2:
                            print("输入的整数不是2个")
                            continue
                            
                        weapon, armor = map(int, inputs)
                        
                        if not (1 <= weapon <= 4 and 1 <= armor <= 3):
                            print("输入的整数不在范围里！")
                            continue
                            
                        if weapon == 4 and armor != 1:
                            print("法杖只能配轻甲！")
                            continue
                            
                        initialization_set.extend([weapon, armor])
                        break
                    except ValueError:
                        print("输入的不是整数")
                        continue

            # 位置选择
            while True:
                rows = board.height
                cols = board.width
                boarder = board.boarder
                
                print("\n现在输入棋子初始坐标，格式为：x y")
                user_input = input()
                if user_input:
                    try:
                        inputs = user_input.split()
                        if len(inputs) != 2:
                            print("输入的整数不是2个")
                            continue
                            
                        x, y = map(int, inputs)
                        
                        if not (0 <= x < cols and 0 <= y < rows):
                            print("输入的整数超过范围！")
                            continue
                            
                        if board.grid[x][y].state != 1:
                            print("输入的坐标状态为不可占据!")
                            continue
                            
                        # 检查边界条件
                        if player_id == 1 and y >= boarder:
                            print(f"玩家1的棋子必须在边界线{boarder}以下!")
                            continue
                        elif player_id == 2 and y <= boarder:
                            print(f"玩家2的棋子必须在边界线{boarder}以上!")
                            continue
                            
                        # 检查是否与已添加的棋子位置冲突
                        is_valid = True
                        for existing_piece in self.pieces:
                            if x == existing_piece.position.x and y == existing_piece.position.y:
                                print("输入的坐标与已有棋子重合！")
                                is_valid = False
                                break
                                
                        if not is_valid:
                            continue
                            
                        initialization_set.extend([x, y])
                        break
                    except ValueError:
                        print("输入的不是整数")
                        continue

        except Exception as e:
            print(f"输入错误：{e}")
            raise

        return initialization_set


class Board:
    """棋盘类"""
    def __init__(self, if_log: int = 1):
        self.width = 0
        self.height = 0
        self.grid = None  # 2D array of Cell
        self.height_map = None  # 2D array of int
        self.boarder = 0
        self.if_log = if_log  # 日志控制，1启用，0禁用

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def valid_target(self, piece: Piece, movement: float):
        """获取有效目标位置，使用改进的 Dijkstra 算法一次性计算所有可达点
        
        Args:
            piece: 要移动的棋子
            movement: 可用的移动力
            
        Returns:
            list: 二维数组，表示每个位置的移动消耗。-1表示不可到达
        """
        from queue import PriorityQueue
        
        # 初始化距离矩阵
        mask = [[-1 for _ in range(self.height)] for _ in range(self.width)]
        start = piece.position
        
        # 优化：使用优先队列的 Dijkstra，一次性计算所有可达点
        frontier = PriorityQueue()
        frontier.put((0, (start.x, start.y)))
        
        # 记录已访问的点
        visited = set()
        mask[start.x][start.y] = 0
        
        while not frontier.empty():
            current_cost, current_pos = frontier.get()
            current_x, current_y = current_pos
            
            # 如果已经处理过这个点，跳过
            if current_pos in visited:
                continue
            visited.add(current_pos)
            
            # 如果当前代价已经超过移动力，不需要继续扩展
            if current_cost > movement:
                continue
            
            # 获取相邻点
            current_point = Point(current_x, current_y)
            for next_pos in self.get_neighbors(current_point):
                next_x, next_y = next_pos.x, next_pos.y
                next_pos_tuple = (next_x, next_y)
                
                # 如果已访问过或格子被占据，跳过
                if next_pos_tuple in visited or self.grid[next_x][next_y].state != 1:
                    continue
                
                # 计算新的代价（考虑高度差）
                height_diff = self.height_map[next_x][next_y] - self.height_map[current_x][current_y]
                move_cost = 1 + max(0, height_diff)
                new_cost = current_cost + move_cost
                
                # 如果新代价在移动力范围内且比已知代价更优
                if new_cost <= movement and (mask[next_x][next_y] == -1 or new_cost < mask[next_x][next_y]):
                    mask[next_x][next_y] = new_cost
                    frontier.put((new_cost, next_pos_tuple))
        
        return mask

    def move_piece(self, piece: Piece, to: Point, movement: float):
        """移动棋子
        
        Args:
            piece: 要移动的棋子
            to: 目标位置
            movement: 可用的移动力
            
        Returns:
            tuple: (path, success) 其中path是移动路径（如果成功），success是布尔值表示是否成功
        """
        if not self.is_within_bounds(to):
            if self.if_log:
                print(f"目标位置({to.x}, {to.y})超出地图大小")
            return None, False
            
        if self.grid[to.x][to.y].state != 1:
            if self.if_log:
                print(f"目标位置({to.x}, {to.y})被占据")
            return None, False

        path, cost = self.find_shortest_path(piece, piece.position, to, movement)
        if path is None or cost > movement:
            if self.if_log:
                print(f"目标位置({to.x}, {to.y})不可达或超出移动范围")
            return None, False

        # 保存原始位置以便回滚
        old_x, old_y = piece.position.x, piece.position.y
        old_height = piece.height

        try:
            # 更新原始格子状态
            self.grid[old_x][old_y].state = 1
            self.grid[old_x][old_y].player_id = -1
            self.grid[old_x][old_y].piece_id = -1
            
            # 更新目标格子状态
            self.grid[to.x][to.y].state = 2
            self.grid[to.x][to.y].player_id = piece.team
            self.grid[to.x][to.y].piece_id = piece.id
            
            # 更新棋子位置和高度
            piece.position = to
            piece.height = self.height_map[to.x][to.y]

            
            return path, True
            
        except Exception as e:
            # 发生错误时回滚
            if self.if_log:
                print(f"移动过程中发生错误: {e}")
            self.grid[old_x][old_y].state = 2
            self.grid[old_x][old_y].player_id = piece.team
            self.grid[old_x][old_y].piece_id = piece.id
            
            self.grid[to.x][to.y].state = 1
            self.grid[to.x][to.y].player_id = -1
            self.grid[to.x][to.y].piece_id = -1
            
            piece.position = Point(old_x, old_y)
            piece.height = old_height
            return None, False

    def is_occupied(self, point: Point):
        """检查位置是否被占据"""
        return self.grid[point.x][point.y].state == 2

    def get_height(self, point: Point):
        """获取位置高度"""
        return self.height_map[point.x][point.y]

    def remove_piece(self, piece: Piece):
        """移除棋子"""
        x, y = piece.position.x, piece.position.y
        self.grid[x][y].state = 1
        self.grid[x][y].player_id = -1
        self.grid[x][y].piece_id = -1

    def is_within_bounds(self, point: Point):
        """检查位置是否在边界内"""
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def get_neighbors(self, point: Point):
        """获取邻居位置"""
        neighbors = [
            Point(point.x - 1, point.y),
            Point(point.x + 1, point.y),
            Point(point.x, point.y - 1),
            Point(point.x, point.y + 1)
        ]
        return [n for n in neighbors if self.is_within_bounds(n) and self.grid[n.x][n.y].state == 1]

    def find_shortest_path(self, piece: Piece, start: Point, goal: Point, movement: float):
        """寻找最短路径"""
        from queue import PriorityQueue
        
        came_from = {}
        cost_so_far = {}
        frontier = PriorityQueue()
        
        frontier.put((0, (start.x, start.y)))  # 存储坐标元组而不是Point对象
        came_from[(start.x, start.y)] = (start.x, start.y)
        cost_so_far[(start.x, start.y)] = 0
        
        while not frontier.empty():
            _, current_pos = frontier.get()  # 正确解包优先队列元素
            current_x, current_y = current_pos
            
            if current_x == goal.x and current_y == goal.y:
                break
                
            current_point = Point(current_x, current_y)
            for next_pos in self.get_neighbors(current_point):
                next_pos_tuple = (next_pos.x, next_pos.y)
                height_diff = self.height_map[next_pos.x][next_pos.y] - self.height_map[current_x][current_y]
                move_cost = 1 + max(0, height_diff)
                new_cost = cost_so_far[current_pos] + move_cost
                
                if new_cost > movement:
                    continue
                    
                if next_pos_tuple not in cost_so_far or new_cost < cost_so_far[next_pos_tuple]:
                    cost_so_far[next_pos_tuple] = new_cost
                    priority = new_cost
                    frontier.put((priority, next_pos_tuple))
                    came_from[next_pos_tuple] = current_pos
        
        goal_tuple = (goal.x, goal.y)
        if goal_tuple not in came_from:
            return None, 0
            
        path = []
        temp = goal_tuple
        start_tuple = (start.x, start.y)
        
        while temp != start_tuple:
            path.append(Point(temp[0], temp[1]))
            temp = came_from[temp]
            
        path.reverse()
        return path, cost_so_far[goal_tuple]

    def init_from_file(self, file_path: str):
        """从文件初始化棋盘"""
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        dimensions = lines[0].strip().split()
        self.width = int(dimensions[0])
        self.height = int(dimensions[1])
        print(f"Width: {self.width}, Height: {self.height}")
        
        self.grid = np.array([[Cell() for _ in range(self.height)] for _ in range(self.width)], dtype=object)
        self.height_map = np.zeros((self.width, self.height), dtype=int)
        self.boarder = self.height // 2
        
        line_index = 2
        
        # 读取grid
        for y in range(self.height):
            values = lines[line_index].strip().split(',')
            for x in range(self.width):
                self.grid[x][y].state = int(values[x].strip())
            line_index += 1
        
        line_index += 1
        
        # 初始化player_id和piece_id
        for x in range(self.width):
            for y in range(self.height):
                self.grid[x][y].player_id = -1
                self.grid[x][y].piece_id = -1
        
        # 读取height_map
        for y in range(self.height):
            values = lines[line_index].strip().split(',')
            for x in range(self.width):
                self.height_map[x][y] = int(values[x].strip())
            line_index += 1

    def init_pieces_location(self, player1_pieces: List[Piece], player2_pieces: List[Piece]):
        # 检查玩家1的棋子是否都在边界线以下
        for piece in player1_pieces:
            if piece.position.y >= self.boarder:
                raise ValueError(f"玩家1的棋子(ID:{piece.id})位置y={piece.position.y}不合法，必须小于边界线{self.boarder}")
            self.grid[piece.position.x][piece.position.y].state = 2
            self.grid[piece.position.x][piece.position.y].player_id = piece.team
            self.grid[piece.position.x][piece.position.y].piece_id = piece.id
            
        # 检查玩家2的棋子是否都在边界线以上
        for piece in player2_pieces:
            if piece.position.y <= self.boarder:
                raise ValueError(f"玩家2的棋子(ID:{piece.id})位置y={piece.position.y}不合法，必须大于边界线{self.boarder}")
            self.grid[piece.position.x][piece.position.y].state = 2
            self.grid[piece.position.x][piece.position.y].player_id = piece.team
            self.grid[piece.position.x][piece.position.y].piece_id = piece.id


class Spell:
    """法术类"""
    def __init__(self, name: str = "", effect_type: str = "", base_value: int = 0, is_locking_spell: bool = False):
        self.name = name
        self.effect_type = effect_type
        self.base_value = base_value
        self.is_locking_spell = is_locking_spell


class Area:
    """区域类"""
    def __init__(self, x: int = 0, y: int = 0, radius: int = 0):
        self.x = x
        self.y = y
        self.radius = radius

    def contains(self, point: Point):
        """检查点是否在区域内"""
        distance = math.sqrt((point.x - self.x) ** 2 + (point.y - self.y) ** 2)
        return distance <= self.radius


class SpellContext:
    """法术上下文类"""
    def __init__(self):
        self.caster = None
        self.target = None
        self.spell = None
        self.target_area = None
        self.is_delay_spell = False
        self.delay_add = False
        self.spell_cost = 0
        self.spell_lifespan = 0
        self.hit_pieces = []


class AttackContext:
    """攻击上下文类"""
    def __init__(self):
        self.attacker = None
        self.target = None
        self.damage_dealt = 0


class GameState:
    """游戏状态类"""
    def __init__(self):
        self.action_queue = []
        self.current_piece = None
        self.round_number = 0
        self.delayed_spells = []
        self.player1 = None
        self.player2 = None
        self.board = None
        self.is_game_over = False
        self.new_dead_this_round = np.array([], dtype=object)
        self.last_round_dead_pieces = np.array([], dtype=object)


class InitGameMessage:
    """游戏初始化消息"""
    def __init__(self):
        self.piece_cnt: int = 0  # 棋子数量
        self.id: int = 0  # 玩家ID
        self.board: Optional[Board] = None  # 棋盘



from local_input import InputMethodManager, ConsoleInputMethod, FunctionInputMethod, RemoteInputMethod


class Environment:
    """环境类 - 游戏核心控制器"""
    def __init__(self, local_mode: bool = True, if_log: int = 1):
        self.mode = 0 if local_mode else 1  # 0 for local, 1 for remote
        self.if_log = if_log  # 日志控制，1启用，0禁用
        self.input_manager = InputMethodManager(self)
        self.action_queue = []
        self.current_piece = None
        self.round_number = 0
        self.delayed_spells = []
        self.player1 = Player()
        self.player2 = Player()
        self.board = Board(if_log=if_log)
        self.is_game_over = False
        self.new_dead_this_round = np.array([], dtype=object)
        self.last_round_dead_pieces = np.array([], dtype=object)

    def roll_dice(self, n: int, sides: int):
        """投掷骰子"""
        return random.randint(1, sides)

    def step_modified_func(self, num: int):
        """步进修改函数"""
        if num <= 10:
            return 1
        elif num <= 20:
            return 2
        elif num <= 30:
            return 3
        else:
            return 4

    def initialize(self, board_file: str = "./BoardCase/case1.txt"):
        """初始化游戏"""
        if board_file is None:
            # 使用默认棋盘文件
            board_file = os.path.join(os.path.dirname(__file__), "..", "server", "server", "BoardCase", "case1.txt")
            if not os.path.exists(board_file):
                # 创建默认棋盘
                self.create_default_board()
            else:
                self.board.init_from_file(board_file)
        else:
            self.board.init_from_file(board_file)

        self.player1.id = 1
        self.player2.id = 2

        # 创建初始化消息
        init_message1 = InitGameMessage()
        init_message1.piece_cnt = Player.PIECE_CNT
        init_message1.id = 1
        init_message1.board = self.board

        init_message2 = InitGameMessage()
        init_message2.piece_cnt = Player.PIECE_CNT
        init_message2.id = 2
        init_message2.board = self.board

        # 使用输入管理器处理初始化
        init_policy1 = self.input_manager.handle_init_input(1, init_message1)
        init_policy2 = self.input_manager.handle_init_input(2, init_message2)

        # 应用初始化策略
        self.apply_init_policy(1, init_policy1)
        self.apply_init_policy(2, init_policy2)

        # 初始化行动队列
        self.action_queue = np.array([], dtype=object)
        self.delayed_spells = np.array([], dtype=object)
        self.is_game_over = False
        self.round_number = 0
        self.new_dead_this_round = np.array([], dtype=object)

        # 计算优先级
        piece_priority = {}
        
        for piece in self.player1.pieces:
            priority = self.roll_dice(1, 20) + piece.dexterity
            piece_priority[piece] = priority
            
        for piece in self.player2.pieces:
            priority = self.roll_dice(1, 20) + piece.dexterity
            piece_priority[piece] = priority

        # 按优先级排序
        sorted_pieces = sorted(piece_priority.keys(), key=lambda x: -piece_priority[x])
        self.action_queue = np.array(sorted_pieces, dtype=object)
        
        for i, piece in enumerate(self.action_queue):
            piece.id = i

        self.board.init_pieces_location(self.player1.pieces, self.player2.pieces)
        self.last_round_dead_pieces = np.array([], dtype=object)

    def apply_init_policy(self, player_id: int, policy: InitPolicyMessage):
        """应用初始化策略"""
        player = self.player1 if player_id == 1 else self.player2
        pieces_list = []
        
        for piece_arg in policy.piece_args:
            piece = Piece()
            pieces_list.append(piece)
            
            accessor = piece.get_accessor()
            accessor.set_team_to(player_id)
            
            # 设置属性
            accessor.set_strength_to(piece_arg.strength)
            accessor.set_dexterity_to(piece_arg.dexterity)
            accessor.set_intelligence_to(piece_arg.intelligence)
            
            # 设置装备
            player.set_weapon(piece_arg.equip.x, piece)  # x为武器类型
            player.set_armor(piece_arg.equip.y, piece)   # y为防具类型
            
            # 设置位置
            accessor.set_position(piece_arg.pos)
            accessor.set_height_to(self.board.height_map[piece_arg.pos.x][piece_arg.pos.y])
            
            # 设置其他属性
            accessor.set_max_health_to(30 + piece_arg.strength * 2)
            accessor.set_health_to(piece.max_health)
            accessor.set_max_action_points()
            accessor.set_action_points_to(piece.max_action_points)
            accessor.set_max_spell_slots()
            accessor.set_spell_slots_to(piece.max_spell_slots)
            accessor.set_max_movement_to(piece_arg.dexterity + 0.5 * piece_arg.strength + 10)
            accessor.set_movement_to(piece.max_movement)
            
        player.pieces = np.array(pieces_list, dtype=object)
        player.piece_num = len(pieces_list)

    def create_default_board(self):
        """创建默认棋盘"""
        self.board.width = 10
        self.board.height = 10
        self.board.boarder = 5
        
        # 创建默认网格
        self.board.grid = [[Cell(1) for _ in range(self.board.height)] for _ in range(self.board.width)]
        self.board.height_map = [[0 for _ in range(self.board.height)] for _ in range(self.board.width)]
        
        # 设置一些障碍物
        for i in range(2, 8):
            self.board.grid[i][5].state = -1
            self.board.height_map[i][5] = 3

    def is_in_attack_range(self, attacker: Piece, target: Piece):
        """检查是否在攻击范围内"""
        distance = math.sqrt(
            (attacker.position.x - target.position.x) ** 2 +
            (attacker.position.y - target.position.y) ** 2
        )
        return distance <= attacker.attack_range

    def calculate_advantage_value(self, attacker: Piece, target: Piece):
        """计算优势值"""
        height_advantage = 2 * (attacker.height - target.height)
        attacker_env_value = self.calculate_environment_value(attacker)
        target_env_value = self.calculate_environment_value(target)
        env_advantage = 3 * (attacker_env_value - target_env_value)
        return height_advantage + env_advantage

    def calculate_environment_value(self, piece: Piece):
        """计算环境值"""
        env_value = 0
        for spell in self.delayed_spells:
            if spell.target_area.contains(piece.position):
                if spell.spell.effect_type == "Buff":
                    env_value += 1
                elif spell.spell.effect_type == "Damage":
                    env_value -= 1
        return env_value

    def handle_death_check(self, target: Piece):
        """处理死亡检查"""
        death_roll = self.roll_dice(1, 20)
        if self.if_log:
            print(f"[DeathCheck] Roll: {death_roll}")
        
        if death_roll == 20:
            target.get_accessor().set_health_to(1)
            target.get_accessor().set_dying(False)
            target.get_accessor().set_alive(True)
        else:
            target.get_accessor().set_alive(False)
            self.board.remove_piece(target)
            # 从 action_queue 中移除目标
            self.action_queue = np.array([p for p in self.action_queue if p != target], dtype=object)
            # 添加到死亡列表
            self.new_dead_this_round = np.append(self.new_dead_this_round, [target])
            target.death_round = self.round_number

    def execute_attack(self, attack_context: AttackContext):
        """执行攻击"""
        if (attack_context.attacker is None or attack_context.target is None or 
            not attack_context.attacker.is_alive or not attack_context.target.is_alive):
            return

        if attack_context.attacker.action_points <= 0:
            if self.if_log:
                print("[Attack] Failed: Not enough action points.")
            return

        if not self.is_in_attack_range(attack_context.attacker, attack_context.target):
            if self.if_log:
                print("[Attack] Failed: Out of range.")
            return

        attack_roll = self.roll_dice(1, 20)
        is_hit = False
        is_critical = False

        if attack_roll == 1:
            if self.if_log:
                print("[Attack] Natural 1 - Critical Miss.")
            is_hit = False
        elif attack_roll == 20:
            if self.if_log:
                print("[Attack] Natural 20 - Critical Hit!")
            is_hit = True
            is_critical = True
        else:
            attack_throw = attack_roll + self.step_modified_func(attack_context.attacker.strength) + \
                          self.calculate_advantage_value(attack_context.attacker, attack_context.target)
            
            defense_value = attack_context.target.physical_resist + \
                          self.step_modified_func(attack_context.target.dexterity)
            
            is_hit = attack_throw > defense_value
            if self.if_log:
                print(f"[Attack] Roll: {attack_roll} → Total Attack: {attack_throw}, Defense: {defense_value}, Hit: {is_hit}")

        if is_hit:
            damage = attack_context.attacker.physical_damage
            if is_critical:
                damage *= 2
            
            if self.if_log:
                print(f"[Attack] Dealing {damage} {'(Critical) ' if is_critical else ''}damage to target.")
            attack_context.target.receive_damage(damage, "physical")
            attack_context.damage_dealt = damage
            
            if attack_context.target.health <= 0:
                self.handle_death_check(attack_context.target)

        attack_context.attacker.get_accessor().change_action_points_by(-1)

    def get_available_spells(self, piece: Piece = None) -> List[Spell]:
        """获取指定棋子（或当前棋子）可用的法术列表
        
        Args:
            piece: 要检查的棋子，如果为None则使用当前行动棋子
            
        Returns:
            List[Spell]: 可用的法术列表
        """
        if piece is None:
            piece = self.current_piece
            
        if piece is None or not piece.is_alive:
            return []
            
        return SpellFactory.get_available_spells(piece)
        
    def get_spell_targets(self, spell: Spell, caster: Piece = None) -> List[Piece]:
        """获取法术可选的目标列表
        
        Args:
            spell: 要释放的法术
            caster: 施法者，如果为None则使用当前行动棋子
            
        Returns:
            List[Piece]: 可选的目标列表
        """
        if caster is None:
            caster = self.current_piece
            
        if caster is None or not caster.is_alive:
            return []
            
        targets = []
        for piece in self.action_queue:
            if not piece.is_alive:
                continue
                
            # 计算距离
            distance = math.sqrt(
                (caster.position.x - piece.position.x) ** 2 +
                (caster.position.y - piece.position.y) ** 2
            )
            
            # 检查是否在施法范围内
            if distance > spell.range:
                continue
                
            # 根据法术效果类型筛选目标
            if spell.effect_type in [SpellEffectType.DAMAGE, SpellEffectType.DEBUFF]:
                # 伤害和减益法术只能对敌人使用
                if piece.team != caster.team:
                    targets.append(piece)
            elif spell.effect_type in [SpellEffectType.HEAL, SpellEffectType.BUFF]:
                # 治疗和增益法术只能对友军使用
                if piece.team == caster.team:
                    targets.append(piece)
            elif spell.effect_type == SpellEffectType.MOVE:
                # 移动法术只能对自己使用
                if piece == caster:
                    targets.append(piece)
                    
        return targets
        
    def execute_spell(self, spell_context: SpellContext):
        """执行法术"""
        if spell_context.caster is None or not spell_context.caster.is_alive:
            if self.if_log:
                print("[Spell] Failed: Invalid caster.")
            return
            
        # 检查资源
        if (spell_context.caster.action_points <= 0 or 
            spell_context.caster.spell_slots < spell_context.spell_cost):
            if self.if_log:
                print("[Spell] Failed: Not enough resources.")
            return
            
        # 检查施法距离
        if spell_context.target is not None:
            distance = math.sqrt(
                (spell_context.caster.position.x - spell_context.target.position.x) ** 2 +
                (spell_context.caster.position.y - spell_context.target.position.y) ** 2
            )
            if distance > spell_context.spell.range:
                if self.if_log:
                    print("[Spell] Failed: Target out of range.")
                return
                
        # 处理延时法术
        if spell_context.is_delay_spell and not spell_context.delay_add:
            spell_context.delay_add = True
            self.delayed_spells = np.append(self.delayed_spells, [spell_context])
            spell_context.caster.get_accessor().change_action_points_by(-1)
            spell_context.caster.get_accessor().change_spell_slots_by(-1)
            if self.if_log:
                print("[Spell] Delayed spell added.")
            return

        # 处理锁定法术
        if spell_context.spell.is_locking_spell:
            if spell_context.target is None:
                if self.if_log:
                    print("[Spell] Failed: No target for locking spell.")
                return
                
            if not spell_context.target_area.contains(spell_context.target.position):
                if self.if_log:
                    print("[Spell] Target is out of range.")
                return
            print(f"spell_context.type: {spell_context.spell.effect_type}")
            self.apply_spell_effect(spell_context.target, spell_context)
            if self.if_log:
                print("[Spell] Effect applied to single target.")
            
        # 处理范围法术
        else:
            targets = []
            for piece in self.action_queue:
                if not piece.is_alive:
                    continue
                    
                if not spell_context.target_area.contains(piece.position):
                    continue
                    
                # 根据法术效果类型筛选目标
                if spell_context.spell.effect_type in [SpellEffectType.DAMAGE, SpellEffectType.DEBUFF]:
                    if piece.team != spell_context.caster.team:
                        targets.append(piece)
                elif spell_context.spell.effect_type in [SpellEffectType.HEAL, SpellEffectType.BUFF]:
                    if piece.team == spell_context.caster.team:
                        targets.append(piece)
                elif spell_context.spell.effect_type == SpellEffectType.MOVE:
                    if piece == spell_context.caster:
                        targets.append(piece)
                        
            spell_context.hit_pieces = targets
            for target in targets:
                self.apply_spell_effect(target, spell_context)
                if self.if_log:
                    print("[Spell] Effect applied to target.")

        # 消耗资源
        spell_context.caster.get_accessor().change_action_points_by(-1)
        spell_context.caster.get_accessor().change_spell_slots_by(-1)

    def apply_spell_effect(self, target: Piece, spell_context: SpellContext):
        """应用法术效果"""
        accessor = target.get_accessor()
        
        if spell_context.spell.effect_type == SpellEffectType.DAMAGE:
            accessor.set_health_to(max(target.health - spell_context.spell.base_value, 0))
            if target.health <= 0:
                self.handle_death_check(target)
        elif spell_context.spell.effect_type == SpellEffectType.HEAL:
            accessor.set_health_to(min(target.health + spell_context.spell.base_value, target.max_health))
        elif spell_context.spell.effect_type == SpellEffectType.BUFF:
            accessor.set_physical_damage_to(target.physical_damage + spell_context.spell.base_value)
        elif spell_context.spell.effect_type == SpellEffectType.DEBUFF:
            accessor.set_physic_resist_by(spell_context.spell.base_value)
            accessor.set_magic_resist_by(spell_context.spell.base_value)
        elif spell_context.spell.effect_type == SpellEffectType.MOVE:
            
            # 检查目标区域是否存在
            if not spell_context.target_area:
                if self.if_log:
                    print("[Spell:Move] Error: No target area specified")
                return
                
            # 设置目标位置
            target_pos = Point(spell_context.target_area.x, spell_context.target_area.y)
            print(f"target_pos: {target_pos}")
            # 尝试移动（使用很大的移动力值以确保可以到达）
            path, success = self.board.move_piece(target, target_pos, 100.0)
            
            if self.if_log:
                print(f"[Spell:Move] Move success: {success}")
            
            if success:
                # 更新行动点和位置
                target.set_action_points(target.get_action_points() - 1)
                accessor.set_position(target_pos)
            else:
                if self.if_log:
                    print("[Move] Failed: Out of Range")

    def step(self):
        """单回合步进"""
        self.round_number += 1
        if self.if_log:
            print(f"\n===== 回合 {self.round_number} =====")

        # 重置行动点
        for piece in self.action_queue:
            if piece.is_alive:
                piece.set_action_points(piece.max_action_points)

        # 获取当前棋子
        self.current_piece = self.action_queue[0]
        current_player = self.current_piece.team

        if self.if_log:
            print(f"当前行动棋子: ID={self.current_piece.id}, 玩家={current_player}")

        # 处理延时法术
        for i in range(len(self.delayed_spells) - 1, -1, -1):
            spell = self.delayed_spells[i]
            spell.spell_lifespan -= 1
            
            if spell.spell_lifespan == 0:
                self.execute_spell(spell)
                self.delayed_spells = np.delete(self.delayed_spells, i)
                if self.if_log:
                    print("[Spell] Delayed spell triggered and removed.")
            elif spell.spell_lifespan < 0:
                self.delayed_spells = np.delete(self.delayed_spells, i)
                if self.if_log:
                    print("[Spell] Delayed spell expired and removed.")

        # 使用输入管理器获取行动
        action = self.input_manager.handle_action_input(current_player, self)
        print(f"envState:{self.if_log}")
        if self.if_log:
            print(f"action: {action}")
        
        # 更新行动队列
        # 移除第一个元素并添加到末尾
        self.action_queue = np.append(self.action_queue[1:], [self.current_piece])

        # 执行行动
        if action:
            self.execute_player_action(action)

        # 检查游戏结束
        self.is_game_over = (
            not any(p.is_alive for p in self.player1.pieces) or
            not any(p.is_alive for p in self.player2.pieces)
        )
        
        if self.is_game_over and self.if_log:
            print("游戏结束!")
            winner = 1 if any(p.is_alive for p in self.player1.pieces) else 2
            print(f"玩家{winner}获胜!")

        # 更新死亡列表
        self.last_round_dead_pieces = np.array(self.new_dead_this_round, dtype=object)
        self.new_dead_this_round = np.array([], dtype=object)

    def execute_player_action(self, action: ActionSet):
        """执行玩家行动
        
        Args:
            action: ActionSet对象，包含移动、攻击和法术行动
        """
        # 处理移动
        if hasattr(action, 'move') and action.move:
            target = action.move_target
            path, success = self.board.move_piece(self.current_piece, target, self.current_piece.movement)
            if success:
                self.current_piece.set_action_points(self.current_piece.get_action_points() - 1)
                if self.if_log:
                    print(f"移动成功到 ({target.x}, {target.y})")
            elif self.if_log:
                print("移动失败")
                
        # 处理攻击
        if hasattr(action, 'attack') and action.attack:
            if hasattr(action, 'attack_context') and action.attack_context:
                self.execute_attack(action.attack_context)
                if action.attack_context.damage_dealt > 0 and self.if_log:
                    print(f"对棋子{action.attack_context.target.id}造成{action.attack_context.damage_dealt}点伤害")
            elif self.if_log:
                print("无效的攻击目标")
                
        # 处理法术
        if hasattr(action, 'spell') and action.spell:
            if hasattr(action, 'spell_context') and action.spell_context:
                self.execute_spell(action.spell_context)
            elif self.if_log:
                print("无效的法术目标")

    def visualize_board(self):
        """可视化棋盘"""
        print("\n当前棋盘:")
        # 打印列号
        print("   ", end="")
        for x in range(self.board.width):
            print(f"{x:2d} ", end="")
        print("\n")
        
        for y in range(self.board.height):
            # 打印行号
            print(f"{y:2d} ", end="")
            for x in range(self.board.width):
                cell = self.board.grid[x][y]
                if cell.state == 2:
                    piece = next((p for p in self.action_queue if p.id == cell.piece_id), None)
                    if piece:
                        if piece.team == 1:
                            print(f"{Fore.RED}{piece.id:2d} ", end="")
                        else:
                            print(f"{Fore.BLUE}{piece.id:2d} ", end="")
                    else:
                        print("X  ", end="")
                elif cell.state == -1:
                    print(f"{Fore.WHITE}{Back.BLACK}## ", end="")
                else:
                    print(f"{Fore.GREEN}{cell.state:2d} ", end="")
            print(Style.RESET_ALL)  # 重置颜色
        print()

    def get_state_score(self) -> float:
        """获取当前游戏状态的评分（用于AI决策）
        
        评分考虑因素：
        1. 双方棋子的生命值
        2. 棋子的位置优势（基于高度和控制区域）
        3. 剩余行动点和法术位
        4. 装备和属性加成
        
        Returns:
            float: 状态评分。正值表示对当前行动方有利，负值表示不利
        """
        if self.current_piece is None:
            return 0.0
            
        current_team = self.current_piece.team
        score = 0.0
        
        # 计算双方棋子状态
        for piece in self.action_queue:
            if not piece.is_alive:
                continue
                
            piece_score = 0.0
            # 基础生命值评分
            piece_score += piece.health / piece.max_health * 10
            
            # 位置评分（高度优势）
            height_advantage = piece.height * 0.5
            piece_score += height_advantage
            
            # 资源评分
            piece_score += piece.action_points * 2
            piece_score += piece.spell_slots * 1.5
            
            # 装备和属性评分
            piece_score += (piece.physical_damage + piece.magic_damage) * 0.3
            piece_score += (piece.physical_resist + piece.magic_resist) * 0.2
            
            # 根据队伍调整分数
            if piece.team == current_team:
                score += piece_score
            else:
                score -= piece_score
                
        return score
        
    def get_legal_moves(self, piece: Piece = None) -> List[Point]:
        """获取指定棋子（或当前棋子）的所有合法移动位置
        
        Args:
            piece: 要检查的棋子，如果为None则使用当前行动棋子
            
        Returns:
            List[Point]: 所有合法的移动目标位置
        """
        if piece is None:
            piece = self.current_piece
            
        if piece is None or not piece.is_alive:
            return []
            
        legal_moves = []
        mask = self.board.valid_target(piece, piece.movement)
        
        for x in range(self.board.width):
            for y in range(self.board.height):
                if mask[x][y] != -1:
                    legal_moves.append(Point(x, y))
                    
        return legal_moves
        
    def get_attackable_targets(self, piece: Piece = None) -> List[Piece]:
        """获取指定棋子（或当前棋子）可攻击的所有目标
        
        Args:
            piece: 要检查的棋子，如果为None则使用当前行动棋子
            
        Returns:
            List[Piece]: 所有可攻击的目标棋子
        """
        if piece is None:
            piece = self.current_piece
            
        if piece is None or not piece.is_alive:
            return []
            
        targets = []
        for target in self.action_queue:
            if (target.is_alive and 
                target.team != piece.team and
                self.is_in_attack_range(piece, target)):
                targets.append(target)
                
        return targets
        
    def simulate_move(self, piece: Piece, target: Point) -> bool:
        """模拟移动棋子（用于AI决策树搜索），不改变实际游戏状态
        
        Args:
            piece: 要移动的棋子
            target: 目标位置
            
        Returns:
            bool: 移动是否合法
        """
        if not piece.is_alive:
            return False
            
        # 检查移动是否合法
        mask = self.board.valid_target(piece, piece.movement)
        if mask[target.x][target.y] == -1:
            return False
            
        return True
        
    def simulate_attack(self, attacker: Piece, target: Piece) -> float:
        """模拟攻击（用于AI决策树搜索），返回预期伤害
        
        Args:
            attacker: 攻击方棋子
            target: 防守方棋子
            
        Returns:
            float: 预期伤害值
        """
        if not attacker.is_alive or not target.is_alive:
            return 0.0
            
        if not self.board.is_in_attack_range(attacker, target):
            return 0.0
            
        # 计算预期伤害
        attack_throw = 10.5 + self.step_modified_func(attacker.strength)  # 使用平均骰子值
        defense_value = target.physical_resist + self.step_modified_func(target.dexterity)
        
        if attack_throw <= defense_value:
            return 0.0
            
        return max(0, attacker.physical_damage - target.physical_resist)
        
    def step_with_action(self, action: ActionSet) -> None:
        """使用指定的动作执行一个游戏步骤
        
        这是一个辅助方法，用于AI决策树搜索等场景，它会：
        1. 更新回合计数
        2. 重置行动点
        3. 处理延时法术
        4. 执行指定动作
        5. 更新游戏状态
        
        Args:
            action: 要执行的动作
        """
        self.round_number += 1
        
        # 重置行动点
        for piece in self.action_queue:
            if piece.is_alive:
                piece.set_action_points(piece.max_action_points)
                
        # 获取当前棋子
        self.current_piece = self.action_queue[0]
        current_player = self.current_piece.team
        
        # 处理延时法术
        for i in range(len(self.delayed_spells) - 1, -1, -1):
            spell = self.delayed_spells[i]
            spell.spell_lifespan -= 1
            
            if spell.spell_lifespan == 0:
                self.execute_spell(spell)
                self.delayed_spells = np.delete(self.delayed_spells, i)
            elif spell.spell_lifespan < 0:
                self.delayed_spells = np.delete(self.delayed_spells, i)
                
        # 更新行动队列
        self.action_queue = np.append(self.action_queue[1:], [self.current_piece])
        
        # 执行行动
        if action:
            self.execute_player_action(action)
            
        # 检查游戏结束
        self.is_game_over = (
            not any(p.is_alive for p in self.player1.pieces) or
            not any(p.is_alive for p in self.player2.pieces)
        )
        
        # 更新死亡列表
        self.last_round_dead_pieces = np.array(self.new_dead_this_round, dtype=object)
        self.new_dead_this_round = np.array([], dtype=object)
        
    def fork(self) -> 'Environment':
        """创建当前环境的深拷贝
        
        Returns:
            Environment: 一个新的、独立的环境副本
        """
        # 创建新的环境实例，禁用日志
        new_env = Environment(local_mode=(self.mode == 0), if_log=0)
        
        # 复制基本属性
        new_env.mode = self.mode
        new_env.round_number = self.round_number
        new_env.is_game_over = self.is_game_over
        
        # 深拷贝棋盘
        if self.board:
            new_env.board = Board(if_log=new_env.if_log)
            new_env.board.width = self.board.width
            new_env.board.height = self.board.height
            new_env.board.boarder = self.board.boarder
            # 深拷贝 grid
            new_env.board.grid = np.array([[copy.deepcopy(cell) for cell in row] for row in self.board.grid], dtype=object)
            # 深拷贝 height_map
            new_env.board.height_map = np.copy(self.board.height_map)
        
        # 深拷贝所有棋子
        new_env.action_queue = np.array([copy.deepcopy(piece) for piece in self.action_queue], dtype=object)
        new_env.delayed_spells = np.array([copy.deepcopy(spell) for spell in self.delayed_spells], dtype=object)
        new_env.new_dead_this_round = np.array([copy.deepcopy(piece) for piece in self.new_dead_this_round], dtype=object)
        new_env.last_round_dead_pieces = np.array([copy.deepcopy(piece) for piece in self.last_round_dead_pieces], dtype=object)
        
        # 设置当前棋子
        if self.current_piece:
            # 在新的 action_queue 中找到对应的棋子
            for piece in new_env.action_queue:
                if piece.id == self.current_piece.id:
                    new_env.current_piece = piece
                    break
        
        # 深拷贝玩家
        new_env.player1 = copy.deepcopy(self.player1)
        new_env.player2 = copy.deepcopy(self.player2)
        
        # 更新玩家的棋子引用，使其指向新的 action_queue 中的棋子
        new_env.player1.pieces = np.array([piece for piece in new_env.action_queue if piece.team == 1], dtype=object)
        new_env.player2.pieces = np.array([piece for piece in new_env.action_queue if piece.team == 2], dtype=object)
        
        return new_env

    def run(self):
        """运行游戏主循环"""
        self.initialize()

        if self.if_log:
            print("游戏初始化完成，开始游戏！")
            self.visualize_board()
        
        while not self.is_game_over:
            self.step()
            if self.if_log:
                self.visualize_board()
            
            # 如果是控制台输入模式，检查是否继续
            if (isinstance(self.input_manager.get_input_method(1), ConsoleInputMethod) or
                isinstance(self.input_manager.get_input_method(2), ConsoleInputMethod)):
                if input("\n继续下一回合? (y/n): ").lower() != 'y':
                    break


if __name__ == "__main__":
    # 运行本地游戏
    env = Environment(local_mode=True)
    env.run()