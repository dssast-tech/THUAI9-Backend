#include "Listener.h"
#include <iostream>

int main()
{
    ClientListener listener("http://localhost:5001/receive/");
    listener.Start();

    // 模拟运行一段时间
    std::this_thread::sleep_for(std::chrono::seconds(10));
    listener.Stop();

    return 0;
}