import copy
import random
from typing import Tuple
import logging

Recipe = Tuple[int,int,int,int]

logging.basicConfig(filename='file.log',format="%(asctime)s|%(levelname)s|%(name)s|%(message)s")
logger = logging.getLogger("classes")
logger.setLevel(logging.DEBUG)

### Named Constants
SUIT_MOUSE = 0
SUIT_RABBIT = 1
SUIT_FOX = 2
SUIT_BIRD = 3
ID_TO_SUIT = {
    SUIT_MOUSE: "Mouse",
    SUIT_RABBIT: "Rabbit",
    SUIT_FOX: "Fox",
    SUIT_BIRD: "Bird"
}

ITEM_HAMMER = 0
ITEM_SWORD = 1
ITEM_BOOT = 2
ITEM_TEA = 3
ITEM_COINS = 4
ITEM_BAG = 5
ITEM_CROSSBOW = 6
ITEM_NONE = 7
ID_TO_ITEM = {
    ITEM_HAMMER: "Hammer",
    ITEM_SWORD: "Sword",
    ITEM_BOOT: "Boot",
    ITEM_TEA: "Tea",
    ITEM_COINS: "Coins",
    ITEM_BAG: "Bag",
    ITEM_CROSSBOW: "Crossbow",
    ITEM_NONE: "None"
}

N_PLAYERS = 2
PIND_MARQUISE = 0
PIND_EYRIE = 1
ID_TO_PLAYER = {
    PIND_MARQUISE: "Marquise de Cat",
    PIND_EYRIE: "Eyrie Dynasties",
    -1: "None"
}

# MARQUISE
BIND_SAWMILL = 0
BIND_WORKSHOP = 1
BIND_RECRUITER = 2
TIND_KEEP = 0
TIND_WOOD = 1
ID_TO_MBUILD = {
    BIND_SAWMILL: "Sawmill",
    BIND_WORKSHOP: "Workshop",
    BIND_RECRUITER: "Recruiter"
}
ID_TO_MTOKEN = {
    TIND_KEEP: "THE KEEP",
    TIND_WOOD: "Wood"
}

AID_SPEND_BIRD = 117
AID_ORDER_KEEP = 128
AID_ORDER_WOOD = 129
AID_ORDER_SAWMILL = 130
AID_ORDER_WORKSHOP = 131
AID_ORDER_RECRUITER = 132
AID_RECRUIT = 127
AID_OVERWORK = 133

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
ID_TO_LEADER = {
    LEADER_BUILDER: "Builder",
    LEADER_CHARISMATIC: "Charismatic",
    LEADER_COMMANDER: "Commander",
    LEADER_DESPOT: "Despot",
    None: "None"
}
ID_TO_DECREE = {
    DECREE_RECRUIT: "Recruit",
    DECREE_MOVE: "Move",
    DECREE_BATTLE: "Battle",
    DECREE_BUILD: "Build"
}

AID_CHOOSE_LEADER = 4358
AID_DECREE_RECRUIT = 4362
AID_DECREE_MOVE = 4404
AID_DECREE_BATTLE = 4446
AID_DECREE_BUILD = 4488

# Action IDs
AID_GENERIC_SKIP = 0
AID_CHOOSE_CLEARING = 1
AID_BATTLE = 13
AID_BUILD1 = 25
AID_BUILD2 = 37
AID_BUILD3 = 49
AID_CRAFT_CARD = 61
AID_CRAFT_ROYAL_CLAIM = 102
AID_CRAFT_RC_MAPPING = {
    AID_CRAFT_ROYAL_CLAIM:      (4,0,0),
    AID_CRAFT_ROYAL_CLAIM + 1:  (0,4,0),
    AID_CRAFT_ROYAL_CLAIM + 2:  (0,0,4),
    AID_CRAFT_ROYAL_CLAIM + 3:  (3,1,0),
    AID_CRAFT_ROYAL_CLAIM + 4:  (3,0,1),
    AID_CRAFT_ROYAL_CLAIM + 5:  (1,3,0),
    AID_CRAFT_ROYAL_CLAIM + 6:  (1,0,3),
    AID_CRAFT_ROYAL_CLAIM + 7:  (0,3,1),
    AID_CRAFT_ROYAL_CLAIM + 8:  (0,1,3),
    AID_CRAFT_ROYAL_CLAIM + 9:  (2,2,0),
    AID_CRAFT_ROYAL_CLAIM + 10: (2,0,2),
    AID_CRAFT_ROYAL_CLAIM + 11: (0,2,2),
    AID_CRAFT_ROYAL_CLAIM + 12: (2,1,1),
    AID_CRAFT_ROYAL_CLAIM + 13: (1,2,1),
    AID_CRAFT_ROYAL_CLAIM + 14: (1,1,2),
}
AID_DISCARD_CARD = 637
AID_MOVE = 679

