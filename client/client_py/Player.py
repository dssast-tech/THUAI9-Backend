from game_message import PolicyMessage, GameMessage


class Player:
    def action(self, message: GameMessage) -> PolicyMessage:
        """接收处理到的信息，按指定格式发送一个策略指令"""
        return PolicyMessage()