#pragma once
#include <memory>
#include <vector>
// #include "message.pb.h"
#include "State.h"
#include "utils.h"

class Converter {
public:
    static server::_Point to_proto_point(const Point& py_point) {
        server::_Point proto_point;
        proto_point.set_x(py_point.x);
        proto_point.set_y(py_point.y);
        return proto_point;
    }

    static Point from_proto_point(const server::_Point& proto_point) {
        return Point(proto_point.x(), proto_point.y());
    }

    static server::_Cell to_proto_cell(const Cell& py_cell) {
        server::_Cell proto_cell;
        proto_cell.set_state(py_cell.state);
        proto_cell.set_playerid(py_cell.player_id);
        proto_cell.set_pieceid(py_cell.piece_id);
        return proto_cell;
    }

    static Cell from_proto_cell(const server::_Cell& proto_cell) {
        Cell cell;
        cell.state = proto_cell.state();
        cell.player_id = proto_cell.playerid();
        cell.piece_id = proto_cell.pieceid();
        return cell;
    }

    static server::_Board to_proto_board(const std::shared_ptr<Board>& py_board) {
        server::_Board proto_board;
        proto_board.set_width(py_board->width);
        proto_board.set_height(py_board->height);
        proto_board.set_boarder(py_board->boarder);

        // 转换grid
        for (const auto& row : py_board->grid) {
            for (const auto& cell : row) {
                *proto_board.add_grid() = to_proto_cell(cell);
            }
        }

        // 转换height_map
        for (const auto& row : py_board->height_map) {
            for (int height : row) {
                proto_board.add_height_map(height);
            }
        }

        return proto_board;
    }

    static std::shared_ptr<Board> from_proto_board(const server::_Board& proto_board) {
        auto board = std::make_shared<Board>(proto_board.width(), proto_board.height());

        // 转换grid
        int idx = 0;
        for (int i = 0; i < board->width; ++i) {
            for (int j = 0; j < board->height; ++j) {
                board->grid[i][j] = from_proto_cell(proto_board.grid(idx++));
            }
        }

        // 转换height_map
        idx = 0;
        for (int i = 0; i < board->width; ++i) {
            for (int j = 0; j < board->height; ++j) {
                board->height_map[i][j] = proto_board.height_map(idx++);
            }
        }

        board->boarder = proto_board.boarder();
        return board;
    }

    static server::_Area to_proto_area(const Area& py_area) {
        server::_Area proto_area;
        proto_area.set_x(py_area.x);
        proto_area.set_y(py_area.y);
        proto_area.set_radius(py_area.radius);
        return proto_area;
    }

    static Area from_proto_area(const server::_Area& proto_area) {
        Area area;
        area.x = proto_area.x();
        area.y = proto_area.y();
        area.radius = proto_area.radius();
        return area;
    }

    static server::_Piece to_proto_piece(const std::shared_ptr<Piece>& py_piece) {
        server::_Piece proto_piece;
        proto_piece.set_health(py_piece->health);
        proto_piece.set_max_health(py_piece->max_health);
        proto_piece.set_physical_resist(py_piece->physical_resist);
        proto_piece.set_magic_resist(py_piece->magic_resist);
        proto_piece.set_physical_damage(py_piece->physical_damage);
        proto_piece.set_magic_damage(py_piece->magic_damage);
        proto_piece.set_action_points(py_piece->action_points);
        proto_piece.set_max_action_points(py_piece->max_action_points);
        proto_piece.set_spell_slots(py_piece->spell_slots);
        proto_piece.set_max_spell_slots(py_piece->max_spell_slots);
        proto_piece.set_movement(py_piece->movement);
        proto_piece.set_max_movement(py_piece->max_movement);
        proto_piece.set_id(py_piece->id);
        proto_piece.set_strength(py_piece->strength);
        proto_piece.set_dexterity(py_piece->dexterity);
        proto_piece.set_intelligence(py_piece->intelligence);
        *proto_piece.mutable_position() = to_proto_point(py_piece->position);
        proto_piece.set_height(py_piece->height);
        proto_piece.set_attack_range(py_piece->attack_range);
        for (int spell_id : py_piece->spell_list) {
            proto_piece.add_spell_list(spell_id);
        }
        proto_piece.set_team(py_piece->team);
        proto_piece.set_queue_index(py_piece->queue_index);
        proto_piece.set_is_alive(py_piece->is_alive);
        proto_piece.set_is_in_turn(py_piece->is_in_turn);
        proto_piece.set_is_dying(py_piece->is_dying);
        proto_piece.set_spell_range(py_piece->spell_range);
        return proto_piece;
    }

