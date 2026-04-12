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
        return "控制台输入"
        
    def handle_init_input(self, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        """从控制台获取初始化输入"""
        policy = InitPolicyMessage()
        policy.piece_args = []
        
        for i in range(init_message.piece_cnt):
            print(f"现在为棋手 {init_message.id} 的第 {i + 1} 个棋子初始化")
            piece_arg = PieceArg()
            
            # 属性输入
            while True:
                print("为棋子输入属性分配，格式为：力量 敏捷 智力 总和不超过30")
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
                            
                        piece_arg.strength = strength
                        piece_arg.dexterity = dexterity
                        piece_arg.intelligence = intelligence
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
                            
                        piece_arg.equip = Point(weapon, armor)
                        break
                    except ValueError:
                        print("输入的不是整数")
                        continue

            # 位置选择
            while True:
                rows = init_message.board.height
                cols = init_message.board.width
                boarder = init_message.board.boarder
                
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
                            
                        if init_message.board.grid[x][y].state != 1:
                            print("输入的坐标状态为不可占据!")
                            continue
                            
                        # 检查边界条件
                        if init_message.id == 1 and y >= boarder:
                            print(f"玩家1的棋子必须在边界线{boarder}以下!")
                            continue
                        elif init_message.id == 2 and y <= boarder:
                            print(f"玩家2的棋子必须在边界线{boarder}以上!")
                            continue
                            
                        # 检查是否与已添加的棋子位置冲突
                        is_valid = True
                        for existing_arg in policy.piece_args:
                            if x == existing_arg.pos.x and y == existing_arg.pos.y:
                                print("输入的坐标与已有棋子重合！")
                                is_valid = False
                                break
                                
                        if not is_valid:
                            continue
                            
                        piece_arg.pos = Point(x, y)
                        break
                    except ValueError:
                        print("输入的不是整数")
                        continue
                        
            policy.piece_args.append(piece_arg)
            
        return policy
        
    def handle_action_input(self, env: 'Environment') -> ActionSet:
        """从控制台获取行动输入"""
        print(f"\n玩家{env.current_piece.team}的回合 - 棋子ID: {env.current_piece.id}")
        print(f"位置: ({env.current_piece.position.x}, {env.current_piece.position.y})")
        print(f"生命: {env.current_piece.health}/{env.current_piece.max_health}")
        print(f"行动点: {env.current_piece.action_points}")
        print(f"法术位: {env.current_piece.spell_slots}")
        
        # 显示地图
        env.visualize_board()
        
        action = ActionSet()
        
        # 移动部分
        while True:
            print("\n请输入目标移动位置（格式：x y, 若不移动，输入-1 -1）：")
            try:
                user_input = input()
                inputs = user_input.split()
                if len(inputs) != 2:
                    print("输入格式错误，应为两个用空格隔开的整数。")
                    continue
                
                x, y = map(int, inputs)
                
                if x == -1 or y == -1:
                    action.move = False
                    break
                
                # 检查移动目标是否合法
                if not (0 <= x < env.board.width and 0 <= y < env.board.height):
                    print("目标位置超出地图范围！")
                    continue
                    
                if env.board.grid[x][y].state != 1:
                    print("目标位置不可移动！")
                    continue
                
                # 检查移动力是否足够
                path, cost = env.board.find_shortest_path(env.current_piece, env.current_piece.position, Point(x, y), env.current_piece.movement)
                if path is None or cost > env.current_piece.movement:
                    print("目标位置超出移动范围！")
                    continue
                
                action.move = True
                action.move_target = Point(x, y)
                break
            except ValueError:
                print("输入的不是整数")
                continue
        
        # 攻击部分
        while True:
            print("\n请输入要攻击的棋子id编号（若不攻击，输入-1）：")
            try:
                target_id = int(input())
                if target_id == -1:
                    action.attack = False
                    break
                
                # 查找目标棋子
                target = next((p for p in env.action_queue if p.id == target_id and p.is_alive), None)
                if target is None:
                    print("未找到指定的棋子。")
                    continue
                    
                if target.team == env.current_piece.team:
                    print("不能攻击己方棋子！")
                    continue
                    
                # 检查攻击范围
                if not env.is_in_attack_range(env.current_piece, target):
                    print("目标超出攻击范围！")
                    continue
                
                action.attack = True
                action.attack_context = AttackContext()
                action.attack_context.attacker = env.current_piece
                action.attack_context.target = target
                break
            except ValueError:
                print("输入的不是整数")
                continue
        
        # 法术部分
        print("\n是否要施放法术？(1/-1)")
        spell_choice = input()
        if spell_choice and spell_choice.strip() == "1":
            while True:
                print("\n请输入要施加的法术id（若不施法，输入-1）：")
                try:
                    spell_id = int(input())
                    if spell_id == -1:
                        action.spell = False
                        break
                    
                    # 检查法术位
                    if env.current_piece.spell_slots <= 0:
                        print("没有剩余法术位！")
                        action.spell = False
                        break
                    
                    # 获取法术信息
                    spell = SpellFactory.get_spell_by_id(spell_id)
                    if spell is None:
                        print("未找到指定的法术。")
                        continue
                    
                    print(f"\n已选择法术: {spell.name}")
                    print(f"效果类型: {spell.effect_type}")
                    print(f"基础值: {spell.base_value}")
                    print(f"施法范围: {spell.range}")
                    
                    # 获取可选目标
                    spell_targets = env.get_spell_targets(spell)
                    if not spell_targets and not spell.is_area_effect:
                        print("没有可选的目标！")
                        continue
                        
                    print("\n请输入要施加的法术中心坐标（格式：x y）：")
                    coords = input().split()
                    if len(coords) != 2:
                        print("输入格式错误")
                        continue
                    
                    x, y = map(int, coords)
                    
                    # 检查施法距离
                    distance = abs(env.current_piece.position.x - x) + abs(env.current_piece.position.y - y)
                    if distance > spell.range:
                        print(f"施法范围超出限制！(最大范围: {spell.range})")
                        continue
                    
                    if spell.is_area_effect:
                        target = None
                    else:
                        print("\n请输入要攻击的棋子id编号：")
                        try:
                            target_id = int(input())
                            target = next((p for p in spell_targets if p.id == target_id), None)
                            if target is None:
                                print("无效的目标！")
                                continue
                        except ValueError:
                            print("输入的不是整数")
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
                    print("输入的不是整数")
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
        return "函数式输入"
        
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
        return "远程输入"
        
    def handle_init_input(self, init_message: 'InitGameMessage') -> 'InitPolicyMessage':
        raise NotImplementedError("远程输入方法使用 gRPC 客户端处理初始化")
        
    def handle_action_input(self, env: 'Environment') -> ActionSet:
        raise NotImplementedError("远程输入方法使用 gRPC 客户端处理行动输入")


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
            raise ValueError("远程输入方法使用 gRPC 客户端处理初始化")
            
        return input_method.handle_init_input(init_message)
        
    def handle_action_input(self, player_id: int, env: 'Environment') -> ActionSet:
        """处理行动输入"""
        input_method = self.get_input_method(player_id)
        print(f"[InputManager] 玩家{player_id}的输入方法为: {input_method.name}")
        
        if isinstance(input_method, RemoteInputMethod):
            raise ValueError("远程输入方法使用 gRPC 客户端处理行动输入")
            
        print(f"[InputManager] 开始处理玩家{player_id}的行动输入")
        action = input_method.handle_action_input(env)
        print(f"[InputManager] 玩家{player_id}的行动输入处理完成")
        return action
        
    def is_remote_input(self, player_id: int) -> bool:
        """检查玩家是否使用远程输入方法"""
        return isinstance(self.get_input_method(player_id), RemoteInputMethod)