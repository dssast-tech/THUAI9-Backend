cmake_minimum_required(VERSION 3.15)
project(client_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找必要的包
find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)

# 添加proto生成的文件
add_library(proto_lib
    proto/message.pb.cc
    proto/message.pb.h
    proto/message.grpc.pb.cc
    proto/message.grpc.pb.h
)

# 设置proto_lib的包含目录
target_include_directories(proto_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/proto
    ${Protobuf_INCLUDE_DIRS}
    ${gRPC_INCLUDE_DIRS}
)

# 链接必要的库
target_link_libraries(proto_lib PUBLIC
    protobuf::libprotobuf
    gRPC::grpc++
    gRPC::grpc++_reflection
)

# 添加可执行文件
add_executable(client_cpp 
    main.cpp
)

# 链接proto_lib
target_link_libraries(client_cpp PRIVATE proto_lib)

# 添加头文件目录
target_include_directories(client_cpp PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/proto
) 