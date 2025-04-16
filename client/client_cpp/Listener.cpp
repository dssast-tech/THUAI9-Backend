#include "Listener.h"
#include <iostream>

ClientListener::ClientListener(const std::string& urlPrefix) : prefix(urlPrefix), isRunning(false) {}

void ClientListener::Start()
{
    isRunning = true;
    std::cout << "客户端监听启动: " << prefix << std::endl;

    // 模拟监听线程
    std::thread([this]() {
        while (isRunning)
        {
            HandleRequest();
        }
    }).detach();
}

void ClientListener::Stop()
{
    isRunning = false;
    std::cout << "客户端监听停止" << std::endl;
}

void ClientListener::HandleRequest()
{
    // 模拟处理请求
    std::cout << "处理请求..." << std::endl;
}