import random
import copy
from typing import List, Tuple

Recipe = Tuple[int,int,int,int]

### Named Constants
SUIT_MOUSE = 0
SUIT_RABBIT = 1
SUIT_FOX = 2
SUIT_BIRD = 3

ITEM_HAMMER = 0
ITEM_SWORD = 1
ITEM_BOOT = 2
ITEM_TEA = 3
ITEM_COINS = 4
ITEM_BAG = 5
ITEM_CROSSBOW = 6
ITEM_NONE = 7

N_PLAYERS = 2
PIND_MARQUISE = 0
PIND_EYRIE = 1

# MARQUISE
BIND_SAWMILL = 0
BIND_WORKSHOP = 1
BIND_RECRUITER = 2
TIND_KEEP = 0
TIND_WOOD = 1

# EYRIE
BIND_ROOST = 0
LEADER_BUILDER = 0
LEADER_CHARISMATIC = 1
LEADER_COMMANDER = 2
LEADER_DESPOT = 3
DECREE_RECRUIT = 0
DECREE_MOVE = 1
DECREE_BATTLE = 2
DECREE_BUILD = 3

class Clearing:
    def __init__(self,id:int,suit:int,num_building_slots:int,num_ruins:int,opposite_corner_id:int,adj_clearing_ids:list[int]) -> None:
        self.id = id
        self.suit = suit
        self.num_building_slots = num_building_slots
        self.num_ruins = num_ruins
        self.opposite_corner_id = opposite_corner_id
        self.warriors = {i:0 for i in range(N_PLAYERS)}
        self.tokens = {i:[] for i in range(N_PLAYERS)}
        self.buildings = {i:[] for i in range(N_PLAYERS)}
        self.adjacent_clearing_ids = adj_clearing_ids
    
    def get_num_empty_slots(self) -> int:
        "Returns the number of empty slots available to build in for the clearing."
        return self.num_building_slots - sum(len(x) for x in self.buildings.values())
    
    def get_ruling_power(self, faction_index:int) -> int:
        "Returns the total ruling power of the given faction: # of Warriors + # of buildings."
        return self.warriors[faction_index] + len(self.buildings[faction_index])
    
    def has_presence(self, faction_index:int) -> bool:
        """
        Returns True if any pieces of the given faction,
        including tokens, warriors, or buildings, are located in
        this clearing, and False otherwise.

        This means that that the given faction could be attacked.
        """
        return bool(self.get_ruling_power(faction_index) or len(self.tokens[faction_index]))

    def get_ruler(self) -> int:
        """
        Returns the player index of the player that rules the current clearing.
        If nobody returns the current clearing, returns -1.
        """
        num_marquise = self.get_ruling_power(PIND_MARQUISE)
        num_eyrie = self.get_ruling_power(PIND_EYRIE)

        if not (num_marquise + num_eyrie):
            return -1
        # the Eyrie rule tied clearings they have a piece in with "Lords of the Forest"
        return PIND_EYRIE if (num_eyrie >= num_marquise) else PIND_MARQUISE

    def is_ruler(self,faction_index:int) -> bool:
        "Returns True if the given faction IS the ruler of this clearing, False otherwise."
        return self.get_ruler() == faction_index
    
    ### BUILDING METHODS
    def get_num_buildings(self,faction_index:int,building_index:int = -1) -> int:
        """
        Returns the number of buildings of the given type for the given faction in the clearing.

        If no building index is specified, returns the total number of buildings
        for the given faction, regardless of their type.
        """
        return len(self.buildings[faction_index]) if (building_index == -1) else sum(x == building_index for x in self.buildings[faction_index])
    
    def place_building(self,faction_index:int,building_index:int) -> None:
        "Place the given building in this clearing. Assumes the move is legal, performing no checks."
        self.buildings[faction_index].append(building_index)
    
    def remove_building(self,faction_index:int,building_index:int) -> None:
        "Removes the given building in this clearing, assuming it exists. Does not handle points."
        self.buildings[faction_index].remove(building_index)


    ### TOKEN METHODS
    def get_num_tokens(self,faction_index:int,token_index:int) -> int:
        "Returns the number of tokens of the given type for the given faction in the clearing."
        return sum(x == token_index for x in self.tokens[faction_index])

    def place_token(self,faction_index:int,token_index:int) -> None:
        "Place the given token in this clearing. Assumes the move is legal, performing no checks."
        self.buildings[faction_index].append(token_index)
    
    def remove_token(self,faction_index:int,token_index:int) -> None:
        "Removes the given building in this clearing, assuming it exists. Does not handle points."
        self.buildings[faction_index].remove(token_index)
    
    ### WARRIOR METHODS
    def get_num_warriors(self,faction_index:int) -> int:
        "Returns the number of warriors of the given faction in the clearing."
        return self.warriors[faction_index]

    def change_num_warriors(self,faction_index:int,change:int) -> None:
        """
        Adds the specified number of warriors of the specified faction to the clearing.
        Use a negative number to remove warriors. Does NOT change faction supply counts.
        """
        self.warriors[faction_index] += change
    

    def can_start_battle(self,attacker_index:int,defender_index:int) -> bool:
        """
        Returns True if one faction can attack the other as directed
        in this particular clearing, and False otherwise.
        """
        return bool( self.warriors[attacker_index] and self.has_presence(defender_index) )

    def can_place(self,faction_index:int) -> bool:
        """
        Returns True if the faction can place a piece in this clearing. This is mainly affected
        by the Marquise's Keep, which blocks other Factions from placing pieces in its clearing.
        """
        return (faction_index == PIND_MARQUISE) or (TIND_KEEP not in self.tokens[PIND_MARQUISE])


