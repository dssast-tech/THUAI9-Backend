import numpy as np
from typing import List, Optional, Dict, Any
import message_pb2 as msg
from dataclasses import dataclass
from State import *
from utils import *

class Converter:
    @staticmethod
    def flatten_2d_array(array: List[List[Any]]) -> List[Any]:
        """将二维数组展平为一维数组"""
        return [item for row in array for item in row]

    @staticmethod
    def to_proto_point(py_point: Point) -> msg._Point:
        """将Python Point对象转换为protobuf Point消息"""
        return msg._Point(x=py_point.x, y=py_point.y)

    @staticmethod
    def from_proto_point(proto_point: msg._Point) -> Point:
        """将protobuf Point消息转换为Python Point对象"""
        return Point(x=proto_point.x, y=proto_point.y)

    @staticmethod
    def to_proto_piece_args(py_piece_args: List[PieceArg]) -> List[msg._pieceArg]:
        """将Python PieceArg列表转换为protobuf _pieceArg列表
        
        Args:
            py_piece_args: Python格式的棋子参数列表
            
        Returns:
            protobuf格式的棋子参数列表
        """
        return [Converter.to_proto_piece_arg(arg) for arg in py_piece_args]

    @staticmethod
    def from_proto_piece_args(proto_piece_args: List[msg._pieceArg]) -> List[PieceArg]:
        """将protobuf _pieceArg列表转换为Python PieceArg列表
        
        Args:
            proto_piece_args: protobuf格式的棋子参数列表
            
        Returns:
            Python格式的棋子参数列表
        """
        return [Converter.from_proto_piece_arg(arg) for arg in proto_piece_args]

    @staticmethod
    def to_proto_cell(py_cell: Cell) -> msg._Cell:
        """将Python Cell对象转换为protobuf Cell消息"""
        return msg._Cell(
            state=py_cell.state,
            playerId=py_cell.playerId,
            pieceId=py_cell.pieceId
        )

    @staticmethod
    def from_proto_cell(proto_cell: msg._Cell) -> Cell:
        """将protobuf Cell消息转换为Python Cell对象"""
        return Cell(
            state=proto_cell.state,
            playerId=proto_cell.playerId,
            pieceId=proto_cell.pieceId
        )

    @staticmethod
    def to_proto_board(py_board: Board) -> msg._Board:
        """将Python Board对象转换为protobuf Board消息"""
        proto_board = msg._Board(
            width=py_board.width,
            height=py_board.height,
            boarder=py_board.boarder
        )
        
        # 转换grid
        grid_flat = py_board.grid.flatten()
        proto_board.grid.extend([Converter.to_proto_cell(cell) for cell in grid_flat])
        
        # 转换height_map
        proto_board.height_map.extend(py_board.height_map.flatten())
        
        return proto_board

    @staticmethod
    def from_proto_board(proto_board: msg._Board) -> Board:
        """将protobuf Board消息转换为Python Board对象"""
        board = Board(width=proto_board.width, height=proto_board.height)
        
        # 转换grid
        grid_1d = np.array([Converter.from_proto_cell(cell) for cell in proto_board.grid], dtype=object)
        board.grid = grid_1d.reshape(proto_board.width, proto_board.height)
        
        # 转换height_map
        board.height_map = np.array(proto_board.height_map).reshape(proto_board.width, proto_board.height)
        
        board.boarder = proto_board.boarder
        return board

    @staticmethod
    def to_proto_area(py_area: Area) -> msg._Area:
        """将Python Area对象转换为protobuf Area消息"""
        return msg._Area(
            x=py_area.x,
            y=py_area.y,
            radius=py_area.radius
        )

    @staticmethod
    def from_proto_area(proto_area: msg._Area) -> Area:
        """将protobuf Area消息转换为Python Area对象"""
        return Area(
            x=proto_area.x,
            y=proto_area.y,
            radius=proto_area.radius
        )

    @staticmethod
    def to_proto_piece(py_piece: Piece) -> msg._Piece:
        """将Python Piece对象转换为protobuf Piece消息"""
        proto_piece = msg._Piece(
            health=py_piece.health,
            max_health=py_piece.max_health,
            physical_resist=py_piece.physical_resist,
            magic_resist=py_piece.magic_resist,
            physical_damage=py_piece.physical_damage,
            magic_damage=py_piece.magic_damage,
            action_points=py_piece.action_points,
            max_action_points=py_piece.max_action_points,
            spell_slots=py_piece.spell_slots,
            max_spell_slots=py_piece.max_spell_slots,
            movement=py_piece.movement,
            max_movement=py_piece.max_movement,
            id=py_piece.id,
            strength=py_piece.strength,
            dexterity=py_piece.dexterity,
            intelligence=py_piece.intelligence,
            position=Converter.to_proto_point(py_piece.position),
            height=py_piece.height,
            attack_range=py_piece.attack_range,
            deathRound=py_piece.deathRound,
            team=py_piece.team,
            queue_index=py_piece.queue_index,
            is_alive=py_piece.is_alive,
            is_in_turn=py_piece.is_in_turn,
            is_dying=py_piece.is_dying,
            spell_range=py_piece.spell_range
        )
        proto_piece.spell_list.extend(py_piece.spell_list)
        return proto_piece

    @staticmethod
    def from_proto_piece(proto_piece: msg._Piece) -> Piece:
        """将protobuf Piece消息转换为Python Piece对象"""
        piece = Piece()
        # 使用属性赋值
        piece.health = proto_piece.health
        piece.max_health = proto_piece.max_health
        piece.physical_resist = proto_piece.physical_resist
        piece.magic_resist = proto_piece.magic_resist
        piece.physical_damage = proto_piece.physical_damage
        piece.magic_damage = proto_piece.magic_damage
        piece.action_points = proto_piece.action_points
        piece.max_action_points = proto_piece.max_action_points
        piece.spell_slots = proto_piece.spell_slots
        piece.max_spell_slots = proto_piece.max_spell_slots
        piece.movement = proto_piece.movement
        piece.max_movement = proto_piece.max_movement
        piece.id = proto_piece.id
        piece.strength = proto_piece.strength
        piece.dexterity = proto_piece.dexterity
        piece.intelligence = proto_piece.intelligence
        piece.position = Converter.from_proto_point(proto_piece.position)
        piece.height = proto_piece.height
        piece.attack_range = proto_piece.attack_range
        piece.spell_list = np.array(proto_piece.spell_list, dtype=int)
        piece.team = proto_piece.team
        piece.queue_index = proto_piece.queue_index
        piece.is_alive = proto_piece.is_alive
        piece.is_in_turn = proto_piece.is_in_turn
        piece.is_dying = proto_piece.is_dying
        piece.spell_range = proto_piece.spell_range
        return piece

    @staticmethod
    def to_proto_piece_arg(py_piece_arg: PieceArg) -> msg._pieceArg:
        """将Python PieceArg对象转换为protobuf pieceArg消息"""
        return msg._pieceArg(
            strength=py_piece_arg.strength,
            intelligence=py_piece_arg.intelligence,
            dexterity=py_piece_arg.dexterity,
            equip=Converter.to_proto_point(py_piece_arg.equip),
            pos=Converter.to_proto_point(py_piece_arg.pos)
        )

    @staticmethod
    def from_proto_piece_arg(proto_piece_arg: msg._pieceArg) -> PieceArg:
        """将protobuf pieceArg消息转换为Python PieceArg对象"""
        return PieceArg(
            strength=proto_piece_arg.strength,
            intelligence=proto_piece_arg.intelligence,
            dexterity=proto_piece_arg.dexterity,
            equip=Converter.from_proto_point(proto_piece_arg.equip),
            pos=Converter.from_proto_point(proto_piece_arg.pos)
        )

    @staticmethod
    def to_proto_attack_context(py_attack_context: AttackContext) -> msg._AttackContext:
        """将Python AttackContext对象转换为protobuf AttackContext消息"""
        return msg._AttackContext(
            attacker=py_attack_context.attacker,
            target=py_attack_context.target
        )

    @staticmethod
    def from_proto_attack_context(proto_attack_context: msg._AttackContext) -> AttackContext:
        """将protobuf AttackContext消息转换为Python AttackContext对象"""
        return AttackContext(
            attacker=proto_attack_context.attacker,
            target=proto_attack_context.target
        )

    @staticmethod
    def to_proto_spell_context(py_spell_context: SpellContext) -> msg._SpellContext:
        """将Python SpellContext对象转换为protobuf SpellContext消息"""
        proto_spell_context = msg._SpellContext(
            caster=py_spell_context.caster,
            spellID=py_spell_context.spellID,
            targetType=py_spell_context.targetType,
            target=py_spell_context.target,
            spellLifespan=py_spell_context.spellLifespan
        )
        if py_spell_context.targetArea:
            proto_spell_context.targetArea.CopyFrom(
                Converter.to_proto_area(py_spell_context.targetArea)
            )
        return proto_spell_context

    @staticmethod
    def from_proto_spell_context(proto_spell_context: msg._SpellContext) -> SpellContext:
        """将protobuf SpellContext消息转换为Python SpellContext对象"""
        target_area = None
        if proto_spell_context.HasField('targetArea'):
            target_area = Converter.from_proto_area(proto_spell_context.targetArea)
        
        return SpellContext(
            caster=proto_spell_context.caster,
            spellID=proto_spell_context.spellID,
            targetType=proto_spell_context.targetType,
            target=proto_spell_context.target,
            targetArea=target_area,
            spellLifespan=proto_spell_context.spellLifespan
        ) 

    @staticmethod
    def to_proto_action(py_action: ActionSet, player_id: int) -> msg._actionSet:
        """将Python ActionSet对象转换为protobuf _actionSet消息
        
        Args:
            py_action: Python格式的行动集合
            player_id: 玩家ID
            
        Returns:
            protobuf格式的行动集合
        """
        proto_action = msg._actionSet()
        proto_action.playerId = player_id  
        
        # 设置移动相关
        if hasattr(py_action, 'move_target') and py_action.move_target:
            proto_action.move = True
            proto_action.move_target.CopyFrom(Converter.to_proto_point(py_action.move_target))
        else:
            proto_action.move = False
        
        # 设置攻击相关
        proto_action.attack = py_action.attack
        if py_action.attack and py_action.attack_context:
            proto_action.attack_context.CopyFrom(
                Converter.to_proto_attack_context(py_action.attack_context)
            )
        
        # 设置法术相关
        proto_action.spell = py_action.spell
        if py_action.spell and py_action.spell_context:
            proto_action.spell_context.CopyFrom(
                Converter.to_proto_spell_context(py_action.spell_context)
            )
        
        return proto_action

    @staticmethod
    def from_proto_action(proto_action: msg._actionSet) -> ActionSet:
        """将protobuf _actionSet消息转换为Python ActionSet对象
        
        Args:
            proto_action: protobuf格式的行动集合
            
        Returns:
            Python格式的行动集合
        """
        py_action = ActionSet()
        
        # 转换移动相关
        if proto_action.move:
            py_action.move_target = Converter.from_proto_point(proto_action.move_target)
        
        # 转换攻击相关
        py_action.attack = proto_action.attack
        if proto_action.attack:
            py_action.attack_context = Converter.from_proto_attack_context(proto_action.attack_context)
        
        # 转换法术相关
        py_action.spell = proto_action.spell
        if proto_action.spell:
            py_action.spell_context = Converter.from_proto_spell_context(proto_action.spell_context)
        
        return py_action

    @staticmethod
    def from_proto_game_state(proto_state: msg._GameStateResponse, env) -> None:
        """将protobuf _GameStateResponse消息转换并更新到env对象中"""
        # 更新基本信息
        env.round_number = proto_state.currentRound
        env.is_game_over = proto_state.isGameOver
        
        # 更新棋盘
        if proto_state.board:
            env.board = Converter.from_proto_board(proto_state.board)
        # 更新行动队列
        env.action_queue = np.array([Converter.from_proto_piece(piece) for piece in proto_state.actionQueue], dtype=object)
        # 更新当前行动棋子
        for piece in env.action_queue:
            if piece.id == proto_state.currentPieceID:
                env.current_piece = piece
                break
        
        # 更新延迟法术
        env.delayed_spells = np.array([Converter.from_proto_spell_context(spell) for spell in proto_state.delayedSpells], dtype=object)
        # 更新玩家信息
        if not env.player1:
            env.player1 = Player()
            env.player1.id = 1
        if not env.player2:
            env.player2 = Player()
            env.player2.id = 2
        # 根据team属性分配棋子
        env.player1.pieces = np.array([piece for piece in env.action_queue if piece.team == 1], dtype=object)
        env.player2.pieces = np.array([piece for piece in env.action_queue if piece.team == 2], dtype=object)