AID_AMBUSH_MOUSE = 4279
AID_AMBUSH_RABBIT = 4280
AID_AMBUSH_FOX = 4281
AID_AMBUSH_BIRD = 4282
AID_AMBUSH_NONE = 4283

AID_EFFECTS_NONE = 4284
AID_EFFECTS_ARMORERS = 4285
AID_EFFECTS_BRUTTACT = 4286
AID_EFFECTS_SAPPERS = 4287
AID_EFFECTS_ARM_BT = 4288
AID_EFFECTS_ARMSAP = 4289

AID_CARD_BBB = 4290
AID_CARD_ROYAL_CLAIM = 4291
AID_CARD_STAND_DELIVER = 4292
AID_CARD_CODEBREAKERS = 4293
AID_CARD_TAX_COLLECTOR = 4294
AID_CARD_COMMAND_WARREN = 4306

class Clearing:
    def __init__(self,id:int,suit:int,num_building_slots:int,num_ruins:int,opposite_corner_id:int,adj_clearing_ids:set[int]) -> None:
        self.id = id
        self.suit = suit
        self.num_building_slots = num_building_slots
        self.num_ruins = num_ruins
        self.opposite_corner_id = opposite_corner_id
        self.warriors = {i:0 for i in range(N_PLAYERS)}
        self.tokens = {i:[] for i in range(N_PLAYERS)}
        self.buildings = {i:[] for i in range(N_PLAYERS)}
        self.adjacent_clearing_ids = adj_clearing_ids
    
    def __str__(self) -> str:
        ret = f"Clearing {self.id} ({ID_TO_SUIT[self.suit]}) - Ruler: {ID_TO_PLAYER[self.get_ruler()]}"
        ret += f"\n{self.warriors[PIND_MARQUISE]} Marquise Warriors"
        ret += f"\n{self.warriors[PIND_EYRIE]} Eyrie Warriors"
        ret += f"\nAdjacent Clearings: {[self.adjacent_clearing_ids]}"
        ret += f"\n{self.get_num_empty_slots()} Empty Building Spots"

        foo = []
        for bid in self.buildings[PIND_MARQUISE]:
            foo.append(ID_TO_MBUILD[bid])
        if len(self.buildings[PIND_EYRIE]) > 0:
            foo.append("Roost")
        if len(foo) > 0:
            ret += "\nBuildings: " + " ".join(foo)
        foo = []
        for tid in self.tokens[PIND_MARQUISE]:
            foo.append(ID_TO_MTOKEN[tid])
        if len(foo) > 0:
            ret += "\nTokens: " + " ".join(foo)
        return ret + "\n"
    
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
        logger.debug(f"\t\tBuilding {building_index} added for {ID_TO_PLAYER[faction_index]} in clearing {self.id}")
        self.buildings[faction_index].append(building_index)
    
    def remove_building(self,faction_index:int,building_index:int) -> None:
        "Removes the given building in this clearing, assuming it exists. Does not handle points."
        logger.debug(f"\t\tBuilding {building_index} removed for {ID_TO_PLAYER[faction_index]} in clearing {self.id}")
        self.buildings[faction_index].remove(building_index)


    ### TOKEN METHODS
    def get_num_tokens(self,faction_index:int,token_index:int = -1) -> int:
        """Returns the number of tokens of the given type for the given faction in the clearing.

        If no token index is specified, returns the total number of tokens
        for the given faction, regardless of their type.
        """
        return len(self.tokens[faction_index]) if (token_index == -1) else sum(x == token_index for x in self.tokens[faction_index])

    def place_token(self,faction_index:int,token_index:int) -> None:
        "Place the given token in this clearing. Assumes the move is legal, performing no checks."
        logger.debug(f"\t\tToken {token_index} added for {ID_TO_PLAYER[faction_index]} in clearing {self.id}")
        self.tokens[faction_index].append(token_index)
    
    def remove_token(self,faction_index:int,token_index:int) -> None:
        "Removes the given token in this clearing, assuming it exists. Does not handle points."
        logger.debug(f"\t\tToken {token_index} removed for {ID_TO_PLAYER[faction_index]} in clearing {self.id}")
        self.tokens[faction_index].remove(token_index)
    
    ### WARRIOR METHODS
    def get_num_warriors(self,faction_index:int) -> int:
        "Returns the number of warriors of the given faction in the clearing."
        return self.warriors[faction_index]

    def change_num_warriors(self,faction_index:int,change:int) -> None:
        """
        Adds the specified number of warriors of the specified faction to the clearing.
        Use a negative number to remove warriors. Does NOT change faction supply counts.
        """
        logger.debug(f"\t\tWarriors changed by {change} for {ID_TO_PLAYER[faction_index]} in clearing {self.id}")
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
    
    def is_adjacent_to(self,other_index:int):
        "Returns True only if this clearing is connected to the clearing with the other index given."
        return (other_index in self.adjacent_clearing_ids)
    
    def favor_helper(self,safe_faction_index:int):
        """
        Helps with the process of resolving a favor card. Removes any
        and all warriors, buildings, and tokens of all factions that are
        not the safe faction given.

        Returns a 2-tuple: the total number of points that
        should be scored from removing tokens/buildings in this clearing,
        and the number of Marquise warriors removed (for Field Hospitals).
        """
        ans = marqwar = 0
        for faction_i in {j for j in range(N_PLAYERS) if j != safe_faction_index}:
            ans += self.get_num_buildings(faction_i) + self.get_num_tokens(faction_i)
            if faction_i == PIND_MARQUISE:
                marqwar = self.get_num_warriors(faction_i)
                
        return ans,marqwar