class Board:
    def __init__(self, board_comp:list[Clearing]) -> None:
        self.board_comp = board_comp
        self.reset()
    
    def reset(self):
        "Resets the map to the cleared starting state."
        self.clearings = copy.deepcopy(self.board_comp)
    
    def get_total_building_counts(self,faction_index:int,building_index:int = -1):
        """
        Finds the number of buildings of the given faction in each clearing.
        If no building type is specified, returns the total number
        of buildings belonging to the given faction in each clearing.

        Returns a list of integers, with each index matching the corresponding clearing index.
        """
        return [x.get_num_buildings(faction_index,building_index) for x in self.clearings]
    
    def get_clearing_building_counts(self,faction_index:int,clearing_index:int,building_index:int = -1):
        """
        Returns the number of buildings of the given faction in the GIVEN clearing.
        If no building type is specified, returns the total number
        of buildings belonging to the given faction in the ONE clearing.
        """
        return self.clearings[clearing_index].get_num_buildings(faction_index,building_index)

    def move_warriors(self,faction_index:int,amount:int,start_index:int,end_index:int):
        """
        Subtracts warriors of a faction from one clearing, and adds them to another.
        Performs no other checks / assumes the move will be legal.
        """
        start_c,end_c = self.clearings[start_index],self.clearings[end_index]
        
        start_c.change_num_warriors(faction_index,-amount)
        end_c.change_num_warriors(faction_index,amount)
    
    def place_warriors(self,faction_index:int,amount:int,clearing_index:int):
        "Adds the given number of warriors of the faction to the clearing, assuming it is legal to do so."
        self.clearings[clearing_index].change_num_warriors(faction_index,amount)

    def deal_hits(self,faction_index:int,amount:int,clearing_index:int):
        """
        Make the given faction take a certain number of hits in the given clearing.
        Removes warriors first, then buildings/tokens if necessary. 

        TODO: Have some system to tell it which buildings/tokens to take out first?
        """
        target_clearing = self.clearings[clearing_index]
        for i in range(amount):
            if target_clearing.get_num_warriors(faction_index):
                target_clearing.change_num_warriors(faction_index,-1)
            else:
                break
    


class Card:
    def __init__(self,id:int,suit:int,name:str,recipe:Recipe,is_ambush:bool,is_dominance:bool,item:int,points:int) -> None:
        self.id = id
        self.suit = suit
        self.name = name
        self.crafting_recipe = recipe
        self.is_ambush = is_ambush
        self.is_dominance = is_dominance
        self.crafting_item = item
        self.points = points

