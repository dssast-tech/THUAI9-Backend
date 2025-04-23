class PolicyMessage:
    """发送信息的格式"""

    def __init__(self, initialization_set=None, move_target=None, attack=False, attack_position=None,
                 attack_context=None, spell_context=None, comment=""):
        """
        :param initialization_set: InitializationSet 对象，棋子初始化信息
        :param move_target: {"x": int, "y": int}，移动目标
        :param attack: bool，是否攻击
        :param attack_position: {"x": int, "y": int}，攻击位置
        :param attack_context: dict，攻击上下文
        :param spell_context: dict，法术上下文
        :param comment: str，策略说明
        """
        self.initialization_set = initialization_set  # InitializationSet 对象
        self.move_target = move_target  # {"x": int, "y": int}
        self.attack = attack  # 是否攻击
        self.attack_position = attack_position  # {"x": int, "y": int}
        self.attack_context = attack_context  # 攻击上下文
        self.spell_context = spell_context  # 法术上下文
        self.comment = comment  # 策略说明

    def to_dict(self):
        """将 PolicyMessage 转换为字典格式以便序列化为 JSON"""
        return {
            "initializationSet": self.initialization_set.to_dict() if self.initialization_set else None,
            "actionSet": {
                "move_target": self.move_target,
                "attack": self.attack,
                "attack_position": self.attack_position,
                "attack_context": self.attack_context,
                "spell_context": self.spell_context,
            },
            "comment": self.comment,
        }


class GameMessage:
    """接收信息的格式"""

    def __init__(self, game_state=None, pieces=None, board=None, env=None):
        """
        :param game_state: dict，游戏状态
        :param pieces: list，棋子信息
        :param board: dict，棋盘信息
        :param env: dict，环境信息
        """
        self.game_state = game_state  # 游戏状态
        self.pieces = pieces  # 棋子信息
        self.board = board  # 棋盘信息
        self.env = env  # 环境信息

    @staticmethod
    def from_dict(data):
        """从字典格式解析为 GameMessage 对象"""
        return GameMessage(
            game_state=data.get("gameState"),
            pieces=data.get("pieces"),
            board=data.get("board"),
            env=data.get("env"),
        )