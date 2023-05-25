import numpy as np
import math
import random

# Named Constants
SUIT_MOUSE = 0
SUIT_RABBIT = 1
SUIT_FOX = 2
SUIT_BIRD = 3

ITEM_NONE = 0
ITEM_HAMMER = 1
ITEM_SWORD = 2
ITEM_BOOT = 3
ITEM_TEA = 4
ITEM_COINS = 5
ITEM_BAG = 6
ITEM_CROSSBOW = 7

class Clearing:
    def __init__(self,id:int,suit:int,num_building_slots:int,num_ruins:int,is_corner_clearing:bool,adj_clearing_ids:list) -> None:
        self.id = id
        self.suit = suit
        self.num_building_slots = num_building_slots
        self.num_ruins = num_ruins
        self.is_corner_clearing = is_corner_clearing
        self.warriors = {}
        self.tokens = {}
        self.buildings = {i:None for i in range(self.num_building_slots)}
        self.adjacent_clearing_ids = adj_clearing_ids


class Card:
    def __init__(self,id:int,suit:int,name:str,recipe:tuple,is_ambush:bool,is_dominance:bool,item:int,points:int) -> None:
        self.id = id
        self.suit = suit
        self.name = name
        self.crafting_recipe = recipe
        self.is_ambush = is_ambush
        self.is_dominance = is_dominance
        self.crafting_item = item
        self.points = points

class Deck:
    def __init__(self, cards = list()):
        self.cards = list(cards)
    
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self, n):
        drawn = []
        for x in range(n):
            try:
                drawn.append(self.cards.pop())
            except:
                pass
        return drawn
    
    def add(self, cards):
        for card in cards:
            self.cards.append(card)
                
    def size(self):
        return len(self.cards)

class Player:
    def __init__(self) -> None:
        self.id
        self.warrior_storage_size

