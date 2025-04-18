#pragma once
#include <vector>
#include <Player.h>
#include "utils.h"

class Piece
{
public:
    int health;
    int max_health;
    int physical_resist;
    int magic_resist;
    DicePair physical_damage;
    DicePair magic_damage;
    int action_points;
    int max_action_points;
    int spell_slots;
    int max_spell_slots;
    float movement;
    float max_movement;

    int strength;
    int dexterity;
    int intelligence;

    Point position;
    int height;
    int attack_range;
    std::vector<Spell> spell_list;

    int team;
    int queue_index;
    bool is_alive;
    bool is_in_turn;
    bool is_dying;
    double spell_range;

    Piece() : health(0), max_health(0), physical_resist(0), magic_resist(0),
                     action_points(0), max_action_points(0), spell_slots(0), max_spell_slots(0),
                     movement(0), max_movement(0), strength(0), dexterity(0), intelligence(0),
                     height(0), attack_range(0), team(0), queue_index(0), is_alive(true),
                     is_in_turn(false), is_dying(false), spell_range(0.0) {}
};

class Board
{
private:
    int width, height;
    std::vector<std::vector<int>> grid;
    std::vector<std::vector<int>> height_map;

public:
    Board() : width(0), height(0) {}
    Board(int width, int height) : width(width), height(height)
    {
        grid.resize(width, std::vector<int>(height, 0));
        height_map.resize(width, std::vector<int>(height, 0));
    }
};

class Env
{
private:
    std::vector<Piece> action_queue;
    Piece current_piece;
    int round_number;
    std::vector<SpellContext> delayed_spells;
    Player player1;
    Player player2;
    Board board;
    bool isGameOver;

public:
    Env() : round_number(0), isGameOver(false) {}
};