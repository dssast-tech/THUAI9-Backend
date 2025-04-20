#pragma once
#include "GameMessage.h"

class Player
{
public:
    PolicyMessage action(const GameMessage& message){
        // 接收处理到的信息，按指定格式发送一个策略指令
        return PolicyMessage();
    };
};