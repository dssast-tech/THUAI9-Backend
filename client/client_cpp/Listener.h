#pragma once
#include <string>
#include <thread>
#include <atomic>

class ClientListener
{
private:
    std::string prefix;
    std::atomic<bool> isRunning;

public:
    explicit ClientListener(const std::string& urlPrefix);
    void Start();
    void Stop();

private:
    void HandleRequest();
};