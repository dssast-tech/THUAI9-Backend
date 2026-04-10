#pragma once
#include <memory>
#include <vector>
#include <nlohmann/json.hpp>
#include "State.h"
#include "utils.h"

/**
 * JSON <-> 内部数据结构 转换器（Saiblo 版，替代原 proto 版）
 *
 * 游戏状态 JSON 字段对应 GameEngine.cs GetStateJson() 的输出：
 *   currentRound, currentPlayerId, currentPieceID, isGameOver,
 *   actionQueue (Piece[]), board, delayedSpells
 */
class Converter {
public:
    // ---- Point ----

    static Point from_json_point(const nlohmann::json& j) {
        return Point(j.value("x", 0), j.value("y", 0));
    }

    static nlohmann::json to_json_point(const Point& p) {
        return {{"x", p.x}, {"y", p.y}};
    }

    // ---- Cell ----

    static Cell from_json_cell(const nlohmann::json& j) {
        Cell c;
        c.state     = j.value("state", 1);
        c.player_id = j.value("playerId", -1);
        c.piece_id  = j.value("pieceId", -1);
        return c;
    }

    // ---- Board ----

    static std::shared_ptr<Board> from_json_board(const nlohmann::json& j) {
        int w = j.value("width", 0);
        int h = j.value("height", 0);
        auto board = std::make_shared<Board>(w, h);
        board->boarder = j.value("boarder", h / 2);

        // grid 是长度 w*h 的一维数组，行优先（x 外层，y 内层）
        if (j.contains("grid") && j["grid"].is_array()) {
            const auto& grid_arr = j["grid"];
            int idx = 0;
            for (int x = 0; x < w; ++x) {
                for (int y = 0; y < h; ++y) {
                    if (idx < static_cast<int>(grid_arr.size())) {
                        board->grid[x][y] = from_json_cell(grid_arr[idx++]);
                    }
                }
            }
        }

        // height_map 同样是一维数组
        if (j.contains("height_map") && j["height_map"].is_array()) {
            const auto& hm = j["height_map"];
            int idx = 0;
            for (int x = 0; x < w; ++x) {
                for (int y = 0; y < h; ++y) {
                    if (idx < static_cast<int>(hm.size())) {
                        board->height_map[x][y] = hm[idx++].get<int>();
                    }
                }
            }
        }

        return board;
    }

    // ---- Piece ----

    static std::shared_ptr<Piece> from_json_piece(const nlohmann::json& j) {
        auto p = std::make_shared<Piece>();
        p->id               = j.value("id", 0);
        p->team             = j.value("team", 0);
        p->health           = j.value("health", 0);
        p->max_health       = j.value("max_health", 0);
        p->physical_resist  = j.value("physical_resist", 0);
        p->magic_resist     = j.value("magic_resist", 0);
        p->physical_damage  = j.value("physical_damage", 0);
        p->magic_damage     = j.value("magic_damage", 0);
        p->action_points    = j.value("action_points", 0);
        p->max_action_points= j.value("max_action_points", 0);
        p->spell_slots      = j.value("spell_slots", 0);
        p->max_spell_slots  = j.value("max_spell_slots", 0);
        p->movement         = j.value("movement", 0.0f);
        p->max_movement     = j.value("max_movement", 0.0f);
        p->strength         = j.value("strength", 0);
        p->dexterity        = j.value("dexterity", 0);
        p->intelligence     = j.value("intelligence", 0);
        p->height           = j.value("height", 0);
        p->attack_range     = j.value("attack_range", 0);
        p->spell_range      = j.value("spell_range", 0.0);
        p->queue_index      = j.value("queue_index", 0);
        p->is_alive         = j.value("is_alive", true);
        p->is_in_turn       = j.value("is_in_turn", false);
        p->is_dying         = j.value("is_dying", false);

        if (j.contains("position") && j["position"].is_object()) {
            p->position = from_json_point(j["position"]);
        }
        if (j.contains("spell_list") && j["spell_list"].is_array()) {
            for (const auto& s : j["spell_list"]) {
                p->spell_list.push_back(s.get<int>());
            }
        }
        return p;
    }

