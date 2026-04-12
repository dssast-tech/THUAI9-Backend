#pragma once
#include <cmath>
#include <memory>

struct Point {
    int x = 0;
    int y = 0;
    
    Point(int x_ = 0, int y_ = 0) : x(x_), y(y_) {}
};

class ActionSet {
public:
    Point move_target;
    bool attack = false;
    std::shared_ptr<AttackContext> attack_context;
    bool spell = false;
    std::shared_ptr<SpellContext> spell_context;
};

class InitializationSet {
public:
    int strength = 0;
    int dexterity = 0;
    int intelligence = 0;
    int weapon = 0;
    int armor = 0;
    Point position;
};

enum class AttackType {
    Physical,
    Spell,
    Excellence
};

class AttackContext {
public:
    std::shared_ptr<class Piece> attacker;
    std::shared_ptr<class Piece> target;
    AttackType attack_type;
    bool is_critical = false;
    int damage_dealt = 0;
    bool is_hit = false;
    int advantage_value = 0;
    Point attack_position;
    int attack_roll = 0;
    int defense_value = 0;
    bool caused_death = false;
    int death_roll = 0;
};

enum class TargetType {
    Single,
    Area,
    Self,
    Chain
};

enum class SpellEffectType {
    Damage,
    Heal,
    Buff,
    Debuff,
    Move
};

enum class DamageType {
    Fire,
    Ice,
    Lightning,
    Physical,
    Pure,
    None
};

struct Area {
    int x = 0;
    int y = 0;
    int radius = 0;

    bool contains(const Point& point) const {
        double distance = std::abs(point.x - x) + std::abs(point.y - y);
        return distance <= radius;
    }
};

class SpellContext {
public:
    std::shared_ptr<class Piece> caster;
    std::shared_ptr<class Spell> spell;
    int spell_power = 0;
    TargetType target_type;
    std::shared_ptr<class Piece> target;
    std::shared_ptr<Area> target_area;
    double spell_range = 0.0;
    SpellEffectType effect_type;
    DamageType damage_type;
    int damage_value = 0;
    int heal_value = 0;
    int effect_value = 0;
    bool is_delay_spell = false;
    int base_lifespan = 0;
    int spell_lifespan = 0;
    bool is_damage_spell = false;
    bool is_area_effect = false;
    bool is_locking_spell = false;
    int spell_cost = 0;
    int action_cost = 0;
    bool is_hit = false;
    bool is_critical = false;
};

class Spell {
public:
    int id = 0;
    std::string name;
    std::string description;
    SpellEffectType effect_type;
    DamageType damage_type;
    int base_value = 0;
    int range = 0;
    int area_radius = 0;
    int spell_cost = 0;
    int base_lifespan = 0;
    bool is_area_effect = false;
    bool is_delay_spell = false;
    bool is_locking_spell = false;
}; 