class PolicyMessage:
    """发送信息的格式"""

    def __init__(self, move_target=None, attack=False, attack_context=None, spell_context=None, comment=""):
        self.move_target = move_target  # {"x": int, "y": int}
        self.attack = attack  # 是否攻击
        self.attack_context = attack_context  # 攻击上下文
        self.spell_context = spell_context  # 法术上下文
        self.comment = comment  # 策略说明

    def to_dict(self):
        """将 PolicyMessage 转换为字典格式以便序列化为 JSON"""
        return {
            "actions": {
                "move_target": self.move_target,
                "attack": self.attack,
                "attack_context": self.attack_context,
                "spell_context": self.spell_context,
            },
            "comment": self.comment,
        }


class GameMessage:
    """接收信息的格式"""

    def __init__(self, game_state=None, pieces=None, board=None, env=None):
        self.game_state = game_state  # 游戏状态
        self.pieces = pieces  # 棋子信息
        self.board = board  # 棋盘信息
        self.env = env  # 环境信息

    @staticmethod
    def from_dict(data):
        """从字典格式解析为 GameMessage 对象"""
        return GameMessage(
            game_state=data.get("gameState"),
            pieces=data.get("Piece"),
            board=data.get("Board"),
            env=data.get("Env"),
        )