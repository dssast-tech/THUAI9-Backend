/**
 * THUAI9 C++ Client - Saiblo stdin/stdout 版本
 * 替代原 gRPC main.cpp
 *
 * 协议说明：
 *   judger -> AI:  [4字节长度(大端序)] + [JSON]
 *   AI -> judger:  [4字节长度(大端序)] + [JSON]
 *
 * 游戏状态 JSON 由 game-host 发送，字段对应 GameEngine.cs::GetStateJson()。
 * 行动 JSON 由 Converter::to_json_action() 构造，对应 GameEngine.cs::ExecuteAction()。
 */

#include <iostream>
#include <memory>
#include <string>
#include <nlohmann/json.hpp>

#include "SaibloClient.h"
#include "State.h"
#include "Converter.h"
#include "StrategyFactory.h"

static const std::vector<std::string> ERROR_MAP = {"RE", "TLE", "OLE"};

int main() {
    // 关闭 cout/cin 同步，提高 stdin/stdout 二进制读写性能
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    // 选择策略（可通过编译宏或命令行参数切换）
    auto action_strategy = StrategyFactory::get_aggressive_action_strategy();

    auto env = std::make_shared<Env>();
    int player_id = -1;  // Saiblo 0-based，首次从消息中推断

    std::cerr << "[INFO] 等待初始化消息..." << std::endl;

    while (true) {
        nlohmann::json msg;
        try {
            msg = SaibloClient::read_message();
        } catch (const std::exception& e) {
            std::cerr << "[INFO] 连接关闭: " << e.what() << std::endl;
            break;
        }

        int state = msg.value("state", 0);

        // --- 游戏结束 ---
        if (state == -1) {
            std::cerr << "[INFO] 游戏结束" << std::endl;
            break;
        }

        // --- AI 异常消息（player == -1） ---
        if (msg.value("player", 0) == -1) {
            try {
                auto err = nlohmann::json::parse(msg.value("content", std::string("{}")));
                int etype = err.value("error", 0);
                std::cerr << "[ERROR] AI 异常: "
                          << (etype < static_cast<int>(ERROR_MAP.size()) ? ERROR_MAP[etype] : "UNKNOWN")
                          << std::endl;
            } catch (...) {}
            break;
        }

        // --- 正常回合消息 ---
        auto players     = msg.value("player",  std::vector<int>{});
        auto content_list = msg.value("content", std::vector<std::string>{});
        auto listen      = msg.value("listen",  std::vector<int>{});

        // 首次推断自己的 player_id
        if (player_id == -1 && !players.empty()) {
            player_id = players[0];
            std::cerr << "[INFO] 我的 player_id = " << player_id << std::endl;
        }

        // 只在轮到我们时行动
        bool my_turn = false;
        for (int pid : listen) { if (pid == player_id) { my_turn = true; break; } }
        if (!my_turn) continue;

        // 取对应状态 JSON
        int idx = 0;
        for (int i = 0; i < static_cast<int>(players.size()); ++i) {
            if (players[i] == player_id) { idx = i; break; }
        }
        if (idx >= static_cast<int>(content_list.size())) continue;

        nlohmann::json state_data;
        try {
            state_data = nlohmann::json::parse(content_list[idx]);
        } catch (const std::exception& e) {
            std::cerr << "[ERROR] 解析状态 JSON 失败: " << e.what() << std::endl;
            continue;
        }

        // 更新环境
        Converter::from_json_game_state(state_data, env);

        if (!env->current_piece) {
            std::cerr << "[WARN] current_piece 为空，发送空动作" << std::endl;
            nlohmann::json empty = {
                {"player", player_id},
                {"content", nlohmann::json{{"move", false}, {"attack", false}, {"spell", false}}.dump()}
            };
            SaibloClient::write_message(empty);
            continue;
        }

        // 运行策略
        ActionSet action;
        try {
            action = action_strategy(*env);
        } catch (const std::exception& e) {
            std::cerr << "[ERROR] 策略执行失败: " << e.what() << std::endl;
        }

        // 序列化并发送（C# 侧 player_id 是 1-based）
        int csharp_pid = player_id + 1;
        nlohmann::json action_json = Converter::to_json_action(action, csharp_pid);

        nlohmann::json response = {
            {"player",  player_id},
            {"content", action_json.dump()}
        };
        SaibloClient::write_message(response);
        std::cerr << "[INFO] 回合 " << state_data.value("currentRound", 0)
                  << ": 已发送行动" << std::endl;
    }

    return 0;
}