    static std::shared_ptr<Piece> from_proto_piece(const server::_Piece& proto_piece) {
        auto piece = std::make_shared<Piece>();
        piece->health = proto_piece.health();
        piece->max_health = proto_piece.max_health();
        piece->physical_resist = proto_piece.physical_resist();
        piece->magic_resist = proto_piece.magic_resist();
        piece->physical_damage = proto_piece.physical_damage();
        piece->magic_damage = proto_piece.magic_damage();
        piece->action_points = proto_piece.action_points();
        piece->max_action_points = proto_piece.max_action_points();
        piece->spell_slots = proto_piece.spell_slots();
        piece->max_spell_slots = proto_piece.max_spell_slots();
        piece->movement = proto_piece.movement();
        piece->max_movement = proto_piece.max_movement();
        piece->id = proto_piece.id();
        piece->strength = proto_piece.strength();
        piece->dexterity = proto_piece.dexterity();
        piece->intelligence = proto_piece.intelligence();
        piece->position = from_proto_point(proto_piece.position());
        piece->height = proto_piece.height();
        piece->attack_range = proto_piece.attack_range();
        piece->spell_list.assign(proto_piece.spell_list().begin(), proto_piece.spell_list().end());
        piece->team = proto_piece.team();
        piece->queue_index = proto_piece.queue_index();
        piece->is_alive = proto_piece.is_alive();
        piece->is_in_turn = proto_piece.is_in_turn();
        piece->is_dying = proto_piece.is_dying();
        piece->spell_range = proto_piece.spell_range();
        return piece;
    }

    static server::_actionSet to_proto_action(const ActionSet& py_action, int player_id) {
        server::_actionSet proto_action;
        proto_action.set_playerid(player_id);

        if (py_action.move_target.x != 0 || py_action.move_target.y != 0) {
            proto_action.set_move(true);
            *proto_action.mutable_move_target() = to_proto_point(py_action.move_target);
        } else {
            proto_action.set_move(false);
        }

        proto_action.set_attack(py_action.attack);
        if (py_action.attack && py_action.attack_context) {
            auto context = proto_action.mutable_attack_context();
            context->set_attacker(py_action.attack_context->attacker->id);
            context->set_target(py_action.attack_context->target->id);
        }

        proto_action.set_spell(py_action.spell);
        if (py_action.spell && py_action.spell_context) {
            auto context = proto_action.mutable_spell_context();
            context->set_caster(py_action.spell_context->caster->id);
            context->set_spellid(py_action.spell_context->spell->id);
            context->set_target(py_action.spell_context->target->id);
            if (py_action.spell_context->target_area) {
                *context->mutable_targetarea() = to_proto_area(*py_action.spell_context->target_area);
            }
            context->set_spelllifespan(py_action.spell_context->spell_lifespan);
        }

        return proto_action;
    }

    static void from_proto_game_state(const server::_GameStateResponse& proto_state, std::shared_ptr<Env>& env) {
        env->round_number = proto_state.currentround();
        env->is_game_over = proto_state.isgameover();

        if (proto_state.has_board()) {
            env->board = from_proto_board(proto_state.board());
        }

        // 更新行动队列
        env->action_queue.clear();
        for (const auto& piece_proto : proto_state.actionqueue()) {
            env->action_queue.push_back(from_proto_piece(piece_proto));
        }

        // 更新当前行动棋子
        for (const auto& piece : env->action_queue) {
            if (piece->id == proto_state.currentpieceid()) {
                env->current_piece = piece;
                break;
            }
        }

        // 更新延迟法术
        env->delayed_spells.clear();
        for (const auto& spell_proto : proto_state.delayedspells()) {
            auto spell_context = std::make_shared<SpellContext>();
            // TODO: 完成spell_context的转换
            env->delayed_spells.push_back(spell_context);
        }

        // 更新玩家信息
        if (!env->player1) {
            env->player1 = std::make_shared<Player>();
            env->player1->id = 1;
        }
        if (!env->player2) {
            env->player2 = std::make_shared<Player>();
            env->player2->id = 2;
        }

        env->player1->pieces.clear();
        env->player2->pieces.clear();

        for (const auto& piece : env->action_queue) {
            if (piece->team == 1) {
                env->player1->pieces.push_back(piece);
            } else if (piece->team == 2) {
                env->player2->pieces.push_back(piece);
            }
        }
    }

    static std::vector<server::_pieceArg> to_proto_piece_args(const std::vector<PieceArg>& py_piece_args) {
        std::vector<server::_pieceArg> proto_args;
        for (const auto& arg : py_piece_args) {
            server::_pieceArg proto_arg;
            proto_arg.set_strength(arg.strength);
            proto_arg.set_intelligence(arg.intelligence);
            proto_arg.set_dexterity(arg.dexterity);
            *proto_arg.mutable_equip() = to_proto_point(arg.equip);
            *proto_arg.mutable_pos() = to_proto_point(arg.pos);
            proto_args.push_back(proto_arg);
        }
        return proto_args;
    }
}; 