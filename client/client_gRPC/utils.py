import math
from enum import Enum


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


class Message:
    """通信预留转接类"""
    pass


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
        distance = math.sqrt((point.x - self.x) ** 2 + (point.y - self.y) ** 2)
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
