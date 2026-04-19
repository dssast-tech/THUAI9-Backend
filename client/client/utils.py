import math
import numpy as np
from enum import Enum
from typing import Optional, List


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class ActionSet:
    def __init__(self):
        self.move_target = Point()
        self.attack = False
        self.attack_context = None  # AttackContext
        self.spell = False
        self.spell_context = None  # SpellContext
        
    def __str__(self) -> str:
        """返回动作集的可读字符串表示"""
        parts = []
        
        # 移动部分
        if hasattr(self, 'move_target'):
            parts.append(f"移动: {'是' if hasattr(self, 'move') and self.move else '否'}")
            if hasattr(self, 'move') and self.move:
                parts.append(f"  目标位置: ({self.move_target.x}, {self.move_target.y})")
        
        # 攻击部分
        if hasattr(self, 'attack'):
            parts.append(f"攻击: {'是' if self.attack else '否'}")
            if self.attack and self.attack_context:
                parts.append("  攻击详情:")
                if hasattr(self.attack_context, 'attacker') and self.attack_context.attacker:
                    parts.append(f"    攻击者ID: {self.attack_context.attacker.id}")
                if hasattr(self.attack_context, 'target') and self.attack_context.target:
                    parts.append(f"    目标ID: {self.attack_context.target.id}")
                if hasattr(self.attack_context, 'damage_dealt'):
                    parts.append(f"    伤害值: {self.attack_context.damage_dealt}")
        
        # 法术部分
        if hasattr(self, 'spell'):
            parts.append(f"法术: {'是' if self.spell else '否'}")
            if self.spell and self.spell_context:
                parts.append("  法术详情:")
                if hasattr(self.spell_context, 'spell') and self.spell_context.spell:
                    parts.append(f"    名称: {self.spell_context.spell.name}")
                    parts.append(f"    效果类型: {self.spell_context.spell.effect_type.value if self.spell_context.spell.effect_type else 'Unknown'}")
                    parts.append(f"    基础值: {self.spell_context.spell.base_value}")
                if hasattr(self.spell_context, 'target') and self.spell_context.target:
                    parts.append(f"    目标ID: {self.spell_context.target.id}")
                if hasattr(self.spell_context, 'target_area') and self.spell_context.target_area:
                    parts.append(f"    目标区域: ({self.spell_context.target_area.x}, {self.spell_context.target_area.y}), 半径: {self.spell_context.target_area.radius}")
        
        return "\n".join(parts)


class InitializationSet:
    """用于棋子初始化的信息"""

    def __init__(self, strength=0, dexterity=0, intelligence=0, weapon=0, armor=0, position=None):
        """
        :param strength: 力量属性
        :param dexterity: 敏捷属性
        :param intelligence: 智力属性
        :param weapon: 武器类型 (1~长剑, 2~短剑, 3~弓, 4~法杖)
        :param armor: 防具类型 (1~轻甲, 2~中甲, 3~重甲)
        :param position: 初始位置 (Point 对象)
        """
        self.strength = strength
        self.dexterity = dexterity
        self.intelligence = intelligence
        self.weapon = weapon
        self.armor = armor
        self.position = position if position else Point()

    def to_dict(self):
        """将 InitializationSet 转换为字典格式"""
        return {
            "strength": self.strength,
            "dexterity": self.dexterity,
            "intelligence": self.intelligence,
            "weapon": self.weapon,
            "armor": self.armor,
            "position": {"x": self.position.x, "y": self.position.y},
        }

    @staticmethod
    def from_dict(data):
        """从字典格式解析为 InitializationSet 对象"""
        return InitializationSet(
            strength=data.get("strength", 0),
            dexterity=data.get("dexterity", 0),
            intelligence=data.get("intelligence", 0),
            weapon=data.get("weapon", 0),
            armor=data.get("armor", 0),
            position=Point(data["position"]["x"], data["position"]["y"]) if "position" in data else Point(),
        )


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
        self.piece_args = []  # 使用列表以支持PieceArg对象
        
class AttackContext:
    def __init__(self):
        self.attacker = None  # Piece
        self.target = None  # Piece
        self.attack_type = None  # AttackType
        self.is_critical = False
        self.damage_dealt = 0
        self.is_hit = False
        self.advantage_value = 0
        self.attack_position = Point()
        self.attack_roll = 0
        self.defense_value = 0
        self.caused_death = False
        self.death_roll = 0


class AttackType(Enum):
    PHYSICAL = "Physical"
    SPELL = "Spell"
    EXCELLENCE = "Excellence"


class SpellContext:
    def __init__(self):
        self.caster = None  # Piece
        self.spell = None  # Spell
        self.spell_power = 0
        self.target_type = None  # TargetType
        self.target = None  # Piece
        self.target_area = None  # Area
        self.spell_range = 0.0
        self.effect_type = None  # SpellEffectType
        self.damage_type = None  # DamageType
        self.damage_value = 0
        self.heal_value = 0
        self.effect_value = 0
        self.is_delay_spell = False
        self.base_lifespan = 0
        self.spell_lifespan = 0
        self.is_damage_spell = False
        self.is_area_effect = False
        self.is_locking_spell = False
        self.spell_cost = 0
        self.action_cost = 0
        self.is_hit = False
        self.is_critical = False