class Deck:
    def __init__(self, deck_comp:list[tuple[Card,int]]):
        self.deck_comp = deck_comp
        self.reset()
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def reset(self):
        "Remakes the deck from the starting composition and then shuffles it."
        self.cards = []
        for card,amount in self.deck_comp:
            addition = [card for i in range(amount)]
            self.cards += addition
        self.shuffle()

    def draw(self, n):
        """
        Attempts to draw n cards from the deck by popping from the 'cards' list.
        Returns a list of the card objects drawn.

        If the deck runs out, simply returns all of the cards it could draw.
        """
        drawn = []
        for x in range(n):
            try:
                drawn.append(self.cards.pop())
            except:
                pass
        return drawn
    
    def add(self, cards:list[Card]):
        for card in cards:
            self.cards.append(card)
                
    def size(self):
        return len(self.cards)


class Player:
    def __init__(self,id:int) -> None:
        self.id = id
        self.warrior_storage = 0
        self.buildings = {}
        self.tokens = {}
        self.crafted_items = {i:0 for i in range(7)}
        self.hand = []

    def get_num_buildings_on_track(self, building_index:int) -> int:
        "Returns the number of buildings of the given type left on this player's track."
        return self.buildings[building_index]

    def change_num_warriors(self, change:int) -> None:
        """
        Changes the number of warriors in this faction's supply by adding 'change'.
        Use a negative number to remove warriors.
        """
        self.warrior_storage += change
    
    def change_num_buildings(self, building_index:int, change:int) -> None:
        """
        Changes the number of buildings of the given type in this faction's supply by adding 'change'.
        Use a negative number to remove buildings of the given type.
        """
        self.buildings[building_index] += change
    
    def change_num_tokens(self, token_index:int, change:int) -> None:
        """
        Changes the number of tokens of the given type in this faction's supply by adding 'change'.
        Use a negative number to remove tokens of the given type.
        """
        self.tokens[token_index] += change
    
    def change_num_items(self, item_index:int, change:int) -> None:
        """
        Changes the number of items of the given type in this faction's supply by adding 'change'.
        Use a negative number to remove items of the given type.
        """
        self.crafted_items[item_index] += change


class Marquise(Player):
    building_costs = [0,1,2,3,3,4]
    point_tracks = {}
    point_tracks[BIND_SAWMILL] = [0,1,2,3,4,5]
    point_tracks[BIND_WORKSHOP] = [0,2,2,3,4,5]
    point_tracks[BIND_RECRUITER] = [0,1,2,3,3,4]

    def __init__(self, id: int,) -> None:
        super().__init__(id)
        self.warrior_storage = 25
        for i in range(3):
            self.buildings[i] = 6
        self.tokens[TIND_KEEP] = 1
        self.tokens[TIND_WOOD] = 8

    def get_num_cards_to_draw(self) -> int:
        "Returns the number of cards to draw at the end of the turn (In Evening)."
        recruiters_left = self.get_num_buildings_on_track(BIND_RECRUITER)
        if recruiters_left > 3:
            return 1
        elif recruiters_left > 1:
            return 2
        return 3

    def update_from_building_placed(self, building_index:int) -> int:
        """
        Updates the player board as if the given building was placed:
        - Removes 1 building from the corresponding track
        - Adds the amount of wood that would be spent back to the token storage

        Returns the number of Victory Points scored.
        """
        i = 6 - self.get_num_buildings_on_track(building_index)
        building_cost = Marquise.building_costs[i]
        self.change_num_buildings(building_index,-1)
        self.change_num_tokens(TIND_WOOD, building_cost)

        return Marquise.point_tracks[building_index][i]
    

