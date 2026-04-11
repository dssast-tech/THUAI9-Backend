#pragma once
#include <climits>
#include <functional>
#include <vector>
#include "State.h"
#include "utils.h"

/**
 * 策略工厂（Saiblo 版，替代原 gRPC 版）
 *
 * get_aggressive_init_strategy() 返回初始棋子配置策略
 * get_aggressive_action_strategy() / get_defensive_action_strategy() 返回行动策略
 */
class StrategyFactory {
public:
    /**
     * 初始棋子配置策略：返回 PieceArg 列表，由 game-host 在初始化时使用。
     * （Saiblo 模式下，Client 不发送初始化配置，此接口仅保留供本地调试）
     */
    static std::function<std::vector<PieceArg>(int player_id)> get_aggressive_init_strategy() {
        return [](int player_id) -> std::vector<PieceArg> {
            PieceArg arg;
            arg.strength     = 10;
            arg.intelligence = 10;
            arg.dexterity    = 10;
            arg.equip = Point(1, 2);  // 长剑 + 中甲
            arg.pos   = Point(5, player_id == 0 ? 2 : 12);
            return {arg};
        };
    }

    /**
     * 激进行动策略：优先攻击，否则向敌方靠近。
     */
    static std::function<ActionSet(const Env&)> get_aggressive_action_strategy() {
        return [](const Env& env) -> ActionSet {
            ActionSet action;
            if (!env.current_piece) return action;

            const auto& me = env.current_piece;

            // 找最近的敌方棋子
            std::shared_ptr<Piece> enemy;
            int min_dist = INT_MAX;
            for (const auto& p : env.action_queue) {
                if (!p->is_alive || p->team == me->team) continue;
                int d = std::abs(p->position.x - me->position.x)
                      + std::abs(p->position.y - me->position.y);
                if (d < min_dist) { min_dist = d; enemy = p; }
            }

            if (!enemy) return action;

            // 若在攻击范围内，尝试攻击
            if (min_dist <= me->attack_range && me->action_points > 0) {
                action.attack = true;
                action.attack_context = std::make_shared<AttackContext>();
                action.attack_context->attacker = me;
                action.attack_context->target   = enemy;
                return action;
            }

            // 否则向敌方移动一步（简单曼哈顿贪心）
            if (me->movement > 0) {
                Point target = me->position;
                if (std::abs(enemy->position.x - me->position.x) >
                    std::abs(enemy->position.y - me->position.y)) {
                    target.x += (enemy->position.x > me->position.x) ? 1 : -1;
                } else {
                    target.y += (enemy->position.y > me->position.y) ? 1 : -1;
                }
                action.move_target = target;
            }

            return action;
        };
    }

    /**
     * 防守行动策略：优先攻击，否则原地不动。
     */
    static std::function<ActionSet(const Env&)> get_defensive_action_strategy() {
        return [](const Env& env) -> ActionSet {
            ActionSet action;
            if (!env.current_piece) return action;

            const auto& me = env.current_piece;

            for (const auto& p : env.action_queue) {
                if (!p->is_alive || p->team == me->team) continue;
                int d = std::abs(p->position.x - me->position.x)
                      + std::abs(p->position.y - me->position.y);
                if (d <= me->attack_range && me->action_points > 0) {
                    action.attack = true;
                    action.attack_context = std::make_shared<AttackContext>();
                    action.attack_context->attacker = me;
                    action.attack_context->target   = p;
                    return action;
                }
            }

            // 不移动，返回空动作
            return action;
        };
    }
};