# (Card info, Amount in deck)
# Recipe amounts are (Mouse, Bunny, Fox, Wild)
STANDARD_DECK = [
    # (id,   Suit,        Name,                    Recipe,    is_ambush, is_dom, item,          points), Amount
    (Card(0, SUIT_BIRD,   "Ambush! (Bird)",        (0,0,0,0),   True,      False,  ITEM_NONE,     0),      2),
    (Card(1, SUIT_RABBIT,  "Ambush! (Bunny)",      (0,0,0,0),   True,      False,  ITEM_NONE,     0),      1),
    (Card(2, SUIT_FOX,    "Ambush! (Fox)",         (0,0,0,0),   True,      False,  ITEM_NONE,     0),      1),
    (Card(3, SUIT_MOUSE,  "Ambush! (Mouse)",       (0,0,0,0),   True,      False,  ITEM_NONE,     0),      1),
    (Card(4, SUIT_FOX,    "Anvil",                 (0,0,1,0),   False,     False,  ITEM_HAMMER,   2),      1),
    (Card(5, SUIT_BIRD,   "Armorers",              (0,0,1,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(6, SUIT_BIRD,   "Arms Trader",           (0,0,2,0),   False,     False,  ITEM_SWORD,    2),      1),
    (Card(7, SUIT_RABBIT,  "A Visit to Friends",   (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(8, SUIT_RABBIT,  "Bake Sale",            (0,2,0,0),   False,     False,  ITEM_COINS,    3),      1),
    (Card(9, SUIT_RABBIT,  "Better Burrow Bank",   (0,2,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(10,SUIT_BIRD,   "Birdy Bindle",          (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(11,SUIT_BIRD,   "Brutal Tactics",        (0,0,2,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(12,SUIT_RABBIT,  "Cobbler",              (0,2,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(13,SUIT_MOUSE,  "Codebreakers",          (1,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(14,SUIT_RABBIT,  "Command Warren",       (0,2,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(15,SUIT_BIRD,   "Crossbow (Bird)",       (0,0,1,0),   False,     False,  ITEM_CROSSBOW, 1),      1),
    (Card(16,SUIT_MOUSE,  "Crossbow (Mouse)",      (0,0,1,0),   False,     False,  ITEM_CROSSBOW, 1),      1),
#    (Card(17,SUIT_BIRD,   "Bird Dominance",        (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(18,SUIT_RABBIT,  "Bunny Dominance",      (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(19,SUIT_MOUSE,  "Mouse Dominance",       (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(20,SUIT_FOX,    "Fox Dominance",         (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
    # (id,   Suit,        Name,                    Recipe,    is_ambush, is_dom, item,          points), Amount
    (Card(21, SUIT_FOX,    "Favor of the Foxes",   (0,0,3,0),   False,     False,  ITEM_NONE,     0),      1),
    (Card(22, SUIT_MOUSE,  "Favor of the Mice",    (3,0,0,0),   False,     False,  ITEM_NONE,     0),      1),
    (Card(23, SUIT_RABBIT, "Favor of the Rabbits", (0,3,0,0),   False,     False,  ITEM_NONE,     0),      1),
    (Card(24, SUIT_FOX,    "Foxfolk Steel",        (0,0,2,0),   False,     False,  ITEM_SWORD,    2),      1),
    (Card(25, SUIT_FOX,    "Gently Used Knapsack", (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(26, SUIT_MOUSE,   "Investments",         (0,2,0,0),   False,     False,  ITEM_COINS,    3),      1),
    (Card(27, SUIT_MOUSE,    "Mouse-in-a-Sack",    (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(28, SUIT_FOX,   "Protection Racket",     (0,2,0,0),   False,     False,  ITEM_COINS,    3),      1),
    (Card(29, SUIT_RABBIT,  "Root Tea (Rabbit)",   (1,0,0,0),   False,     False,  ITEM_TEA,      2),      1),
    (Card(30, SUIT_FOX,  "Root Tea (Fox)",         (1,0,0,0),   False,     False,  ITEM_TEA,      2),      1),
    (Card(31, SUIT_MOUSE,  "Root Tea (Mouse)",     (1,0,0,0),   False,     False,  ITEM_TEA,      2),      1),
    (Card(32, SUIT_BIRD,  "Sappers",               (1,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(33, SUIT_MOUSE,  "Scouting Party",       (2,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(34, SUIT_RABBIT, "Smuggler's Trail",     (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(35, SUIT_FOX,   "Stand and Deliver!",    (3,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(36, SUIT_MOUSE,   "Sword",               (0,0,2,0),   False,     False,  ITEM_SWORD,    2),      1),
    (Card(37, SUIT_FOX,   "Tax Collector",         (1,1,1,0),   False,     False,  ITEM_NONE,     0),      3),
    (Card(38, SUIT_FOX,   "Travel Gear (Fox)",     (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(39, SUIT_MOUSE,   "Travel Gear (Mouse)", (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(40, SUIT_BIRD,   "Woodland Runners",     (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(41, SUIT_BIRD,  "Royal Claim",           (0,0,0,4),   False,     False,  ITEM_NONE,     0),      1)
]

MAP_AUTUMN = [
    #        id, suit,         num_building_slots, num_ruins, is_corner_clearing, list of adj clearings
    Clearing(0,  SUIT_FOX,     1,                 0,         True,               [1,3,4]),
    Clearing(1,  SUIT_RABBIT,  2,                 0,         False,              [0,2]),
    Clearing(2,  SUIT_MOUSE,   2,                 0,         True,               [1,3,7]),
    Clearing(3,  SUIT_RABBIT,  1,                 1,         False,              [0,2,5]),
    Clearing(4,  SUIT_MOUSE,   2,                 0,         False,              [0,5,8]),
    Clearing(5,  SUIT_FOX,     1,                 1,         False,              [3,4,6,8,10]),
    Clearing(6,  SUIT_MOUSE,   2,                 1,         False,              [5,7,11]),
    Clearing(7,  SUIT_FOX,     1,                 1,         False,              [2,6,11]),
    Clearing(8,  SUIT_RABBIT,  1,                 0,         True,               [4,5,9]),
    Clearing(9,  SUIT_FOX,     2,                 0,         False,              [8,10]),
    Clearing(10, SUIT_MOUSE,   2,                 0,         False,              [5,9,11]),
    Clearing(11, SUIT_RABBIT,  1,                 0,         True,               [6,7,10])
]


class root2pCatsVsEyrie:
    def __init__(self):
        self.board_size = 11
        self.board = np.zeros((self.board_size, self.board_size), dtype="int32")
        self.player = 1
        self.board_markers = [
            chr(x) for x in range(ord("A"), ord("A") + self.board_size)
        ]

    def to_play(self):
        return 0 if self.player == 1 else 1

    def reset(self):
        self.board = np.zeros((self.board_size, self.board_size), dtype="int32")
        self.player = 1
        return self.get_observation()

    def step(self, action):
        x = math.floor(action / self.board_size)
        y = action % self.board_size
        self.board[x][y] = self.player

        done = self.is_finished()

        reward = 1 if done else 0

        self.player *= -1

        return self.get_observation(), reward, done

    def get_observation(self):
        board_player1 = np.where(self.board == 1, 1.0, 0.0)
        board_player2 = np.where(self.board == -1, 1.0, 0.0)
        board_to_play = np.full((11, 11), self.player, dtype="int32")
        return np.array([board_player1, board_player2, board_to_play])

    def legal_actions(self):
        legal = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    legal.append(i * self.board_size + j)
        return legal

    def is_finished(self):
        has_legal_actions = False
        directions = ((1, -1), (1, 0), (1, 1), (0, 1))
        for i in range(self.board_size):
            for j in range(self.board_size):
                # if no stone is on the position, don't need to consider this position
                if self.board[i][j] == 0:
                    has_legal_actions = True
                    continue
                # value-value at a coord, i-row, j-col
                player = self.board[i][j]
                # check if there exist 5 in a line
                for d in directions:
                    x, y = i, j
                    count = 0
                    for _ in range(5):
                        if (x not in range(self.board_size)) or (
                            y not in range(self.board_size)
                        ):
                            break
                        if self.board[x][y] != player:
                            break
                        x += d[0]
                        y += d[1]
                        count += 1
                        # if 5 in a line, store positions of all stones, return value
                        if count == 5:
                            return True
        return not has_legal_actions

    def render(self):
        marker = "  "
        for i in range(self.board_size):
            marker = marker + self.board_markers[i] + " "
        print(marker)
        for row in range(self.board_size):
            print(chr(ord("A") + row), end=" ")
            for col in range(self.board_size):
                ch = self.board[row][col]
                if ch == 0:
                    print(".", end=" ")
                elif ch == 1:
                    print("X", end=" ")
                elif ch == -1:
                    print("O", end=" ")
            print()

    def human_input_to_action(self):
        human_input = input("Enter an action: ")
        if (
            len(human_input) == 2
            and human_input[0] in self.board_markers
            and human_input[1] in self.board_markers
        ):
            x = ord(human_input[0]) - 65
            y = ord(human_input[1]) - 65
            if self.board[x][y] == 0:
                return True, x * self.board_size + y
        return False, -1

    def action_to_human_input(self, action):
        x = math.floor(action / self.board_size)
        y = action % self.board_size
        x = chr(x + 65)
        y = chr(y + 65)
        return x + y
