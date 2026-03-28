"""
回放系统模块
提供游戏状态的序列化和反序列化功能
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from env import Environment, Piece, Board
    from utils import ActionSet, Point, SpellContext, AttackContext, Area, Spell, SpellEffectType

from utils import Point, ActionSet, AttackContext, SpellContext, Area, Spell, SpellEffectType


class NumpyEncoder(json.JSONEncoder):
    """自定义JSON编码器，自动处理NumPy类型"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


class ReplaySerializer:
    """回放序列化器"""
    
    @staticmethod
    def serialize_piece(piece: 'Piece') -> Optional[Dict]:
        """序列化棋子信息"""
        if piece is None:
            return None
        return {
            "id": piece.id,
            "team": piece.team,
            "type": piece.type,
            "position": {"x": piece.position.x, "y": piece.position.y},
            "height": piece.height,
            "health": piece.health,
            "max_health": piece.max_health,
            "action_points": piece.action_points,
            "max_action_points": piece.max_action_points,
            "spell_slots": piece.spell_slots,
            "max_spell_slots": piece.max_spell_slots,
            "movement": piece.movement,
            "max_movement": piece.max_movement,
            "physical_damage": piece.physical_damage,
            "magic_damage": piece.magic_damage,
            "physical_resist": piece.physical_resist,
            "magic_resist": piece.magic_resist,
            "strength": piece.strength,
            "dexterity": piece.dexterity,
            "intelligence": piece.intelligence,
            "attack_range": piece.attack_range,
            "is_alive": piece.is_alive,
            "is_dying": piece.is_dying,
            "death_round": piece.death_round
        }
    
    @staticmethod
    def serialize_action(action: 'ActionSet') -> Optional[Dict]:
        """序列化行动信息"""
        if action is None:
            return None
        
        action_data = {}
        
        # 移动信息
        if hasattr(action, 'move') and action.move and hasattr(action, 'move_target') and action.move_target:
            action_data["move"] = {
                "target": {"x": action.move_target.x, "y": action.move_target.y}
            }
        
        # 攻击信息
        if hasattr(action, 'attack') and action.attack and action.attack_context:
            attack_ctx = action.attack_context
            action_data["attack"] = {
                "attacker_id": attack_ctx.attacker.id if attack_ctx.attacker else None,
                "target_id": attack_ctx.target.id if attack_ctx.target else None,
                "damage_dealt": attack_ctx.damage_dealt if hasattr(attack_ctx, 'damage_dealt') else 0,
                "is_hit": attack_ctx.is_hit if hasattr(attack_ctx, 'is_hit') else False,
                "is_critical": attack_ctx.is_critical if hasattr(attack_ctx, 'is_critical') else False
            }
        
        # 法术信息
        if hasattr(action, 'spell') and action.spell and action.spell_context:
            spell_ctx = action.spell_context
            spell_data = {
                "caster_id": spell_ctx.caster.id if spell_ctx.caster else None,
                "spell_name": spell_ctx.spell.name if spell_ctx.spell else None,
                "spell_id": spell_ctx.spell.id if spell_ctx.spell else None,
                "effect_type": spell_ctx.spell.effect_type.value if spell_ctx.spell and spell_ctx.spell.effect_type else None,
                "is_delay_spell": spell_ctx.is_delay_spell if hasattr(spell_ctx, 'is_delay_spell') else False,
                "spell_lifespan": spell_ctx.spell_lifespan if hasattr(spell_ctx, 'spell_lifespan') else 0
            }
            
            if spell_ctx.target:
                spell_data["target_id"] = spell_ctx.target.id
            if spell_ctx.target_area:
                spell_data["target_area"] = {
                    "x": spell_ctx.target_area.x,
                    "y": spell_ctx.target_area.y,
                    "radius": spell_ctx.target_area.radius
                }
            if hasattr(spell_ctx, 'hit_pieces') and spell_ctx.hit_pieces:
                spell_data["hit_pieces"] = [p.id for p in spell_ctx.hit_pieces]
            
            action_data["spell"] = spell_data
        
        return action_data
    
    @staticmethod
    def serialize_board_state(board: 'Board') -> Dict:
        """序列化棋盘状态"""
        return {
            "width": board.width,
            "height": board.height,
            "height_map": board.height_map.tolist() if board.height_map is not None else None,
            "boarder": board.boarder
        }
    
    @staticmethod
    def serialize_all_pieces(action_queue: List['Piece']) -> List[Dict]:
        """序列化所有棋子状态"""
        pieces = []
        for piece in action_queue:
            if piece:
                pieces.append(ReplaySerializer.serialize_piece(piece))
        return pieces
    
    @staticmethod
    def serialize_delayed_spells(delayed_spells: List['SpellContext']) -> List[Dict]:
        """序列化延时法术列表"""
        spells = []
        for spell_ctx in delayed_spells:
            if spell_ctx:
                spell_data = {
                    "caster_id": spell_ctx.caster.id if spell_ctx.caster else None,
                    "spell_name": spell_ctx.spell.name if spell_ctx.spell else None,
                    "spell_id": spell_ctx.spell.id if spell_ctx.spell else None,
                    "spell_lifespan": spell_ctx.spell_lifespan if hasattr(spell_ctx, 'spell_lifespan') else 0,
                    "target_area": {
                        "x": spell_ctx.target_area.x,
                        "y": spell_ctx.target_area.y,
                        "radius": spell_ctx.target_area.radius
                    } if spell_ctx.target_area else None
                }
                spells.append(spell_data)
        return spells
    
    @staticmethod
    def record_round(env: 'Environment', action: 'ActionSet') -> Dict:
        """记录本回合的回放信息"""
        return {
            "round_number": env.round_number,
            "current_piece": ReplaySerializer.serialize_piece(env.current_piece) if env.current_piece else None,
            "action": ReplaySerializer.serialize_action(action) if action else None,
            "board_state": ReplaySerializer.serialize_board_state(env.board),
            "pieces_state": ReplaySerializer.serialize_all_pieces(env.action_queue),
            "delayed_spells": ReplaySerializer.serialize_delayed_spells(env.delayed_spells),
            "new_dead_pieces": [ReplaySerializer.serialize_piece(p) for p in env.last_round_dead_pieces],
            "is_game_over": env.is_game_over
        }


