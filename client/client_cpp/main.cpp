#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <chrono>
#include <grpcpp/grpcpp.h>
#include "message.grpc.pb.h"
#include "State.h"
#include "Converter.h"
#include "StrategyFactory.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using server::GameService;

// 全局变量
std::shared_ptr<Player> player = std::make_shared<Player>();
std::shared_ptr<Env> env = std::make_shared<Env>();

void subscribe_game_state(std::shared_ptr<GameService::Stub> stub, int player_id, 
                         const std::function<ActionSet(const Env&)>& action_strategy) {
    server::_GameStateRequest request;
    request.set_playerid(player_id);
    
    ClientContext context;
    std::unique_ptr<grpc::ClientReader<server::_GameStateResponse>> reader(
        stub->BroadcastGameState(&context, request));

    server::_GameStateResponse state;
    while (reader->Read(&state)) {
        std::cout << "\n收到游戏状态更新:" << std::endl;
        std::cout << "当前回合: " << state.currentround() << std::endl;
        std::cout << "当前行动玩家: " << state.currentplayerid() << std::endl;
        std::cout << "当前行动棋子: " << state.currentpieceid() << std::endl;
        std::cout << "游戏是否结束: " << state.isgameover() << std::endl;

        // 如果是当前玩家的回合，生成并发送行动
        if (state.currentplayerid() == player_id) {
            // 等待一小段时间，确保服务器准备好接收行动
            std::this_thread::sleep_for(std::chrono::milliseconds(100));

            try {
                // 将游戏状态转换为策略函数需要的格式
                Converter::from_proto_game_state(state, env);

                // 使用策略生成行动
                ActionSet action = action_strategy(*env);

                // 将行动转换为protobuf格式
                auto action_proto = Converter::to_proto_action(action, player_id);

                std::cout << "发送行动" << std::endl;

                // 发送行动到服务器
                ClientContext action_context;
                server::_actionResponse response;
                Status status = stub->SendAction(&action_context, action_proto, &response);

                if (status.ok() && response.success()) {
                    std::cout << "行动已被接受" << std::endl;
                } else {
                    std::cout << "行动被拒绝: " << response.mes() << std::endl;
                }
            } catch (const std::exception& e) {
                std::cout << "发送行动时出错: " << e.what() << std::endl;
            }
        }

        if (state.isgameover()) {
            std::cout << "游戏结束！" << std::endl;
            break;
        }
    }
}

int main() {
    // 创建Channel
    std::shared_ptr<Channel> channel = grpc::CreateChannel(
        "localhost:50051", grpc::InsecureChannelCredentials());
    std::shared_ptr<GameService::Stub> stub = GameService::NewStub(channel);

    // 选择策略
    auto init_strategy = StrategyFactory::get_aggressive_init_strategy();
    auto action_strategy = StrategyFactory::get_defensive_action_strategy();

    // 初始化游戏
    server::_InitRequest init_request;
    init_request.set_message("Hello, Server!");
    ClientContext init_context;
    server::_InitResponse init_response;
    
    Status status = stub->SendInit(&init_context, init_request, &init_response);
    if (!status.ok()) {
        std::cout << "初始化失败" << std::endl;
        return 1;
    }

    std::cout << "初始化响应: " << init_response.id() << std::endl;
    player->id = init_response.id();

    // 获取初始化游戏状态并应用初始化策略
    auto init_policy = Converter::to_proto_piece_args(init_strategy(init_response));

    // 将init_policy转换为protobuf消息并发送
    server::_InitPolicyRequest init_policy_request;
    init_policy_request.set_playerid(player->id);
    *init_policy_request.mutable_pieceargs() = {init_policy.begin(), init_policy.end()};

    ClientContext init_policy_context;
    server::_InitPolicyResponse init_policy_response;
    status = stub->SendInitPolicy(&init_policy_context, init_policy_request, &init_policy_response);

    std::cout << "初始化策略已发送" << std::endl;

    // 启动游戏状态订阅
    std::cout << "开始订阅游戏状态..." << std::endl;
    std::thread subscription_thread(subscribe_game_state, stub, player->id, action_strategy);
    subscription_thread.detach();
    std::cout << "已完成订阅" << std::endl;

    // 保持主线程运行
    std::string input;
    std::getline(std::cin, input);

    return 0;
} 