class Eyrie(Player):
    roost_points = [0,1,2,3,4,4,5]
    leader_starting_viziers = { # (Recruit, Move, Battle, Build)
        LEADER_BUILDER:     (1,1,0,0),
        LEADER_CHARISMATIC: (1,0,1,0),
        LEADER_COMMANDER:   (0,1,1,0),
        LEADER_DESPOT:      (0,1,0,1)
    }

    def __init__(self, id: int) -> None:
        super().__init__(id)
        self.warrior_storage = 20
        self.buildings[BIND_ROOST] = 7
        self.available_leaders = {0,1,2,3}
        self.deposed_leaders = set()
        self.chosen_leader_index = None
        self.decree = {i:[] for i in range(4)}
        self.viziers = [Card(CID_LOYAL_VIZIER,SUIT_BIRD,"Loyal Vizier",(0,0,0,0),False,False,ITEM_NONE,0) for i in range(2)]
    
    def get_num_cards_to_draw(self) -> int:
        "Returns the number of cards to draw at the end of the turn (In Evening)."
        recruiters_left = self.get_num_buildings_on_track(BIND_ROOST)
        if recruiters_left > 4:
            return 1
        elif recruiters_left > 1:
            return 2
        return 3
    
    def get_points_to_score(self) -> int:
        "Returns the number of points that should be scored in the evening phase."
        x = self.get_num_buildings_on_track(BIND_ROOST)
        if x == 7:
            return 0
        return self.roost_points[6 - x]

    def place_roost(self) -> None:
        "Removes 1 roost from the track, as if it was placed on the board."
        self.change_num_buildings(BIND_ROOST,-1)
    
    def choose_new_leader(self, leader_index:int) -> None:
        """
        Sets the given leader as the new leader of the Eyries. Assumes that the two
        Loyal Vizier Cards are in the factions list of viziers, and will attempt to
        place them in the corresponding Decree columns for the given leader.
        """
        self.chosen_leader_index = leader_index
        self.available_leaders.remove(leader_index)

        # Place the starting viziers for the new leader
        for i, place_vizier in enumerate(Eyrie.leader_starting_viziers[leader_index]):
            if place_vizier:
                self.decree[i].append(self.viziers.pop())
    
    def turmoil_helper(self):
        """
        Resolves several actions as if Turmoil has just occured:
        - Takes out the Loyal Viziers from the Decree
        - Completely empties the decree
        - Removes the current leader and resets the available leaders if needed

        Returns a tuple containing two items:
        - list: contains all of the card objects in the decree that should be discarded
        - int: the number of bird cards that were in the
        decree in total, which is the number of points that the Eyrie should lose
        """
        num_bird_cards = 0
        cards_to_discard = []

        # we want to remove the two viziers, but will
        # simultaneously count the number of bird cards
        # in the entire decree
        for card_list in self.decree.values():
            num_birds_in_this_slot = sum(x.suit == SUIT_BIRD for x in card_list)
            # this slot only matters now if any birds are in it
            if num_birds_in_this_slot:
                num_bird_cards += num_birds_in_this_slot
                for i,card in enumerate(card_list):
                    if card.id == CID_LOYAL_VIZIER:
                        # This is a loyal vizier, which we need to keep for the Eyrie's board
                        # We can safely pop the card because at most one will appear in each of these lists
                        self.viziers.append(card_list.pop(i))
                        break
            # add the non-vizier cards to the list to discard
            cards_to_discard += card_list
        
        # reset the decree
        self.decree = {i:[] for i in range(4)}

        # depose the current leader
        self.deposed_leaders.add(self.chosen_leader_index)
        self.chosen_leader_index = None
        if len(self.deposed_leaders) == 4:
            # reset available leaders if all 4 have been deposed
            self.available_leaders = {0,1,2,3}
            self.deposed_leaders.clear()

        return cards_to_discard, num_bird_cards