class ReplayDeserializer:
    """回放反序列化器"""
    
    @staticmethod
    def deserialize_piece(piece_data: Dict, env: 'Environment' = None) -> Optional['Piece']:
        """反序列化棋子信息"""
        if piece_data is None:
            return None
        
        from env import Piece
        
        piece = Piece()
        piece.id = piece_data.get("id", 0)
        piece.team = piece_data.get("team", 0)
        piece.type = piece_data.get("type", "")
        piece.position = Point(
            piece_data["position"]["x"],
            piece_data["position"]["y"]
        )
        piece.height = piece_data.get("height", 0)
        piece.health = piece_data.get("health", 0)
        piece.max_health = piece_data.get("max_health", 0)
        piece.action_points = piece_data.get("action_points", 0)
        piece.max_action_points = piece_data.get("max_action_points", 0)
        piece.spell_slots = piece_data.get("spell_slots", 0)
        piece.max_spell_slots = piece_data.get("max_spell_slots", 0)
        piece.movement = piece_data.get("movement", 0.0)
        piece.max_movement = piece_data.get("max_movement", 0.0)
        piece.physical_damage = piece_data.get("physical_damage", 0)
        piece.magic_damage = piece_data.get("magic_damage", 0)
        piece.physical_resist = piece_data.get("physical_resist", 0)
        piece.magic_resist = piece_data.get("magic_resist", 0)
        piece.strength = piece_data.get("strength", 0)
        piece.dexterity = piece_data.get("dexterity", 0)
        piece.intelligence = piece_data.get("intelligence", 0)
        piece.attack_range = piece_data.get("attack_range", 0)
        piece.is_alive = piece_data.get("is_alive", True)
        piece.is_dying = piece_data.get("is_dying", False)
        piece.death_round = piece_data.get("death_round", -1)
        
        return piece
    
    @staticmethod
    def deserialize_action(action_data: Dict, env: 'Environment' = None) -> Optional['ActionSet']:
        """反序列化行动信息"""
        if action_data is None:
            return None
        
        action = ActionSet()
        
        # 移动信息
        if "move" in action_data:
            move_data = action_data["move"]
            if "target" in move_data:
                action.move_target = Point(
                    move_data["target"]["x"],
                    move_data["target"]["y"]
                )
                action.move = True
        
        # 攻击信息
        if "attack" in action_data:
            attack_data = action_data["attack"]
            action.attack = True
            action.attack_context = AttackContext()
            if env:
                # 尝试从环境中找到对应的棋子
                attacker_id = attack_data.get("attacker_id")
                target_id = attack_data.get("target_id")
                if attacker_id:
                    for piece in env.action_queue:
                        if piece.id == attacker_id:
                            action.attack_context.attacker = piece
                            break
                if target_id:
                    for piece in env.action_queue:
                        if piece.id == target_id:
                            action.attack_context.target = piece
                            break
            action.attack_context.damage_dealt = attack_data.get("damage_dealt", 0)
            if hasattr(action.attack_context, 'is_hit'):
                action.attack_context.is_hit = attack_data.get("is_hit", False)
            if hasattr(action.attack_context, 'is_critical'):
                action.attack_context.is_critical = attack_data.get("is_critical", False)
        
        # 法术信息
        if "spell" in action_data:
            spell_data = action_data["spell"]
            action.spell = True
            action.spell_context = SpellContext()
            
            if env:
                # 尝试从环境中找到对应的棋子
                caster_id = spell_data.get("caster_id")
                target_id = spell_data.get("target_id")
                if caster_id:
                    for piece in env.action_queue:
                        if piece.id == caster_id:
                            action.spell_context.caster = piece
                            break
                if target_id:
                    for piece in env.action_queue:
                        if piece.id == target_id:
                            action.spell_context.target = piece
                            break
            
            # 恢复法术对象
            from utils import SpellFactory
            spell_id = spell_data.get("spell_id")
            if spell_id:
                action.spell_context.spell = SpellFactory.get_spell_by_id(spell_id)
            
            # 恢复目标区域
            if "target_area" in spell_data and spell_data["target_area"]:
                area_data = spell_data["target_area"]
                action.spell_context.target_area = Area(
                    area_data["x"],
                    area_data["y"],
                    area_data["radius"]
                )
            
            action.spell_context.is_delay_spell = spell_data.get("is_delay_spell", False)
            action.spell_context.spell_lifespan = spell_data.get("spell_lifespan", 0)
        
        return action
    
    @staticmethod
    def deserialize_board_state(board_data: Dict) -> 'Board':
        """反序列化棋盘状态"""
        from env import Board
        
        board = Board(if_log=0)
        board.width = board_data.get("width", 0)
        board.height = board_data.get("height", 0)
        board.boarder = board_data.get("boarder", 0)
        
        if board_data.get("height_map"):
            height_map_list = board_data["height_map"]
            board.height_map = np.array(height_map_list, dtype=np.int32)
        else:
            board.height_map = np.zeros((board.width, board.height), dtype=np.int32)
        
        # 初始化grid（需要根据实际情况调整）
        from env import Cell
        board.grid = np.array([[Cell(1) for _ in range(board.height)] for _ in range(board.width)], dtype=object)
        
        return board
    
    @staticmethod
    def restore_game_state(env: 'Environment', round_data: Dict) -> None:
        """从回合数据恢复游戏状态
        
        Args:
            env: 要恢复到的环境对象
            round_data: 回合数据字典
        """
        # 恢复回合编号
        env.round_number = round_data.get("round_number", 0)
        env.is_game_over = round_data.get("is_game_over", False)
        
        # 恢复棋盘状态
        board_data = round_data.get("board_state")
        if board_data:
            env.board = ReplayDeserializer.deserialize_board_state(board_data)
        
        # 恢复所有棋子
        pieces_data = round_data.get("pieces_state", [])
        env.action_queue = np.array([], dtype=object)
        piece_dict = {}  # 用于建立ID到棋子的映射
        
        for piece_data in pieces_data:
            piece = ReplayDeserializer.deserialize_piece(piece_data, env)
            if piece:
                env.action_queue = np.append(env.action_queue, [piece])
                piece_dict[piece.id] = piece
        
        # 恢复当前棋子
        current_piece_data = round_data.get("current_piece")
        if current_piece_data:
            current_piece_id = current_piece_data.get("id")
            if current_piece_id in piece_dict:
                env.current_piece = piece_dict[current_piece_id]
        
        # 恢复玩家棋子列表
        env.player1.pieces = np.array([p for p in env.action_queue if p.team == 1], dtype=object)
        env.player2.pieces = np.array([p for p in env.action_queue if p.team == 2], dtype=object)
        
        # 恢复棋盘grid状态（根据棋子位置更新）
        if env.board and env.board.grid is not None:
            # 重置所有grid状态
            for x in range(env.board.width):
                for y in range(env.board.height):
                    env.board.grid[x][y].state = 1  # 默认可行走
                    env.board.grid[x][y].player_id = -1
                    env.board.grid[x][y].piece_id = -1
            
            # 根据棋子位置更新grid
            for piece in env.action_queue:
                if piece.is_alive:
                    x, y = piece.position.x, piece.position.y
                    if 0 <= x < env.board.width and 0 <= y < env.board.height:
                        env.board.grid[x][y].state = 2  # 占据
                        env.board.grid[x][y].player_id = piece.team
                        env.board.grid[x][y].piece_id = piece.id
        
        # 恢复延时法术
        delayed_spells_data = round_data.get("delayed_spells", [])
        env.delayed_spells = np.array([], dtype=object)
        for spell_data in delayed_spells_data:
            spell_ctx = SpellContext()
            spell_id = spell_data.get("spell_id")
            if spell_id:
                from utils import SpellFactory
                spell_ctx.spell = SpellFactory.get_spell_by_id(spell_id)
            spell_ctx.spell_lifespan = spell_data.get("spell_lifespan", 0)
            if spell_data.get("target_area"):
                area_data = spell_data["target_area"]
                spell_ctx.target_area = Area(area_data["x"], area_data["y"], area_data["radius"])
            caster_id = spell_data.get("caster_id")
            if caster_id and caster_id in piece_dict:
                spell_ctx.caster = piece_dict[caster_id]
            env.delayed_spells = np.append(env.delayed_spells, [spell_ctx])
        
        # 恢复死亡棋子列表
        dead_pieces_data = round_data.get("new_dead_pieces", [])
        env.last_round_dead_pieces = np.array([], dtype=object)
        for dead_piece_data in dead_pieces_data:
            dead_piece_id = dead_piece_data.get("id")
            if dead_piece_id in piece_dict:
                env.last_round_dead_pieces = np.append(env.last_round_dead_pieces, [piece_dict[dead_piece_id]])
        
        env.new_dead_this_round = np.array([], dtype=object)


