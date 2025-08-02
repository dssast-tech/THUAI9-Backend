from typing import Callable, List
import math
from dataclasses import dataclass
from env import *
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
    def get_aggressive_action_strategy() -> Callable[[Environment], ActionSet]:
        """获取攻击型行动策略 - 主动接近并攻击敌人"""
        def strategy(env: Environment) -> ActionSet:
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
    def get_defensive_action_strategy() -> Callable[[Environment], ActionSet]:
        """获取防御型行动策略 - 保持距离，使用远程攻击"""
        def strategy(env: Environment) -> ActionSet:
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
    def get_random_action_strategy() -> Callable[[Environment], ActionSet]:
        """随机选择一个行动策略"""
        import random
        strategies = [
            StrategyFactory.get_aggressive_action_strategy(),
            StrategyFactory.get_defensive_action_strategy()
        ]
        return random.choice(strategies)

    @staticmethod
    def get_alpha_beta_action_strategy(max_depth: int = 3) -> Callable[[Environment], ActionSet]:
        """获取基于AlphaBeta剪枝的行动策略
        
        Args:
            max_depth: 最大搜索深度
            
        Returns:
            Callable[[Environment], ActionSet]: 策略函数
        """
        def alpha_beta(env: Environment, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, Optional[ActionSet]]:
            if depth == 0 or env.is_game_over:
                return env.get_state_score(), None
                
            current_piece = env.current_piece
            if maximizing:
                max_eval = float('-inf')
                best_action = None
                
                # 获取所有可能的移动
                legal_moves = env.get_legal_moves()
                attackable_targets = env.get_attackable_targets()
                
                # 尝试每个可能的行动组合
                for move in [None] + legal_moves:
                    for target in [None] + attackable_targets:
                        action = ActionSet()
                        
                        # 设置移动
                        if move is not None:
                            action.move = True
                            action.move_target = move
                        else:
                            action.move = False
                            
                        # 设置攻击
                        if target is not None:
                            action.attack = True
                            action.attack_context = AttackContext()
                            action.attack_context.attacker = current_piece
                            action.attack_context.target = target
                        else:
                            action.attack = False
                            
                        # 暂不考虑法术
                        action.spell = False
                        
                        # 模拟行动
                        next_env = env.fork()
                        next_env.execute_player_action(action)
                        
                        eval, _ = alpha_beta(next_env, depth - 1, alpha, beta, False)
                        if eval > max_eval:
                            max_eval = eval
                            best_action = action
                            
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                            
                return max_eval, best_action
            else:
                min_eval = float('inf')
                best_action = None
                
                # 获取所有可能的移动
                legal_moves = env.get_legal_moves()
                attackable_targets = env.get_attackable_targets()
                
                # 尝试每个可能的行动组合
                for move in [None] + legal_moves:
                    for target in [None] + attackable_targets:
                        action = ActionSet()
                        
                        # 设置移动
                        if move is not None:
                            action.move = True
                            action.move_target = move
                        else:
                            action.move = False
                            
                        # 设置攻击
                        if target is not None:
                            action.attack = True
                            action.attack_context = AttackContext()
                            action.attack_context.attacker = current_piece
                            action.attack_context.target = target
                        else:
                            action.attack = False
                            
                        # 暂不考虑法术
                        action.spell = False
                        
                        # 模拟行动
                        next_env = env.fork()
                        next_env.execute_player_action(action)
                        
                        eval, _ = alpha_beta(next_env, depth - 1, alpha, beta, True)
                        if eval < min_eval:
                            min_eval = eval
                            best_action = action
                            
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                            
                return min_eval, best_action
        
        def strategy(env: Environment) -> ActionSet:
            _, best_action = alpha_beta(env, max_depth, float('-inf'), float('inf'), True)
            return best_action if best_action is not None else ActionSet()
            
        return strategy
        
    @staticmethod
    def get_mcts_action_strategy(simulation_count: int = 100) -> Callable[[Environment], ActionSet]:
        """获取基于MCTS的行动策略
        
        Args:
            simulation_count: 每个决策点的模拟次数
            
        Returns:
            Callable[[Environment], ActionSet]: 策略函数
        """
        class MCTSNode:
            def __init__(self, env: Environment, parent=None, action: Optional[ActionSet] = None):
                self.env = env
                self.parent = parent
                self.action = action
                self.children = []
                self.visits = 0
                self.value = 0.0
                
            def expand(self):
                """扩展当前节点"""
                current_piece = self.env.current_piece
                legal_moves = self.env.get_legal_moves()
                attackable_targets = self.env.get_attackable_targets()
                
                # 生成所有可能的行动组合
                for move in [None] + legal_moves:
                    for target in [None] + attackable_targets:
                        action = ActionSet()
                        
                        # 设置移动
                        if move is not None:
                            action.move = True
                            action.move_target = move
                        else:
                            action.move = False
                            
                        # 设置攻击
                        if target is not None:
                            action.attack = True
                            action.attack_context = AttackContext()
                            action.attack_context.attacker = current_piece
                            action.attack_context.target = target
                        else:
                            action.attack = False
                            
                        # 暂不考虑法术
                        action.spell = False
                        
                        # 创建子节点
                        next_env = self.env.fork()
                        next_env.execute_player_action(action)
                        child = MCTSNode(next_env, self, action)
                        self.children.append(child)
                        
            def select(self) -> 'MCTSNode':
                """选择最有希望的子节点"""
                if not self.children:
                    return self
                    
                # UCB1公式选择节点
                def ucb1(node: MCTSNode) -> float:
                    if node.visits == 0:
                        return float('inf')
                    return node.value / node.visits + math.sqrt(2 * math.log(self.visits) / node.visits)
                    
                return max(self.children, key=ucb1)
                
            def simulate(self) -> float:
                """模拟到游戏结束"""
                sim_env = self.env.fork()
                max_steps = 50  # 防止无限循环
                
                while not sim_env.is_game_over and max_steps > 0:
                    # 随机选择行动
                    legal_moves = sim_env.get_legal_moves()
                    attackable_targets = sim_env.get_attackable_targets()
                    
                    action = ActionSet()
                    
                    # 随机移动
                    if legal_moves and random.random() < 0.7:
                        action.move = True
                        action.move_target = random.choice(legal_moves)
                    else:
                        action.move = False
                        
                    # 随机攻击
                    if attackable_targets and random.random() < 0.8:
                        action.attack = True
                        action.attack_context = AttackContext()
                        action.attack_context.attacker = sim_env.current_piece
                        action.attack_context.target = random.choice(attackable_targets)
                    else:
                        action.attack = False
                        
                    action.spell = False
                    
                    sim_env.execute_player_action(action)
                    max_steps -= 1
                    
                return sim_env.get_state_score()
                
            def backpropagate(self, value: float):
                """反向传播模拟结果"""
                node = self
                while node is not None:
                    node.visits += 1
                    node.value += value
                    node = node.parent
                    value = -value  # 对抗游戏中，父节点的收益是子节点的相反数
        
        def strategy(env: Environment) -> ActionSet:
            root = MCTSNode(env)
            
            # 运行MCTS
            for _ in range(simulation_count):
                node = root
                
                # 选择
                while node.children:
                    node = node.select()
                    
                # 扩展
                if node.visits > 0:
                    node.expand()
                    if node.children:
                        node = random.choice(node.children)
                        
                # 模拟
                value = node.simulate()
                
                # 反向传播
                node.backpropagate(value)
                
            # 选择访问次数最多的子节点对应的行动
            if not root.children:
                return ActionSet()
                
            best_child = max(root.children, key=lambda c: c.visits)
            return best_child.action
            
        return strategy