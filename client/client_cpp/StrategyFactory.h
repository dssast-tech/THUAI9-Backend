#pragma once
#include <functional>
#include "State.h"
#include "utils.h"

class StrategyFactory {
public:
    static std::function<std::vector<PieceArg>(const server::_InitResponse&)> get_aggressive_init_strategy() {
        return [](const server::_InitResponse& response) {
            std::vector<PieceArg> args;
            // TODO: 实现具体的初始化策略
            return args;
        };
    }

    static std::function<ActionSet(const Env&)> get_defensive_action_strategy() {
        return [](const Env& env) {
            ActionSet action;
            // TODO: 实现具体的行动策略
            return action;
        };
    }
}; 