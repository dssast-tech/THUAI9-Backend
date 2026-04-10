#pragma once
#include <iostream>
#include <string>
#include <cstdint>
#include <nlohmann/json.hpp>

#ifdef _WIN32
#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <arpa/inet.h>
#endif

/**
 * Saiblo stdin/stdout 通信协议客户端（C++ 版）
 *
 * 消息格式 judger -> AI:  [4字节长度(大端序)] + [JSON内容]
 * 消息格式 AI -> judger:  [4字节长度(大端序)] + [JSON内容]
 */
class SaibloClient {
public:
    /**
     * 从 stdin 读取一条消息，返回解析后的 JSON。
     * 读取失败时抛出 std::runtime_error。
     */
    static nlohmann::json read_message() {
        // 读取 4 字节大端序长度头
        uint32_t net_len = 0;
        if (!read_exact(reinterpret_cast<char*>(&net_len), 4)) {
            throw std::runtime_error("stdin closed while reading length header");
        }
        uint32_t length = ntohl(net_len);

        // 读取 JSON 正文
        std::string buf(length, '\0');
        if (!read_exact(&buf[0], length)) {
            throw std::runtime_error("stdin closed while reading message body");
        }

        return nlohmann::json::parse(buf);
    }

    /**
     * 向 stdout 写入一条消息。
     */
    static void write_message(const nlohmann::json& data) {
        std::string content = data.dump();
        uint32_t net_len = htonl(static_cast<uint32_t>(content.size()));

        std::cout.write(reinterpret_cast<const char*>(&net_len), 4);
        std::cout.write(content.c_str(), static_cast<std::streamsize>(content.size()));
        std::cout.flush();
    }

private:
    static bool read_exact(char* buf, std::size_t n) {
        std::size_t total = 0;
        while (total < n) {
            std::cin.read(buf + total, static_cast<std::streamsize>(n - total));
            std::streamsize got = std::cin.gcount();
            if (got <= 0) return false;
            total += static_cast<std::size_t>(got);
        }
        return true;
    }
};