# (Card info, Amount in deck)
# Recipe amounts are (Mouse, Bunny, Fox, Wild)
STANDARD_DECK_COMP = [
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
    (Card(17, SUIT_FOX,    "Favor of the Foxes",   (0,0,3,0),   False,     False,  ITEM_NONE,     0),      1),
    (Card(18, SUIT_MOUSE,  "Favor of the Mice",    (3,0,0,0),   False,     False,  ITEM_NONE,     0),      1),
    (Card(19, SUIT_RABBIT, "Favor of the Rabbits", (0,3,0,0),   False,     False,  ITEM_NONE,     0),      1),
    (Card(20, SUIT_FOX,    "Foxfolk Steel",        (0,0,2,0),   False,     False,  ITEM_SWORD,    2),      1),
    # (id,   Suit,        Name,                    Recipe,    is_ambush, is_dom, item,          points), Amount
    (Card(21, SUIT_FOX,    "Gently Used Knapsack", (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(22, SUIT_MOUSE,   "Investments",         (0,2,0,0),   False,     False,  ITEM_COINS,    3),      1),
    (Card(23, SUIT_MOUSE,    "Mouse-in-a-Sack",    (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(24, SUIT_FOX,   "Protection Racket",     (0,2,0,0),   False,     False,  ITEM_COINS,    3),      1),
    (Card(25, SUIT_RABBIT,  "Root Tea (Rabbit)",   (1,0,0,0),   False,     False,  ITEM_TEA,      2),      1),
    (Card(26, SUIT_FOX,  "Root Tea (Fox)",         (1,0,0,0),   False,     False,  ITEM_TEA,      2),      1),
    (Card(27, SUIT_MOUSE,  "Root Tea (Mouse)",     (1,0,0,0),   False,     False,  ITEM_TEA,      2),      1),
    (Card(28, SUIT_BIRD,  "Sappers",               (1,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(29, SUIT_MOUSE,  "Scouting Party",       (2,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(30, SUIT_RABBIT, "Smuggler's Trail",     (1,0,0,0),   False,     False,  ITEM_BAG,      1),      1),
    (Card(31, SUIT_FOX,   "Stand and Deliver!",    (3,0,0,0),   False,     False,  ITEM_NONE,     0),      2),
    (Card(32, SUIT_MOUSE,   "Sword",               (0,0,2,0),   False,     False,  ITEM_SWORD,    2),      1),
    (Card(33, SUIT_FOX,   "Tax Collector",         (1,1,1,0),   False,     False,  ITEM_NONE,     0),      3),
    (Card(34, SUIT_FOX,   "Travel Gear (Fox)",     (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(35, SUIT_MOUSE,   "Travel Gear (Mouse)", (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(36, SUIT_BIRD,   "Woodland Runners",     (0,1,0,0),   False,     False,  ITEM_BOOT,     1),      1),
    (Card(37, SUIT_BIRD,  "Royal Claim",           (0,0,0,4),   False,     False,  ITEM_NONE,     0),      1)
#    (Card(38,SUIT_BIRD,   "Bird Dominance",        (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(39,SUIT_RABBIT,  "Bunny Dominance",      (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(40,SUIT_MOUSE,  "Mouse Dominance",       (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(41,SUIT_FOX,    "Fox Dominance",         (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
]
CID_ROYAL_CLAIM = 37
CID_LOYAL_VIZIER = len(STANDARD_DECK_COMP)

MAP_AUTUMN = [
    #        id, suit,         num_building_slots, num_ruins, opposite_corner_id, list of adj clearings
    Clearing(0,  SUIT_FOX,     1,                 0,         11,                  [1,3,4]),
    Clearing(1,  SUIT_RABBIT,  2,                 0,         -1,                  [0,2]),
    Clearing(2,  SUIT_MOUSE,   2,                 0,         8,                   [1,3,7]),
    Clearing(3,  SUIT_RABBIT,  1,                 1,         -1,                  [0,2,5]),
    Clearing(4,  SUIT_MOUSE,   2,                 0,         -1,                  [0,5,8]),
    Clearing(5,  SUIT_FOX,     1,                 1,         -1,                  [3,4,6,8,10]),
    Clearing(6,  SUIT_MOUSE,   2,                 1,         -1,                  [5,7,11]),
    Clearing(7,  SUIT_FOX,     1,                 1,         -1,                  [2,6,11]),
    Clearing(8,  SUIT_RABBIT,  1,                 0,         2,                   [4,5,9]),
    Clearing(9,  SUIT_FOX,     2,                 0,         -1,                  [8,10]),
    Clearing(10, SUIT_MOUSE,   2,                 0,         -1,                  [5,9,11]),
    Clearing(11, SUIT_RABBIT,  1,                 0,         0,                   [6,7,10])
]