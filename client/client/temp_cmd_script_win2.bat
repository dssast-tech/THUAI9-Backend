echo ========== client(mcts) terminal =========
cd /d D:\Code\THUAI9-Backend\client\client_gRPC
C:\Users\35809\.conda\envs\thuai\python.exe grpc_client.py --host 127.0.0.1 --port 50051 --mode remote --strategy mcts
echo client mcts finished (if stopped)
pause