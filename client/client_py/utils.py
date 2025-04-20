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
    """用于棋子初始化的信息，具体内容待定"""
    pass


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
