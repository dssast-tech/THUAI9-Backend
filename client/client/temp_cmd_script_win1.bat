echo ========== server terminal =========
call "E:\\Anaconda3\\Scripts\\activate.bat" thuai
cd /d D:\Code\THUAI9-Backend\server\server\server
dotnet run --urls http://127.0.0.1:50051
echo server finished (if stopped)
pause