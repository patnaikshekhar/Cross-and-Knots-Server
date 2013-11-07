# Cross and Knots Server

> **Overview**
>
> This is a game server which utilizes [tornado](http://www.tornadoweb.org/en/stable/) web sockets. It communicates with the client using JSON in a certain format. Each message contains a command which tells the server what the client wants to do.
>
>
> **Usage**
>
> Run python server.py to start the server on port 8888.
>
> Run python server.py --**port number** to sta
>
> **Files**
>
> The server consists of two main files
>
>+ *server.py* - This contains the main server code and the game objects
>+ *constants.py* - This contains all the constants required for the game
