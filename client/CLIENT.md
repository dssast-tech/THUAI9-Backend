## Client

The client part is more like a basic code framework that the contestants can use to implement their own game logic. Therefore, what we need to do is to provide the basic structure of controlling the game server, while the detailed implementation of the game logic is left to the contestants.

Communicational protocols should be pre-defined and agreed upon by both the client and server sides. The client should be able to understand the server's response and send appropriate commands to the server. The server should be able to understand the client's commands and execute the corresponding actions. In case of any discrepancies, the server should respond with an error message or terminate the connection.