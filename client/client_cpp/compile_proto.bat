@echo off
REM 设置protoc编译器路径（请根据实际安装路径修改）
set PROTOC="%VCPKG_ROOT%\installed\x64-windows\tools\protobuf\protoc.exe"
set GRPC_CPP_PLUGIN="%VCPKG_ROOT%\installed\x64-windows\tools\grpc\grpc_cpp_plugin.exe"

REM 创建输出目录
if not exist "proto" mkdir proto

REM 编译proto文件
%PROTOC% -I../client_gRPC --cpp_out=proto ../client_gRPC/message.proto
%PROTOC% -I../client_gRPC --grpc_out=proto --plugin=protoc-gen-grpc=%GRPC_CPP_PLUGIN% ../client_gRPC/message.proto

echo Proto files compiled successfully!
pause 