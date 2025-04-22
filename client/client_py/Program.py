from Listener import ClientListener
from Player import Player

if __name__ == "__main__":
    player = Player()
    # 创建客户端监听器，指定 URL 前缀和回调函数
    listener = ClientListener("http://localhost:5001/receive/", player.action)
    listener.start()