from typing import List, Tuple, Optional, Dict, Callable, TYPE_CHECKING
from dataclasses import dataclass
import os
from utils import *

if TYPE_CHECKING:
    from env import Environment, InitGameMessage, InitPolicyMessage, PieceArg

class IInputMethod:
    """输入方法接口 - 定义所有输入方法的通用接口"""
    def handle_init_input(self, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        """处理初始化输入"""
        raise NotImplementedError()
        
    def handle_action_input(self, env: 'Environment') -> ActionSet:
        """处理游戏中的行动输入"""
        raise NotImplementedError()
        
    @property
    def name(self) -> str:
        """输入方法的名称"""
        raise NotImplementedError()


class ConsoleInputMethod(IInputMethod):
    """控制台输入方法"""
    @property
    def name(self) -> str:
        return "console"
        
    def handle_init_input(self, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        """从控制台获取初始化输入"""
        policy = InitPolicyMessage()
        policy.piece_args = []
        
        for i in range(init_message.piece_cnt):
            print(f"Init piece {i + 1}/{init_message.piece_cnt} for player {init_message.id}")
            piece_arg = PieceArg()
            
            # 属性输入
            while True:
                print("Enter stats: strength dexterity intelligence (sum <= 30)")
                user_input = input()
                if user_input:
                    try:
                        inputs = user_input.split()
                        nums = [int(x) for x in inputs]
                        if len(nums) != 3:
                            print("Expected exactly 3 integers")
                            continue
                        
                        strength, dexterity, intelligence = nums
                        
                        if any(n < 0 for n in nums):
                            print("Stats must be non-negative")
                            continue
                            
                        if sum(nums) > 30:
                            print("Sum of stats must not exceed 30")
                            continue
                            
                        piece_arg.strength = strength
                        piece_arg.dexterity = dexterity
                        piece_arg.intelligence = intelligence
                        break
                    except ValueError:
                        print("Invalid input: need integers")
                        continue

            # 显示武器防具表
            print("\nWeapons / armor table")
            print("Weapon     phys   magic   range")
            print("1 longsword 18     0       5")
            print("2 shortsword 24     0       3")
            print("3 bow        16     0       9")
            print("4 staff       0    22      12")
            print("Armor    phys_res magic_res AP mod")
            print("1 light       8       10      +3")
            print("2 medium     15       13       0")
            print("3 heavy      23       17      -3")

            # 装备选择
            while True:
                print("\nEnter weapon (1-4) and armor (1-3), space-separated")
                user_input = input()
                if user_input:
                    try:
                        inputs = user_input.split()
                        if len(inputs) != 2:
                            print("Expected exactly 2 integers")
                            continue
                            
                        weapon, armor = map(int, inputs)
                        
                        if not (1 <= weapon <= 4 and 1 <= armor <= 3):
                            print("Weapon or armor type out of range")
                            continue
                            
                        if weapon == 4 and armor != 1:
                            print("Staff must be paired with light armor (armor 1)")
                            continue
                            
                        piece_arg.equip = Point(weapon, armor)
                        break
                    except ValueError:
                        print("Invalid input: need integers")
                        continue

            # 位置选择
            while True:
                rows = init_message.board.height
                cols = init_message.board.width
                boarder = init_message.board.boarder
                
                print("\nEnter start cell: x y")
                user_input = input()
                if user_input:
                    try:
                        inputs = user_input.split()
                        if len(inputs) != 2:
                            print("Expected exactly 2 integers")
                            continue
                            
                        x, y = map(int, inputs)
                        
                        if not (0 <= x < cols and 0 <= y < rows):
                            print("Coordinates out of board bounds")
                            continue
                            
                        if init_message.board.grid[x][y].state != 1:
                            print("Cell is not walkable")
                            continue
                            
                        # 检查边界条件
                        if init_message.id == 1 and y >= boarder:
                            print(f"Player 1 pieces must be below border (y < {boarder})")
                            continue
                        elif init_message.id == 2 and y <= boarder:
                            print(f"Player 2 pieces must be above border (y > {boarder})")
                            continue
                            
                        # 检查是否与已添加的棋子位置冲突
                        is_valid = True
                        for existing_arg in policy.piece_args:
                            if x == existing_arg.pos.x and y == existing_arg.pos.y:
                                print("Cell already occupied by another of your pieces")
                                is_valid = False
                                break
                                
                        if not is_valid:
                            continue
                            
                        piece_arg.pos = Point(x, y)
                        break
                    except ValueError:
                        print("Invalid input: need integers")
                        continue
                        
            policy.piece_args.append(piece_arg)
            
        return policy
        
    def handle_action_input(self, env: 'Environment') -> ActionSet:
        """从控制台获取行动输入"""
        print(f"\nTeam {env.current_piece.team} turn — piece id={env.current_piece.id}")
        print(f"Position: ({env.current_piece.position.x}, {env.current_piece.position.y})")
        print(f"HP: {env.current_piece.health}/{env.current_piece.max_health}")
        print(f"Action points: {env.current_piece.action_points}")
        print(f"Spell slots: {env.current_piece.spell_slots}")
        
        # 显示地图
        env.visualize_board()
        
        action = ActionSet()
        
        # 移动部分
        while True:
            print("\nMove target: x y (or -1 -1 to skip move)")
            try:
                user_input = input()
                inputs = user_input.split()
                if len(inputs) != 2:
                    print("Expected two space-separated integers.")
                    continue
                
                x, y = map(int, inputs)
                
                if x == -1 or y == -1:
                    action.move = False
                    break
                
                # 检查移动目标是否合法
                if not (0 <= x < env.board.width and 0 <= y < env.board.height):
                    print("Target out of map bounds")
                    continue
                    
                if env.board.grid[x][y].state != 1:
                    print("Target cell is not walkable")
                    continue
                
                # 检查移动力是否足够
                path, cost = env.board.find_shortest_path(env.current_piece, env.current_piece.position, Point(x, y), env.current_piece.movement)
                if path is None or cost > env.current_piece.movement:
                    print("Target beyond movement reach")
                    continue
                
                action.move = True
                action.move_target = Point(x, y)
                break
            except ValueError:
                print("Invalid input: need integers")
                continue
        
        # 攻击部分
        while True:
            print("\nAttack target piece id (-1 to skip)")
            try:
                target_id = int(input())
                if target_id == -1:
                    action.attack = False
                    break
                
                # 查找目标棋子
                target = next((p for p in env.action_queue if p.id == target_id and p.is_alive), None)
                if target is None:
                    print("No such piece.")
                    continue
                    
                if target.team == env.current_piece.team:
                    print("Cannot attack friendly piece")
                    continue
                    
                # 检查攻击范围
                if not env.is_in_attack_range(env.current_piece, target):
                    print("Target out of attack range")
                    continue
                
                action.attack = True
                action.attack_context = AttackContext()
                action.attack_context.attacker = env.current_piece
                action.attack_context.target = target
                break
            except ValueError:
                print("Invalid input: need integers")
                continue
        
        # 法术部分
        print("\nCast a spell? (1 = yes, anything else = no)")
        spell_choice = input()
        if spell_choice and spell_choice.strip() == "1":
            while True:
                print("\nSpell id (-1 to cancel)")
                try:
                    spell_id = int(input())
                    if spell_id == -1:
                        action.spell = False
                        break
                    
                    # 检查法术位
                    if env.current_piece.spell_slots <= 0:
                        print("No spell slots left")
                        action.spell = False
                        break
                    
                    # 获取法术信息
                    spell = SpellFactory.get_spell_by_id(spell_id)
                    if spell is None:
                        print("Unknown spell id")
                        continue
                    
                    print(f"\nSelected spell: {spell.name}")
                    print(f"Effect type: {spell.effect_type}")
                    print(f"Base value: {spell.base_value}")
                    print(f"Range: {spell.range}")
                    
                    # 获取可选目标
                    spell_targets = env.get_spell_targets(spell)
                    if not spell_targets and not spell.is_area_effect:
                        print("No valid targets")
                        continue
                        
                    print("\nSpell center: x y")
                    coords = input().split()
                    if len(coords) != 2:
                        print("Expected two integers")
                        continue
                    
                    x, y = map(int, coords)
                    
                    # 检查施法距离
                    distance = abs(env.current_piece.position.x - x) + abs(env.current_piece.position.y - y)
                    if distance > spell.range:
                        print(f"Out of spell range (max {spell.range})")
                        continue
                    
                    if spell.is_area_effect:
                        target = None
                    else:
                        print("\nTarget piece id for spell:")
                        try:
                            target_id = int(input())
                            target = next((p for p in spell_targets if p.id == target_id), None)
                            if target is None:
                                print("Invalid target")
                                continue
                        except ValueError:
                            print("Invalid input: need integers")
                            continue
                    
                    action.spell = True
                    action.spell_context = SpellContext()
                    action.spell_context.caster = env.current_piece
                    action.spell_context.target = target
                    action.spell_context.spell = spell
                    action.spell_context.target_area = Area(x, y, spell.area_radius)
                    action.spell_context.is_delay_spell = spell.is_delay_spell
                    action.spell_context.spell_lifespan = spell.base_lifespan
                    action.spell_context.delay_add = False
                    break
                except ValueError:
                    print("Invalid input: need integers")
                    continue
        else:
            action.spell = False
        
        return action


class FunctionInputMethod(IInputMethod):
    """函数式本地输入方法"""
    def __init__(self, init_handler: Callable[['InitGameMessage'], List[PieceArg]],
                 action_handler: Callable[['Environment'], ActionSet]):
        self._init_handler = init_handler
        self._action_handler = action_handler
        
    @property
    def name(self) -> str:
        return "function"
        
    def handle_init_input(self, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        piece_args = self._init_handler(init_message)
        policy = InitPolicyMessage()
        policy.piece_args = piece_args
        return policy
        
    def handle_action_input(self, env: 'Environment') -> ActionSet:
        print(f"[FunctionInput] Executing action handler for player {env.current_piece.team}")
        try:
            action = self._action_handler(env)
            print(f"[FunctionInput] Action handler executed successfully")
            return action
        except Exception as e:
            print(f"[FunctionInput] Error executing action handler: {e}")
            raise


class RemoteInputMethod(IInputMethod):
    """远程输入方法"""
    def __init__(self, env: 'Environment'):
        self._env = env
        
    @property
    def name(self) -> str:
        return "remote"
        
    def handle_init_input(self, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        raise NotImplementedError("Remote input: use gRPC client for init")
        
    def handle_action_input(self, env: 'Environment') -> ActionSet:
        raise NotImplementedError("Remote input: use gRPC client for actions")


class InputMethodManager:
    """输入方法管理器"""
    def __init__(self, env: 'Environment'):
        self._env = env
        self._player_input_methods = {}
        
        # 默认为所有玩家设置控制台输入
        self.set_console_input_method(1)
        self.set_console_input_method(2)
        
    def set_input_method(self, player_id: int, input_method: IInputMethod):
        """设置玩家的输入方法"""
        self._player_input_methods[player_id] = input_method
        # print(f"玩家 {player_id} 的输入方式已设置为: {input_method.name}")
        
    def get_input_method(self, player_id: int) -> IInputMethod:
        """获取玩家的输入方法"""
        if player_id in self._player_input_methods:
            return self._player_input_methods[player_id]
            
        # 默认返回控制台输入
        default_method = ConsoleInputMethod()
        self._player_input_methods[player_id] = default_method
        return default_method
        
    def set_function_input_method(self, player_id: int,
                                init_handler: Callable[['InitGameMessage'], 'InitPolicyMessage'],
                                action_handler: Callable[['Environment'], ActionSet]):
        """设置函数式输入方法"""
        input_method = FunctionInputMethod(init_handler, action_handler)
        self.set_input_method(player_id, input_method)
        
    def set_console_input_method(self, player_id: int):
        """设置控制台输入方法"""
        self.set_input_method(player_id, ConsoleInputMethod())
        
    def set_remote_input_method(self, player_id: int):
        """设置远程输入方法"""
        self.set_input_method(player_id, RemoteInputMethod(self._env))
        
    def handle_init_input(self, player_id: int, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        """处理初始化输入"""
        input_method = self.get_input_method(player_id)
        
        if isinstance(input_method, RemoteInputMethod):
            raise ValueError("Remote input: use gRPC client for init")
            
        return input_method.handle_init_input(init_message)
        
    def handle_action_input(self, player_id: int, env: 'Environment') -> ActionSet:
        """处理行动输入"""
        input_method = self.get_input_method(player_id)
        print(f"[InputManager] player {player_id} input: {input_method.name}")
        
        if isinstance(input_method, RemoteInputMethod):
            raise ValueError("Remote input: use gRPC client for actions")
            
        print(f"[InputManager] handling action input for player {player_id}")
        action = input_method.handle_action_input(env)
        print(f"[InputManager] player {player_id} action input done")
        return action
        
    def is_remote_input(self, player_id: int) -> bool:
        """检查玩家是否使用远程输入方法"""
        return isinstance(self.get_input_method(player_id), RemoteInputMethod)