cmake_minimum_required(VERSION 3.15)
project(thuai9_client_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ---- nlohmann/json ----
# 优先用系统包，若没有则用 FetchContent 自动下载
find_package(nlohmann_json 3.2.0 QUIET)
if(NOT nlohmann_json_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        nlohmann_json
        URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
        URL_HASH SHA256=d6c65aca6b1ed68e7a182f4757257b107ae403032760ed6ef121c9d55e81757d
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()

# ---- Windows: 链接 ws2_32（ntohl/htonl） ----
if(WIN32)
    set(PLATFORM_LIBS ws2_32)
else()
    set(PLATFORM_LIBS "")
endif()

# ---- 可执行文件 ----
add_executable(thuai9_client main.cpp)

target_include_directories(thuai9_client PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(thuai9_client PRIVATE
    nlohmann_json::nlohmann_json
    ${PLATFORM_LIBS}
)
