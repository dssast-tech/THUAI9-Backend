from utils import Point, DicePair, Spell


class Piece:
    def __init__(self):
        self.health = 0
        self.max_health = 0
        self.physical_resist = 0
        self.magic_resist = 0
        self.physical_damage = DicePair(0, 0)
        self.magic_damage = DicePair(0, 0)
        self.action_points = 0
        self.max_action_points = 0
        self.spell_slots = 0
        self.max_spell_slots = 0
        self.movement = 0.0
        self.max_movement = 0.0
        self.strength = 0
        self.dexterity = 0
        self.intelligence = 0
        self.position = Point(0, 0)
        self.height = 0
        self.attack_range = 0
        self.spell_list = []
        self.team = 0
        self.queue_index = 0
        self.is_alive = True
        self.is_in_turn = False
        self.is_dying = False
        self.spell_range = 0.0


class Board:
    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(height)] for _ in range(width)]
        self.height_map = [[0 for _ in range(height)] for _ in range(width)]


class Env:
    def __init__(self):
        self.action_queue = []
        self.current_piece = None
        self.round_number = 0
        self.delayed_spells = []
        self.player1 = None
        self.player2 = None
        self.board = Board()
        self.is_game_over = False