class TargetType(Enum):
    SINGLE = "Single"
    AREA = "Area"
    SELF = "Self"
    CHAIN = "Chain"


class SpellEffectType(Enum):
    DAMAGE = "Damage"
    HEAL = "Heal"
    BUFF = "Buff"
    DEBUFF = "Debuff"
    MOVE = "Move"


class DamageType(Enum):
    FIRE = "Fire"
    ICE = "Ice"
    LIGHTNING = "Lightning"
    PHYSICAL = "Physical"
    PURE = "Pure"
    NONE = "None"


class Area:
    def __init__(self, x=0, y=0, radius=0):
        self.x = x
        self.y = y
        self.radius = radius

    def contains(self, point):
        distance = np.sqrt((point.x - self.x) ** 2 + (point.y - self.y) ** 2)
        return distance <= self.radius


class Spell:
    def __init__(self, id=0, name="", description="", effect_type=None, damage_type=None, base_value=0,
                 range_=0, area_radius=0, spell_cost=0, base_lifespan=0, is_area_effect=False,
                 is_delay_spell=False, is_locking_spell=False):
        self.id = id
        self.name = name
        self.description = description
        self.effect_type = effect_type
        self.damage_type = damage_type
        self.base_value = base_value
        self.range = range_
        self.area_radius = area_radius
        self.spell_cost = spell_cost
        self.base_lifespan = base_lifespan
        self.is_area_effect = is_area_effect
        self.is_delay_spell = is_delay_spell
        self.is_locking_spell = is_locking_spell


class SpellFactory:
    """法术工厂类，提供所有可用的法术"""
    
    @staticmethod
    def get_all_spells() -> List[Spell]:
        """获取所有可用的法术列表"""
        return [
            Spell(
                id=1,
                name="Fireball",
                description="对范围内敌人造成火焰伤害",
                effect_type=SpellEffectType.DAMAGE,
                damage_type=DamageType.FIRE,
                base_value=30,
                range_=12,
                area_radius=5,
                spell_cost=1,
                base_lifespan=0,
                is_area_effect=True,
                is_delay_spell=False,
                is_locking_spell=False
            ),
            Spell(
                id=2,
                name="Heal",
                description="治疗友方单位",
                effect_type=SpellEffectType.HEAL,
                damage_type=DamageType.NONE,
                base_value=30,
                range_=5,
                area_radius=4,
                spell_cost=1,
                base_lifespan=0,
                is_area_effect=False,
                is_delay_spell=False,
                is_locking_spell=True
            ),
            Spell(
                id=3,
                name="Arrow Hit",
                description="箭击",
                effect_type=SpellEffectType.DAMAGE,
                damage_type=DamageType.PHYSICAL,
                base_value=30,
                range_=9,
                area_radius=7,
                spell_cost=1,
                base_lifespan=0,
                is_area_effect=False,
                is_delay_spell=False,
                is_locking_spell=True
            ),
            Spell(
                id=4,
                name="Trap",
                description="陷阱",
                effect_type=SpellEffectType.DAMAGE,
                damage_type=DamageType.PHYSICAL,
                base_value=30,
                range_=3,
                area_radius=0,
                spell_cost=1,
                base_lifespan=2,
                is_area_effect=False,
                is_delay_spell=True,
                is_locking_spell=False
            ),
            Spell(
                id=5,
                name="Teleport",
                description="瞬间移动",
                effect_type=SpellEffectType.MOVE,
                damage_type=DamageType.PHYSICAL,
                base_value=30,
                range_=100,
                area_radius=100,
                spell_cost=1,
                base_lifespan=2,
                is_area_effect=False,
                is_delay_spell=False,
                is_locking_spell=True
            )
        ]
    
    @staticmethod
    def get_spell_by_id(spell_id: int) -> Optional[Spell]:
        """根据ID获取法术"""
        return next((spell for spell in SpellFactory.get_all_spells() if spell.id == spell_id), None)
    
    @staticmethod
    def get_available_spells(piece) -> List[Spell]:
        """获取指定棋子可用的法术列表
        
        根据棋子类型和属性返回可用的法术列表：
        - 战士：主要是物理伤害和增益法术
        - 法师：主要是魔法伤害和控制法术
        - 弓箭手：主要是远程攻击和陷阱法术
        """
        all_spells = SpellFactory.get_all_spells()
        available_spells = []
        
        # 根据棋子类型筛选法术
        if piece.type == "Warrior":
            available_spells.extend([
                spell for spell in all_spells
                if spell.damage_type == DamageType.PHYSICAL
                or spell.effect_type == SpellEffectType.BUFF
            ])
        elif piece.type == "Mage":
            available_spells.extend([
                spell for spell in all_spells
                if spell.damage_type in [DamageType.FIRE, DamageType.ICE, DamageType.LIGHTNING]
                or spell.effect_type in [SpellEffectType.DAMAGE, SpellEffectType.DEBUFF]
            ])
        elif piece.type == "Archer":
            available_spells.extend([
                spell for spell in all_spells
                if spell.name in ["Arrow Hit", "Trap"]
                or spell.effect_type == SpellEffectType.MOVE
            ])
            
        # 根据智力值限制法术数量
        max_spells = piece.intelligence // 5 + 1
        return available_spells[:max_spells]

