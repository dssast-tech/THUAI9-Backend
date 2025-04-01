# THUAI-8: WarChess

This is the official repository for the THUAI-8 project, a turn-based strategy warchess game.
```python
thuai8/
│
├── demo/ # It is just a demo.
│
├── client/ # This part contains all functions that the players should
│           # complete in order to interact with the game server.
└── server/ # TThis part contains all functions that the game server
            # (logic) requires.
```
In such case it is convenient to use TCP/IP protocol to communicate between the clients (players) and the game server.
It is reconmmended to refer to the demo when finishing the client-server part.