class ReplayManager:
    """回放管理器"""
    
    def __init__(self, env: 'Environment'):
        self.env = env
        self.replay_data = []
    
    def record_round(self, action: 'ActionSet') -> None:
        """记录本回合的回放信息"""
        round_data = ReplaySerializer.record_round(self.env, action)
        self.replay_data.append(round_data)
    
    def save_to_json(self, filepath: str = None) -> str:
        """保存回放数据到JSON文件
        
        Args:
            filepath: 保存路径，如果为None则自动生成文件名
            
        Returns:
            str: 保存的文件路径
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"replay_{timestamp}.json"
        
        replay_file = {
            "game_info": {
                "total_rounds": self.env.round_number,
                "is_game_over": self.env.is_game_over,
                "winner": 1 if self.env.is_game_over and any(p.is_alive for p in self.env.player1.pieces) else 
                           (2 if self.env.is_game_over and any(p.is_alive for p in self.env.player2.pieces) else None)
            },
            "rounds": self.replay_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(replay_file, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)
        
        if self.env.if_log:
            print(f"[Replay] 回放数据已保存到: {filepath}")
        
        return filepath
    
    @staticmethod
    def load_from_json(filepath: str) -> Dict:
        """从JSON文件加载回放数据
        
        Args:
            filepath: JSON文件路径
            
        Returns:
            Dict: 回放数据字典
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            replay_data = json.load(f)
        return replay_data
    
    @staticmethod
    def restore_to_round(env: 'Environment', replay_data: Dict, target_round: int) -> bool:
        """将游戏状态恢复到指定回合
        
        Args:
            env: 要恢复到的环境对象
            replay_data: 回放数据字典
            target_round: 目标回合编号（从1开始）
            
        Returns:
            bool: 是否成功恢复
        """
        rounds = replay_data.get("rounds", [])
        if target_round < 1 or target_round > len(rounds):
            return False
        
        # 恢复到目标回合的状态
        round_data = rounds[target_round - 1]
        ReplayDeserializer.restore_game_state(env, round_data)
        
        return True
    
    @staticmethod
    def restore_to_end(env: 'Environment', replay_data: Dict) -> bool:
        """将游戏状态恢复到结束状态
        
        Args:
            env: 要恢复到的环境对象
            replay_data: 回放数据字典
            
        Returns:
            bool: 是否成功恢复
        """
        rounds = replay_data.get("rounds", [])
        if not rounds:
            return False
        
        # 恢复到最后一回合的状态
        round_data = rounds[-1]
        ReplayDeserializer.restore_game_state(env, round_data)
        
        return True

