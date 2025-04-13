## Server

Generally speaking, the server is responsible for handling the game logic and controlled by the clients. It is responsible for processing the game state, updating the game state, and sending the game state to the clients. The server is also responsible for handling the game rules and ensuring that the game is fair and balanced.

To implement the server, we can refer to the sketch in the group chat, where the game is seperated into several modules:

- Players & Pieces: These two modules are responsible for managing the players and pieces in the game. The players module is responsible for keeping track of the players' information, such as their names, scores, and the pieces they own. The pieces module is responsible for keeping track of the pieces' information, such as their position, type, owner and other attributes.

- Skills: This module is responsible for managing the skills of pieces in the game. The skills module is responsible for keeping track of the skills' information, such as their name, description, and cooldown. Meanwhile, all instantiate skills should be saved at the Environment module.

- Map: These two modules are responsible for managing the map and the status of the game. The map module is responsible for containing the information of the map, such as the size, the positions of the walls, and the positions of the obstacles. This module is relatively simple, since it is static and is initialized once at the beginning of the game.

- Environment: This module is responsible for managing the environment of the game. The environment module is responsible for keeping track of the game state, such as the current player, the current turn, and the current phase. This module is responsible for updating the game state based on the actions of players and pieces. Note that the environment module should be aware of all the modules, such as the players, pieces, and skills modules, due to our designed feature that **all pieces could only interact with the environment module rather than directly with each other**.

Besides, remember to reserve some functions for the server to communicate with the clients, such as sending the game state to the clients and receiving the actions from the clients. The specific implementation of these functions will depend on the specific protocol used by the clients.