    // ---- Game State -> Env ----

    static void from_json_game_state(const nlohmann::json& state, std::shared_ptr<Env>& env) {
        env->round_number  = state.value("currentRound", 0);
        env->is_game_over  = state.value("isGameOver", false);
        int current_pid    = state.value("currentPieceID", -1);

        if (state.contains("board") && state["board"].is_object()) {
            env->board = from_json_board(state["board"]);
        }

        env->action_queue.clear();
        if (state.contains("actionQueue") && state["actionQueue"].is_array()) {
            for (const auto& pj : state["actionQueue"]) {
                env->action_queue.push_back(from_json_piece(pj));
            }
        }

        env->current_piece = nullptr;
        for (const auto& piece : env->action_queue) {
            if (piece->id == current_pid) {
                env->current_piece = piece;
                break;
            }
        }

        if (!env->player1) { env->player1 = std::make_shared<Player>(); env->player1->id = 1; }
        if (!env->player2) { env->player2 = std::make_shared<Player>(); env->player2->id = 2; }
        env->player1->pieces.clear();
        env->player2->pieces.clear();
        for (const auto& piece : env->action_queue) {
            if (piece->team == 1) env->player1->pieces.push_back(piece);
            else if (piece->team == 2) env->player2->pieces.push_back(piece);
        }
    }

    // ---- ActionSet -> JSON ----
    //
    // 对应 GameEngine.cs ExecuteAction 接受的 JSON 格式：
    // { "move": bool, "move_target": {x,y},
    //   "attack": bool, "attack_context": {attacker_id, target_id} | null,
    //   "spell": bool,  "spell_context": {...} | null }

    static nlohmann::json to_json_action(const ActionSet& action, int player_id) {
        nlohmann::json j;
        j["player_id"] = player_id;  // C# 内部 1-based

        bool do_move = (action.move_target.x != 0 || action.move_target.y != 0);
        j["move"] = do_move;
        j["move_target"] = do_move
            ? nlohmann::json{{"x", action.move_target.x}, {"y", action.move_target.y}}
            : nullptr;

        j["attack"] = action.attack;
        if (action.attack && action.attack_context) {
            nlohmann::json ac;
            ac["attacker"] = action.attack_context->attacker ? action.attack_context->attacker->id : -1;
            ac["target"]   = action.attack_context->target   ? action.attack_context->target->id   : -1;
            j["attack_context"] = ac;
        } else {
            j["attack_context"] = nullptr;
        }

        j["spell"] = action.spell;
        if (action.spell && action.spell_context) {
            auto& sc = action.spell_context;
            nlohmann::json sc_j;
            sc_j["caster"]        = sc->caster ? sc->caster->id : -1;
            sc_j["spell_id"]      = sc->spell  ? sc->spell->id  : -1;
            sc_j["target"]        = sc->target ? sc->target->id : -1;
            sc_j["spell_lifespan"]= sc->spell_lifespan;
            if (sc->target_area) {
                nlohmann::json ta;
                ta["x"]      = sc->target_area->x;
                ta["y"]      = sc->target_area->y;
                ta["radius"] = sc->target_area->radius;
                sc_j["target_area"] = ta;
            } else {
                sc_j["target_area"] = nullptr;
            }
            j["spell_context"] = sc_j;
        } else {
            j["spell_context"] = nullptr;
        }

        return j;
    }

    // ---- PieceArg list -> JSON（初始化棋子配置）----

    static nlohmann::json to_json_piece_args(const std::vector<PieceArg>& args) {
        nlohmann::json arr = nlohmann::json::array();
        for (const auto& a : args) {
            nlohmann::json item;
            item["strength"]     = a.strength;
            item["intelligence"] = a.intelligence;
            item["dexterity"]    = a.dexterity;
            nlohmann::json eq; eq["x"] = a.equip.x; eq["y"] = a.equip.y;
            nlohmann::json pos; pos["x"] = a.pos.x; pos["y"] = a.pos.y;
            item["equip"] = eq;
            item["pos"]   = pos;
            arr.push_back(item);
        }
        return arr;
    }
};
