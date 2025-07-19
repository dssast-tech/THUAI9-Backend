#pragma once
#include <vector>
#include <memory>
#include "utils.h"

class Player {
public:
    int id = -1;
    std::vector<std::shared_ptr<Piece>> pieces;
};

class Piece {
public:
    int health = 0;
    int max_health = 0;
    int physical_resist = 0;
    int magic_resist = 0;
    int physical_damage = 0;
    int magic_damage = 0;
    int action_points = 0;
    int max_action_points = 0;
    int spell_slots = 0;
    int max_spell_slots = 0;
    float movement = 0.0f;
    float max_movement = 0.0f;
    int id = 0;
    int strength = 0;
    int dexterity = 0;
    int intelligence = 0;
    Point position{0, 0};
    int height = 0;
    int attack_range = 0;
    std::vector<int> spell_list;
    int team = 0;
    int queue_index = 0;
    bool is_alive = true;
    bool is_in_turn = false;
    bool is_dying = false;
    double spell_range = 0.0;
};

struct Cell {
    int state = 1;  // 默认为可行走
    int player_id = -1;  // 默认无人
    int piece_id = -1;  // 默认无棋子
};

class Board {
public:
    int width = 0;
    int height = 0;
    std::vector<std::vector<Cell>> grid;
    std::vector<std::vector<int>> height_map;
    int boarder = 0;  // 分界线为高度的一半

    Board(int w = 0, int h = 0) : width(w), height(h) {
        grid.resize(w, std::vector<Cell>(h));
        height_map.resize(w, std::vector<int>(h, 0));
        boarder = h / 2;
    }

    bool is_within_bounds(const Point& p) const {
        return p.x >= 0 && p.x < width && p.y >= 0 && p.y < height;
    }

    bool is_occupied(const Point& p) const {
        return grid[p.x][p.y].state == 2;
    }

    int get_height(const Point& p) const {
        return height_map[p.x][p.y];
    }
};

class Env {
public:
    std::vector<std::shared_ptr<Piece>> action_queue;
    std::shared_ptr<Piece> current_piece;
    int round_number = 0;
    std::vector<std::shared_ptr<SpellContext>> delayed_spells;
    std::shared_ptr<Player> player1;
    std::shared_ptr<Player> player2;
    std::shared_ptr<Board> board;
    bool is_game_over = false;

    Env() : board(std::make_shared<Board>()) {}
};

class InitGameMessage {
public:
    int piece_cnt = 0;
    int id = 0;
    std::shared_ptr<Board> board;
};

class PieceArg {
public:
    int strength = 0;
    int intelligence = 0;
    int dexterity = 0;
    Point equip{0, 0};
    Point pos{0, 0};
};

class InitPolicyMessage {
public:
    std::vector<PieceArg> piece_args;
}; 