from typing import Callable, List
import math
from dataclasses import dataclass
from State import *
from converter import *
from utils import *
from message_pb2 import _InitResponse

class StrategyFactory:
    """策略工厂类 - 提供不同的游戏策略"""
    
    @staticmethod
    def calculate_distance(p1: Point, p2: Point) -> float:
        """计算两点之间的距离"""
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

    @staticmethod
    def get_aggressive_init_strategy() -> Callable[[_InitResponse], List[PieceArg]]:
        """获取攻击型初始化策略"""
        def strategy(init_message: _InitResponse) -> List[PieceArg]:
            piece_args = []
            
            # 攻击型配置：高力量，中敏捷，低智力
            for i in range(init_message.pieceCnt):
                arg = PieceArg()
                arg.strength = 20      # 高力量
                arg.dexterity = 8      # 中敏捷
                arg.intelligence = 2    # 低智力
                arg.equip = Point(2, 3)  # 短剑+重甲 (高伤害+高防御)
                
                # 设置位置 - 偏向前线位置
                if init_message.id == 1:  # 第一个玩家
                    arg.pos = Point(2 + i * 2, 5)
                else:  # 第二个玩家
                    arg.pos = Point(init_message.board.width - 3 - i * 2, init_message.board.height - 6)
                
                piece_args.append(arg)
            
            return piece_args
        
        return strategy

    @staticmethod
    def get_defensive_init_strategy() -> Callable[[_InitResponse], List[PieceArg]]:
        """获取防御型初始化策略"""
        def strategy(init_message: _InitResponse) -> List[PieceArg]:
            piece_args = []
            
            # 防御型配置：中力量，高敏捷，中智力
            for i in range(init_message.pieceCnt):
                arg = PieceArg()
                arg.strength = 5       # 低力量
                arg.dexterity = 15     # 高敏捷
                arg.intelligence = 10   # 中智力
                arg.equip = Point(3, 1)  # 弓+轻甲 (远程+机动性)
                
                # 设置位置 - 偏向后方位置
                if init_message.id == 1:  # 第一个玩家
                    arg.pos = Point(3 + i * 3, 3)
                else:  # 第二个玩家
                    arg.pos = Point(init_message.board.width - 4 - i * 3, init_message.board.height - 4)
                
                piece_args.append(arg)
            
            return piece_args
        
        return strategy

    @staticmethod
    def get_aggressive_action_strategy() -> Callable[[Env], ActionSet]:
        """获取攻击型行动策略 - 主动接近并攻击敌人"""
        def strategy(env: Env) -> ActionSet:
            action = ActionSet()
            current_piece = env.current_piece
            
            # 寻找最近的敌人
            target_enemy = None
            nearest_distance = float('inf')
            
            for piece in env.action_queue:
                if piece.team != current_piece.team and piece.is_alive:
                    distance = StrategyFactory.calculate_distance(
                        Point(current_piece.position.x, current_piece.position.y),
                        Point(piece.position.x, piece.position.y)
                    )
                    if distance < nearest_distance:
                        nearest_distance = distance
                        target_enemy = piece
            
            # 没有敌人，不执行任何动作
            if target_enemy is None:
                action.move = False
                action.attack = False
                action.spell = False
                return action
            
            # 移动决策 - 向目标敌人移动
            action.move = True
            
            # 计算向敌人方向移动的方向
            dx = 1 if target_enemy.position.x > current_piece.position.x else -1
            dy = 1 if target_enemy.position.y > current_piece.position.y else -1
            
            # 移动到目标位置
            action.move_target = Point(
                current_piece.position.x + dx,
                current_piece.position.y + dy
            )
            
            # 如果已经在攻击范围内，则攻击
            if nearest_distance <= current_piece.attack_range:
                action.attack = True
                action.attack_context = AttackContext()
                action.attack_context.attacker = current_piece
                action.attack_context.target = target_enemy
                action.attack_context.attackPosition = current_piece.position
            else:
                action.attack = False
            
            # 暂不使用法术
            action.spell = False
            
            return action
        
        return strategy

    @staticmethod
    def get_defensive_action_strategy() -> Callable[[Env], ActionSet]:
        """获取防御型行动策略 - 保持距离，使用远程攻击"""
        def strategy(env: Env) -> ActionSet:
            action = ActionSet()
            current_piece = env.current_piece
            
            # 寻找最近的敌人
            target_enemy = None
            nearest_distance = float('inf')
            
            for piece in env.action_queue:
                if piece.team != current_piece.team and piece.is_alive:
                    distance = StrategyFactory.calculate_distance(
                        Point(current_piece.position.x, current_piece.position.y),
                        Point(piece.position.x, piece.position.y)
                    )
                    if distance < nearest_distance:
                        nearest_distance = distance
                        target_enemy = piece
            
            # 没有敌人，不执行任何动作
            if target_enemy is None:
                action.move = False
                action.attack = False
                action.spell = False
                return action
            
            # 移动决策 - 保持在攻击范围内，但不要太近
            action.move = True
            
            # 理想距离是攻击范围的70%
            ideal_distance = current_piece.attack_range * 0.7
            
            if nearest_distance < ideal_distance - 2:  # 太近了，远离
                # 远离敌人
                dx = 1 if current_piece.position.x > target_enemy.position.x else -1
                dy = 1 if current_piece.position.y > target_enemy.position.y else -1
                
                action.move_target = Point(
                    current_piece.position.x + dx,
                    current_piece.position.y + dy
                )
            elif nearest_distance > ideal_distance + 2:  # 太远了，靠近
                # 靠近敌人
                dx = 1 if target_enemy.position.x > current_piece.position.x else -1
                dy = 1 if target_enemy.position.y > current_piece.position.y else -1
                
                action.move_target = Point(
                    current_piece.position.x + dx,
                    current_piece.position.y + dy
                )
            else:  # 在理想范围内
                action.move = False
            
            # 如果在攻击范围内，则攻击
            if nearest_distance <= current_piece.attack_range:
                action.attack = True
                action.attack_context = AttackContext()
                action.attack_context.attacker = current_piece
                action.attack_context.target = target_enemy
                action.attack_context.attackPosition = current_piece.position
            else:
                action.attack = False
            
            # 暂不使用法术
            action.spell = False
            
            return action
        
        return strategy

    @staticmethod
    def get_random_init_strategy() -> Callable[[_InitResponse], List[PieceArg]]:
        """随机选择一个初始化策略"""
        import random
        strategies = [
            StrategyFactory.get_aggressive_init_strategy(),
            StrategyFactory.get_defensive_init_strategy()
        ]
        return random.choice(strategies)

    @staticmethod
    def get_random_action_strategy() -> Callable[[Env], ActionSet]:
        """随机选择一个行动策略"""
        import random
        strategies = [
            StrategyFactory.get_aggressive_action_strategy(),
            StrategyFactory.get_defensive_action_strategy()
        ]
        return random.choice(strategies) 