class Board:
    def __init__(self, board_comp:list[Clearing]) -> None:
        self.board_comp = board_comp
        self.reset()
    
    def __str__(self) -> str:
        s = "Current Board:\n"
        for c in self.clearings:
            s += str(c) + "\n"
        return s

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
        Returns the number of buildings of the given faction of the given type in the GIVEN clearing.
        If no building type is specified, returns the total number
        of buildings belonging to the given faction in the ONE clearing.
        """
        return self.clearings[clearing_index].get_num_buildings(faction_index,building_index)

    def get_clearing_token_counts(self,faction_index:int,clearing_index:int,token_index:int = -1):
        """
        Returns the number of buildings of the given faction of the given type in the GIVEN clearing.
        If no building type is specified, returns the total number
        of buildings belonging to the given faction in the ONE clearing.
        """
        return self.clearings[clearing_index].get_num_tokens(faction_index,token_index)
    
    def get_empty_building_slot_counts(self):
        """
        Finds the number of empty building slots in each clearing on
        the board. Returns a list of integers, one for each corresponding clearing.
        """
        return [x.get_num_empty_slots() for x in self.clearings]

    def get_rulers(self):
        """
        Finds the current ruling faction of each clearing. Returns a list of integers,
        each corresponding to the faction ID of the ruler in the given clearing, or
        a -1 if there is no ruler of the clearing.
        """
        return [x.get_ruler() for x in self.clearings]
    
    def get_possible_battles(self,attacker_index:int,defender_index:int):
        """
        Returns a list of all of the places where the given faction can start
        a battle with the target faction.

        Returns a list of booleans, one for each clearing.
        """
        return [x.can_start_battle(attacker_index,defender_index) for x in self.clearings]
    
    def get_num_warriors(self,faction_index:int):
        "Returns a list of the number of warriors of the given faction in each clearing."
        return [x.get_num_warriors(faction_index) for x in self.clearings]
    
    def get_crafting_power(self,faction_index:int):
        """
        Returns the crafting power of the given faction. This is
        represented by a list of integers:
        - [Mouse Power / Rabbit Power / Fox Power]
        """
        power = [0,0,0]
        if faction_index == PIND_MARQUISE:
            buildings = self.get_total_building_counts(PIND_MARQUISE,BIND_WORKSHOP)
        else:
            buildings = self.get_total_building_counts(PIND_EYRIE,BIND_ROOST)

        for clearing_i,num_buildings in enumerate(buildings):
            if num_buildings:
                c = self.clearings[clearing_i]
                power[c.suit] += num_buildings
        return power
    
    def get_legal_move_actions(self,faction_index:int,starting_suits:set[int]):
        """
        Finds every possible distinct legal move that the given faction can currently
        make on the board. The start clearing of each move must have its suit in starting_suits.

        Returns a list of integers: the AID's of each distinct move possible.
        """
        ans = []
        for i,start_clearing in enumerate(self.clearings):
            n_warriors = start_clearing.get_num_warriors(faction_index)
            if (n_warriors == 0) or (start_clearing.suit not in starting_suits):
                continue
            valid_dest_ids = []
            if start_clearing.is_ruler(faction_index):
                valid_dest_ids += list(start_clearing.adjacent_clearing_ids)
            else:
                for dest_id in start_clearing.adjacent_clearing_ids:
                    if self.clearings[dest_id].is_ruler(faction_index):
                        valid_dest_ids.append(dest_id)

            ans += [(i*300+j*25+a+AID_MOVE) for j in valid_dest_ids for a in range(n_warriors)]
        return ans
    
    def move_warriors(self,faction_index:int,amount:int,start_index:int,end_index:int):
        """
        Subtracts warriors of a faction from one clearing, and adds them to another.
        Performs no other checks / assumes the move will be legal.
        """
        logger.debug(f"\tMoving {amount} warriors of {ID_TO_PLAYER[faction_index]} from {start_index} to {end_index}")
        start_c,end_c = self.clearings[start_index],self.clearings[end_index]
        
        start_c.change_num_warriors(faction_index,-amount)
        end_c.change_num_warriors(faction_index,amount)

    def place_warriors(self,faction_index:int,amount:int,clearing_index:int):
        "Adds the given number of warriors of the faction to the clearing, assuming it is legal to do so."
        self.clearings[clearing_index].change_num_warriors(faction_index,amount)
    
    def place_building(self,faction_index:int,building_index:int,clearing_index:int):
        "Adds one of the given building type to the given clearing, assuming it's legal to do so."
        self.clearings[clearing_index].place_building(faction_index,building_index)

    def place_token(self,faction_index:int,token_index:int,clearing_index:int):
        "Adds one of the given building type to the given clearing, assuming it's legal to do so."
        self.clearings[clearing_index].place_token(faction_index,token_index)
    
    def resolve_favor(self,safe_faction_index:int,clearing_indexes:list[int]):
        """
        Resolves the effects of the safe faction crafting a favor card. The
        Effect is carried out in each clearing in the given list of indexes.

        Returns a 2-tuple: the total number of points scored by the
        activating player for removing buildings and tokens, and
        the list of Marquise warriors removed per clearing / the suit (for Field Hospitals)
        """
        ans = 0
        field_hospitals = []
        for i in clearing_indexes:
            pts,marqwars = self.clearings[i].favor_helper(safe_faction_index)
            ans += pts
            if marqwars > 0:
                field_hospitals.append( (marqwars,self.clearings[i].suit) )
        return ans,field_hospitals
    
    def get_wood_available(self):
        """
        For the Marquise, returns a list of integers, one for each clearing.
        The integer for clearing i is the amount of wood tokens available
        to use to Build in clearing i, either from that clearing or using
        any number of connected clearings ruled by the cats.

        If the Marquise do NOT rule clearing i, the amount of wood
        in that clearing is given as -1.
        """
        ans = [-1 for i in range(12)]
        # find out which clearings the Marquise rule - which is where wood actually counts
        foo = [(x == PIND_MARQUISE) for x in self.get_rulers()]
        clearings_left_to_assign = {i for i,ruled in enumerate(foo) if ruled}

        # make groups of connected clearings ruled by the Marquise
        while clearings_left_to_assign:
            i = clearings_left_to_assign.pop()
            new_group = {i}
            total = self.clearings[i].get_num_tokens(PIND_MARQUISE,TIND_WOOD)
            c_to_add_to_group = {j for j in self.clearings[i].adjacent_clearing_ids if j in clearings_left_to_assign}
            while c_to_add_to_group:
                j = c_to_add_to_group.pop()
                clearings_left_to_assign.remove(j)
                new_group.add(j)
                total += self.clearings[j].get_num_tokens(PIND_MARQUISE,TIND_WOOD)
                c_to_add_to_group.update( {k for k in self.clearings[j].adjacent_clearing_ids if k in (clearings_left_to_assign - c_to_add_to_group)} )

            for i in new_group:
                ans[i] = total
        return ans
    
    def get_wood_to_build_in(self, clearing_index:int):
        """
        For the Marquise, returns a list of integers, one for each clearing.
        Assuming that we are building in the given input clearing index, the
        integer in index i of the returned list is the number of wood tokens
        available to legally take out of clearing i for contributing to the build.

        Thus, a clearing that has 1+ wood tokens, but is NOT connected by rule to
        the building clearing will show up as 0, as it has no usable wood for this build.
        """
        ans = [0 for i in range(12)]
        # it is assumed that the given clearing is ruled by the Marquise (required to build)
        clearings_checked = set()
        clearings_to_check = {clearing_index}
        while clearings_to_check:
            i = clearings_to_check.pop()
            clearings_checked.add(i)
            ans[i] = self.clearings[i].get_num_tokens(PIND_MARQUISE,TIND_WOOD)
            for j in self.clearings[i].adjacent_clearing_ids:
                if (j not in clearings_checked) and (self.clearings[j].get_ruler() == PIND_MARQUISE):
                    clearings_to_check.add(j)
        return ans
    

class Card:
    def __init__(self,id:int,suit:int,name:str,recipe:Recipe,is_ambush:bool,is_dominance:bool,is_persistent:bool,item:int,points:int) -> None:
        self.id = id
        self.suit = suit
        self.name = name
        self.crafting_recipe = recipe
        self.is_ambush = is_ambush
        self.is_dominance = is_dominance
        self.is_persistent = is_persistent
        self.crafting_item = item
        self.points = points
    
    def __str__(self) -> str:
        return f"{self.name} ({ID_TO_SUIT[self.suit]}) (ID {self.id}) ({self.points} Points) (Recipe {self.crafting_recipe})"

class Deck:
    def __init__(self, deck_comp:list[tuple[Card,int]]):
        self.deck_comp = deck_comp
        self.reset()
    
    def __str__(self) -> str:
        return f" - Deck - {self.size()} Cards\n"
    
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
        "Adds the given cards in the input to the deck and then shuffles the deck."
        for card in cards:
            self.cards.append(card)
        self.shuffle()
                
    def size(self):
        "Returns the current number of cards in the deck."
        return len(self.cards)


class Player:
    def __init__(self,id:int) -> None:
        self.id = id
        self.warrior_storage = 0
        self.buildings = {}
        self.tokens = {}
        self.crafted_items = {i:0 for i in range(7)}
        self.persistent_cards = []
        self.hand = []
    
    def __str__(self) -> str:
        ret = f"""Player ID {self.id}
    Warriors: {self.warrior_storage} - Buildings: {self.buildings} - Tokens: {self.tokens}
    Crafted Items: {self.crafted_items} - Crafted Cards: {[i.name for i in self.persistent_cards]}
    Hand:\n"""
        for card in self.hand:
            ret += f"\t- {str(card)}\n"
        return ret

    def get_num_buildings_on_track(self, building_index:int) -> int:
        "Returns the number of buildings of the given type left on this player's track."
        return self.buildings[building_index]
    
    def get_num_tokens_in_store(self, token_index:int) -> int:
        "Returns the number of tokens of the given type left in this player's store."
        return self.tokens[token_index]

    def change_num_warriors(self, change:int) -> None:
        """
        Changes the number of warriors in this faction's supply by adding 'change'.
        Use a negative number to remove warriors.
        """
        logger.debug(f"\t\t{ID_TO_PLAYER[self.id]} warrior storage changed by {change}")
        self.warrior_storage += change
    
    def change_num_buildings(self, building_index:int, change:int) -> None:
        """
        Changes the number of buildings of the given type in this faction's supply by adding 'change'.
        Use a negative number to remove buildings of the given type.
        """
        logger.debug(f"\t\t{ID_TO_PLAYER[self.id]} buildings ID {building_index} changed by {change}")
        self.buildings[building_index] += change
    
    def change_num_tokens(self, token_index:int, change:int) -> None:
        """
        Changes the number of tokens of the given type in this faction's supply by adding 'change'.
        Use a negative number to remove tokens of the given type.
        """
        logger.debug(f"\t\t{ID_TO_PLAYER[self.id]} tokens ID {token_index} changed by {change}")
        self.tokens[token_index] += change
    
    def change_num_items(self, item_index:int, change:int) -> None:
        """
        Changes the number of items of the given type in this faction's supply by adding 'change'.
        Use a negative number to remove items of the given type.
        """
        logger.debug(f"\t\t{ID_TO_PLAYER[self.id]} items ID {item_index} changed by {change}")
        self.crafted_items[item_index] += change
    
    def has_suit_in_hand(self, suit_id:int):
        """
        Returns True only if any card in the player's hand is
        either of the exact given suit OR is a BIRD card.
        """
        return any((c.suit in {suit_id, SUIT_BIRD}) for c in self.hand)

    def get_ambush_actions(self,clearing_suit:int):
        "Returns a list of all valid ambush AID's this player can do with their current hand in a clearing of the given suit."
        ans = set()
        valid_suits = {SUIT_BIRD,clearing_suit}
        for card in self.hand:
            if card.is_ambush and card.suit in valid_suits:
                ans.add(AID_AMBUSH_NONE)
                ans.add(card.suit + AID_AMBUSH_MOUSE)
        return list(ans)
    
    def get_attacker_card_actions(self):
        "Returns a list of all valid attacking AID's this player can do with their current persistent cards."
        ans = set()
        for card in self.persistent_cards:
            if card.id == CID_ARMORERS:
                ans.add(AID_EFFECTS_NONE)
                ans.add(AID_EFFECTS_ARMORERS)
            elif card.id == CID_BRUTAL_TACTICS:
                ans.add(AID_EFFECTS_NONE)
                ans.add(AID_EFFECTS_BRUTTACT)
        if len(ans) == 3:
            ans.add(AID_EFFECTS_ARM_BT)
        return list(ans)

    def get_defender_card_actions(self):
        "Returns a list of all valid defending AID's this player can do with their current persistent cards."
        ans = set()
        for card in self.persistent_cards:
            if card.id == CID_ARMORERS:
                ans.add(AID_EFFECTS_NONE)
                ans.add(AID_EFFECTS_ARMORERS)
            elif card.id == CID_SAPPERS:
                ans.add(AID_EFFECTS_NONE)
                ans.add(AID_EFFECTS_SAPPERS)
        if len(ans) == 3:
            ans.add(AID_EFFECTS_ARMSAP)
        return list(ans)
    
    def has_card_id_in_hand(self,id:int):
        "Returns True only if this player has a card with the given ID in their hand."
        return any(c.id == id for c in self.hand)
    

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
        self.keep_clearing_id = -1
    
    def __str__(self) -> str:
        return "--- Marquise de Cat ---\n" + super().__str__() + f"\nKeep placed in clearing {self.keep_clearing_id}"

    def get_num_cards_to_draw(self) -> int:
        "Returns the number of cards to draw at the end of the turn (In Evening)."
        recruiters_left = self.get_num_buildings_on_track(BIND_RECRUITER)
        if recruiters_left > 3:
            return 1
        elif recruiters_left > 1:
            return 2
        return 3

    def update_from_building_placed(self, building_index:int) -> tuple[int,int]:
        """
        Updates the player board as if the given building was placed:
        - Removes 1 building from the corresponding track
        - Wood token amounts should be handled outside when they are
        properly removed from the board

        Returns the number of wood to use and Victory Points scored.
        """
        i = 6 - self.get_num_buildings_on_track(building_index)
        self.change_num_buildings(building_index,-1)

        return Marquise.building_costs[i], Marquise.point_tracks[building_index][i]
    

class Eyrie(Player):
    roost_points = [0,0,1,2,3,4,4,5]
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
        self.available_leaders = [0,1,2,3]
        self.deposed_leaders = []
        self.chosen_leader_index = None
        self.decree = {i:[] for i in range(4)}
        self.viziers = [Card(CID_LOYAL_VIZIER,SUIT_BIRD,"Loyal Vizier",(0,0,0,0),False,False,False,ITEM_NONE,0) for i in range(2)]
    
    def __str__(self) -> str:
        ret = "--- Eyrie Dynasties ---\n" + super().__str__() + f"\nCurrent Leader: {ID_TO_LEADER[self.chosen_leader_index]} - Leaders Available: {[ID_TO_LEADER[i] for i in self.available_leaders]}\n"
        ret += "Decree:\n"
        for i,lst in self.decree.items():
            ret += f"\t{ID_TO_DECREE[i]}: {[(card.name,ID_TO_SUIT[card.suit]) for card in lst]}\n"
        return ret

    def get_num_cards_to_draw(self) -> int:
        "Returns the number of cards to draw at the end of the turn (In Evening)."
        roosts_left = self.get_num_buildings_on_track(BIND_ROOST)
        if roosts_left > 4:
            return 1
        elif roosts_left > 1:
            return 2
        return 3
    
    def get_points_to_score(self) -> int:
        "Returns the number of points that should be scored in the evening phase."
        x = self.get_num_buildings_on_track(BIND_ROOST)
        return self.roost_points[7 - x]

    def place_roost(self) -> None:
        "Removes 1 roost from the track, as if it was placed on the board."
        self.change_num_buildings(BIND_ROOST,-1)
    
    def add_to_decree(self,card_to_add:Card,decree_index:int):
        "Adds the given card object to the decree."
        logger.debug(f"\t\tCard {card_to_add.name} added to decree at {ID_TO_DECREE[decree_index]}")
        self.decree[decree_index].append(card_to_add)
    
    def choose_new_leader(self, leader_index:int) -> None:
        """
        Sets the given leader as the new leader of the Eyries. Assumes that the two
        Loyal Vizier Cards are in the factions list of viziers, and will attempt to
        place them in the corresponding Decree columns for the given leader.
        """
        logger.debug(f"\tNew Leader Chosen: {ID_TO_LEADER[leader_index]}")
        self.chosen_leader_index = leader_index
        self.available_leaders.remove(leader_index)

        # Place the starting viziers for the new leader
        for i, place_vizier in enumerate(Eyrie.leader_starting_viziers[leader_index]):
            if place_vizier:
                self.add_to_decree(self.viziers.pop(),i)
    
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
        self.deposed_leaders.append(self.chosen_leader_index)
        self.chosen_leader_index = None
        if len(self.deposed_leaders) == 4:
            # reset available leaders if all 4 have been deposed
            self.available_leaders = [0,1,2,3]
            self.deposed_leaders = []

        return cards_to_discard, num_bird_cards


class Battle:
    # a choice must be made about using an ambush card
    STAGE_DEF_AMBUSH = 0
    STAGE_ATT_AMBUSH = 1
    # choosing what extra effects/cards to activate
    STAGE_ATT_EFFECTS = 2
    STAGE_DEF_EFFECTS = 3
    # choosing the order in which their pieces will be damaged
    STAGE_ATT_ORDER = 4
    STAGE_DEF_ORDER = 5
    # the cats are given a choice whether to activate field hospitals or not
    STAGE_FIELD_HOSPITALS = 6
    # waiting for the dice roll
    STAGE_DICE_ROLL = 7
    # battle is done
    STAGE_DONE = 8

    def __init__(self,att_id:int,def_id:int,clearing_id:int) -> None:
        self.attacker_id = att_id
        self.defender_id = def_id
        self.clearing_id = clearing_id
        self.stage = None
        self.att_rolled_hits = None
        self.att_extra_hits = 0
        self.def_rolled_hits = None
        self.def_extra_hits = 0
        self.att_hits_to_deal = 0
        self.def_hits_to_deal = 0
        self.att_ambush_id = None
        self.def_ambush_id = None
        self.att_cardboard_removed = False
        self.def_cardboard_removed = False
    
    def __str__(self) -> str:
        ret = f"--- BATTLE: {ID_TO_PLAYER[self.attacker_id]} attacking {ID_TO_PLAYER[self.defender_id]} in Clearing {self.clearing_id} ---\n"
        ret += f"Roll: {(self.att_rolled_hits,self.def_rolled_hits)}"
        return ret

# (Card info, Amount in deck)
# Recipe amounts are (Mouse, Bunny, Fox, Wild)
STANDARD_DECK_COMP = [
    # (id,   Suit,        Name,                    Recipe,    is_ambush, is_dom, is_persistent    item,          points), Amount
    (Card(0, SUIT_BIRD,   "Ambush! (Bird)",        (0,0,0,0),   True,      False,   False,      ITEM_NONE,        0),      2),
    (Card(1, SUIT_RABBIT,  "Ambush! (Rabbit)",     (0,0,0,0),   True,      False,   False,      ITEM_NONE,        0),      1),
    (Card(2, SUIT_FOX,    "Ambush! (Fox)",         (0,0,0,0),   True,      False,   False,      ITEM_NONE,        0),      1),
    (Card(3, SUIT_MOUSE,  "Ambush! (Mouse)",       (0,0,0,0),   True,      False,   False,      ITEM_NONE,        0),      1),
    (Card(4, SUIT_FOX,    "Anvil",                 (0,0,1,0),   False,     False,   False,      ITEM_HAMMER,      2),      1),
    (Card(5, SUIT_BIRD,   "Armorers",              (0,0,1,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(6, SUIT_BIRD,   "Arms Trader",           (0,0,2,0),   False,     False,   False,      ITEM_SWORD,       2),      1),
    (Card(7, SUIT_RABBIT,  "A Visit to Friends",   (0,1,0,0),   False,     False,   False,      ITEM_BOOT,        1),      1),
    (Card(8, SUIT_RABBIT,  "Bake Sale",            (0,2,0,0),   False,     False,   False,      ITEM_COINS,       3),      1),
    (Card(9, SUIT_RABBIT,  "Better Burrow Bank",   (0,2,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(10,SUIT_BIRD,   "Birdy Bindle",          (1,0,0,0),   False,     False,   False,      ITEM_BAG,         1),      1),
    (Card(11,SUIT_BIRD,   "Brutal Tactics",        (0,0,2,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(12,SUIT_RABBIT,  "Cobbler",              (0,2,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(13,SUIT_MOUSE,  "Codebreakers",          (1,0,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(14,SUIT_RABBIT,  "Command Warren",       (0,2,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(15,SUIT_BIRD,   "Crossbow (Bird)",       (0,0,1,0),   False,     False,   False,      ITEM_CROSSBOW,    1),      1),
    (Card(16,SUIT_MOUSE,  "Crossbow (Mouse)",      (0,0,1,0),   False,     False,   False,      ITEM_CROSSBOW,    1),      1),
    (Card(17, SUIT_FOX,    "Favor of the Foxes",   (0,0,3,0),   False,     False,   False,      ITEM_NONE,        0),      1),
    (Card(18, SUIT_MOUSE,  "Favor of the Mice",    (3,0,0,0),   False,     False,   False,      ITEM_NONE,        0),      1),
    (Card(19, SUIT_RABBIT, "Favor of the Rabbits", (0,3,0,0),   False,     False,   False,      ITEM_NONE,        0),      1),
    (Card(20, SUIT_FOX,    "Foxfolk Steel",        (0,0,2,0),   False,     False,   False,      ITEM_SWORD,       2),      1),
    # (id,   Suit,        Name,                    Recipe,    is_ambush, is_dom, is_persistent    item,          points), Amount
    (Card(21, SUIT_FOX,    "Gently Used Knapsack", (1,0,0,0),   False,     False,   False,      ITEM_BAG,         1),      1),
    (Card(22, SUIT_MOUSE,   "Investments",         (0,2,0,0),   False,     False,   False,      ITEM_COINS,       3),      1),
    (Card(23, SUIT_MOUSE,    "Mouse-in-a-Sack",    (1,0,0,0),   False,     False,   False,      ITEM_BAG,         1),      1),
    (Card(24, SUIT_FOX,   "Protection Racket",     (0,2,0,0),   False,     False,   False,      ITEM_COINS,       3),      1),
    (Card(25, SUIT_RABBIT,  "Root Tea (Rabbit)",   (1,0,0,0),   False,     False,   False,      ITEM_TEA,         2),      1),
    (Card(26, SUIT_FOX,  "Root Tea (Fox)",         (1,0,0,0),   False,     False,   False,      ITEM_TEA,         2),      1),
    (Card(27, SUIT_MOUSE,  "Root Tea (Mouse)",     (1,0,0,0),   False,     False,   False,      ITEM_TEA,         2),      1),
    (Card(28, SUIT_BIRD,  "Sappers",               (1,0,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(29, SUIT_MOUSE,  "Scouting Party",       (2,0,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(30, SUIT_RABBIT, "Smuggler's Trail",     (1,0,0,0),   False,     False,   False,      ITEM_BAG,         1),      1),
    (Card(31, SUIT_FOX,   "Stand and Deliver!",    (3,0,0,0),   False,     False,   True,       ITEM_NONE,        0),      2),
    (Card(32, SUIT_MOUSE,   "Sword",               (0,0,2,0),   False,     False,   False,      ITEM_SWORD,       2),      1),
    (Card(33, SUIT_FOX,   "Tax Collector",         (1,1,1,0),   False,     False,   True,       ITEM_NONE,        0),      3),
    (Card(34, SUIT_FOX,   "Travel Gear (Fox)",     (0,1,0,0),   False,     False,   False,      ITEM_BOOT,        1),      1),
    (Card(35, SUIT_MOUSE,   "Travel Gear (Mouse)", (0,1,0,0),   False,     False,   False,      ITEM_BOOT,        1),      1),
    (Card(36, SUIT_BIRD,   "Woodland Runners",     (0,1,0,0),   False,     False,   False,      ITEM_BOOT,        1),      1),
    (Card(37, SUIT_BIRD,  "Royal Claim",           (0,0,0,4),   False,     False,   True,       ITEM_NONE,        0),      1)
#    (Card(38,SUIT_BIRD,   "Bird Dominance",        (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(39,SUIT_RABBIT,  "Bunny Dominance",      (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(40,SUIT_MOUSE,  "Mouse Dominance",       (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
#    (Card(41,SUIT_FOX,    "Fox Dominance",         (0,0,0,0),   False,     True,   ITEM_NONE,     0),      1),
]

CID_AMBUSH_BIRD = 0
CID_AMBUSH_RABBIT = 1
CID_AMBUSH_FOX = 2
CID_AMBUSH_MOUSE = 3
CID_ARMORERS = 5
CID_BRUTAL_TACTICS = 11
CID_SAPPERS = 28
CID_SCOUTING_PARTY = 29
CID_COBBLER = 12
CID_COMMAND_WARREN = 14
CID_CODEBREAKERS = 13
CID_STAND_AND_DELIVER = 31
CID_TAX_COLLECTOR = 33
CID_BBB = 9
CID_ROYAL_CLAIM = 37
CID_FAVORS = {17,18,19}
CID_LOYAL_VIZIER = len(STANDARD_DECK_COMP)

ACTION_TO_BIRD_ID = {
    AID_SPEND_BIRD: CID_AMBUSH_BIRD,
    AID_SPEND_BIRD + 1: CID_ARMORERS,
    AID_SPEND_BIRD + 2: 6, # arms trader
    AID_SPEND_BIRD + 3: 10, # birdy bindle
    AID_SPEND_BIRD + 4: CID_BRUTAL_TACTICS,
    AID_SPEND_BIRD + 5: 15, # bird crossbow
    AID_SPEND_BIRD + 6: CID_SAPPERS,
    AID_SPEND_BIRD + 7: 36,
    AID_SPEND_BIRD + 8: CID_ROYAL_CLAIM,
    AID_SPEND_BIRD + 9: 38,
}
BIRD_ID_TO_ACTION = {i:a for (a,i) in ACTION_TO_BIRD_ID.items()}

MAP_AUTUMN = [
    #        id, suit,         num_building_slots, num_ruins, opposite_corner_id, set of adj clearings
    Clearing(0,  SUIT_FOX,     1,                 0,         11,                  {1,3,4}),
    Clearing(1,  SUIT_RABBIT,  2,                 0,         -1,                  {0,2}),
    Clearing(2,  SUIT_MOUSE,   2,                 0,         8,                   {1,3,7}),
    Clearing(3,  SUIT_RABBIT,  1,                 1,         -1,                  {0,2,5}),
    Clearing(4,  SUIT_MOUSE,   2,                 0,         -1,                  {0,5,8}),
    Clearing(5,  SUIT_FOX,     1,                 1,         -1,                  {3,4,6,8,10}),
    Clearing(6,  SUIT_MOUSE,   2,                 1,         -1,                  {5,7,11}),
    Clearing(7,  SUIT_FOX,     1,                 1,         -1,                  {2,6,11}),
    Clearing(8,  SUIT_RABBIT,  1,                 0,         2,                   {4,5,9}),
    Clearing(9,  SUIT_FOX,     2,                 0,         -1,                  {8,10}),
    Clearing(10, SUIT_MOUSE,   2,                 0,         -1,                  {5,9,11}),
    Clearing(11, SUIT_RABBIT,  1,                 0,         0,                   {6,7,10})
]

CLEARING_SUITS = {
    SUIT_FOX: [c.id for c in MAP_AUTUMN if c.suit == SUIT_FOX],
    SUIT_MOUSE: [c.id for c in MAP_AUTUMN if c.suit == SUIT_MOUSE],
    SUIT_RABBIT: [c.id for c in MAP_AUTUMN if c.suit == SUIT_RABBIT]
}