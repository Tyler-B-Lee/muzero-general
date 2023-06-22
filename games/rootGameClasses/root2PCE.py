import math
import random
import numpy as np
from classes import *

class root2pCatsVsEyrie:
    PHASE_SETUP_MARQUISE = 0
    PHASE_SETUP_EYRIE = 1
    PHASE_BIRDSONG_MARQUISE = 2
    PHASE_BIRDSONG_EYRIE = 3
    PHASE_DAYLIGHT_MARQUISE = 4
    PHASE_DAYLIGHT_EYRIE = 5
    PHASE_EVENING_MARQUISE = 6
    PHASE_EVENING_EYRIE= 7

    def __init__(self, board_composition:list, deck_composition:list):
        self.n_players = N_PLAYERS
        self.board = Board(board_composition)
        self.deck = Deck(deck_composition)

        self.reset_general_items()
        self.reset_for_marquise()
        self.reset_for_eyrie()

    def to_play(self):
        return 0 if self.current_player == 1 else 1
    
    def index_to_id(self,x):
        "Converts 0 to 1, 1 to -1"
        return 1 if (x == 0) else -1
    
    def reset_general_items(self):
        self.saved_actions = None
        self.saved_battle_actions = None
        self.saved_battle_player = None
        self.points_scored_this_turn = 0
        self.current_player = 1
        self.players = [Marquise(0), Eyrie(1)]
        self.victory_points = [0,0]
        self.phase = self.PHASE_SETUP_MARQUISE
        self.phase_steps = 0
        self.field_hospitals = []
        self.persistent_used_this_turn = set()
        # self.available_dominances = set()
        self.remaining_craft_power = [0]
        self.board.reset()
        self.deck.reset()
        self.battle = Battle(-1,-1,-1)
        self.battle.stage = Battle.STAGE_DONE
        self.discard_pile = []
        self.available_items = {
            ITEM_COINS: 2,
            ITEM_BOOT: 2,
            ITEM_BAG: 2,
            ITEM_TEA: 2,
            ITEM_SWORD: 2,
            ITEM_CROSSBOW: 1,
            ITEM_HAMMER: 1
        }
        self.first_player = random.choice([-1,1])
        self.draw_cards(PIND_MARQUISE,3)
        self.draw_cards(PIND_EYRIE,3)
    def reset_for_marquise(self):
        self.wood_placement_started = False
        self.starting_build_spots = [0]
        self.available_wood_spots = [0]
        self.available_recruiters = [0]
        self.marquise_actions = 3
        self.marquise_moves = 2
        self.recruited_this_turn = 0
        self.remaining_wood_cost = 0
    def reset_for_eyrie(self):
        self.eyrie_cards_added = 0
        self.eyrie_bird_added = 0
        self.remaining_decree = {
            DECREE_RECRUIT: [0,0,0,0],
            DECREE_MOVE: [0,0,0,0],
            DECREE_BATTLE: [0,0,0,0],
            DECREE_BUILD: [0,0,0,0]
        }

    def reset(self):
        self.reset_general_items()
        self.reset_for_marquise()
        self.reset_for_eyrie()
        return self.get_observation()

    def step(self, action):
        ans = []
        # check if we are resolving field hospitals
        if len(self.field_hospitals) > 0:
            # the action is say if the marquise are discarding a card or not
            foo = self.field_hospitals.pop()
            if action == AID_GENERIC_SKIP:
                logger.debug(f"The Marquise do not use Field Hospitals on the {foo[0]} warriors in the {ID_TO_SUIT[foo[1]]} Clearing")
            else:
                # they are using Field Hospitals
                self.activate_field_hospitals(foo[0],action - AID_DISCARD_CARD)
            while len(self.field_hospitals) > 0:
                suit = self.field_hospitals[-1][1]
                if self.players[PIND_MARQUISE].has_suit_in_hand(suit):
                    self.saved_actions = [AID_GENERIC_SKIP] + [c.id+AID_DISCARD_CARD for c in self.players[PIND_MARQUISE].hand if (c.suit in {suit,SUIT_BIRD})]
                    return
                else:
                    self.field_hospitals.pop()
            if self.battle.stage != Battle.STAGE_DONE:
                self.saved_actions = self.saved_battle_actions
                self.current_player = self.saved_battle_player
                return
            if self.phase in {self.PHASE_BIRDSONG_EYRIE,self.PHASE_DAYLIGHT_EYRIE,self.PHASE_EVENING_EYRIE}:
                self.current_player = -1
            else:
                self.current_player = 1
            self.saved_actions = self.advance_game()
            return

        if self.battle.stage == Battle.STAGE_DONE:
            self.resolve_action(action)
            # battle could have been started
            if self.battle.stage is None:
                self.saved_battle_actions = self.resolve_battle_action(action)
                self.saved_battle_player = self.current_player
                # check for field hospitals
                while len(self.field_hospitals) > 0:
                    suit = self.field_hospitals[-1][1]
                    if self.players[PIND_MARQUISE].has_suit_in_hand(suit):
                        self.saved_actions = [AID_GENERIC_SKIP] + [c.id+AID_DISCARD_CARD for c in self.players[PIND_MARQUISE].hand if (c.suit in {suit,SUIT_BIRD})]
                        self.current_player = 1
                        return
                    else:
                        self.field_hospitals.pop()
                ans = self.saved_battle_actions
        else:
            self.saved_battle_actions = self.resolve_battle_action(action)
            self.saved_battle_player = self.current_player
            # check for field hospitals
            while len(self.field_hospitals) > 0:
                suit = self.field_hospitals[-1][1]
                if self.players[PIND_MARQUISE].has_suit_in_hand(suit):
                    self.saved_actions = [AID_GENERIC_SKIP] + [c.id+AID_DISCARD_CARD for c in self.players[PIND_MARQUISE].hand if (c.suit in {suit,SUIT_BIRD})]
                    self.current_player = 1
                    return
                else:
                    self.field_hospitals.pop()
            ans = self.saved_battle_actions

        if bool(ans):
            self.saved_actions = ans
        else:
            self.saved_actions = self.advance_game()

        done = False

        reward = 1 if done else 0

        # return self.get_observation(), reward, done

    def get_observation(self):
        board_player1 = np.where(self.board == 1, 1.0, 0.0)
        board_player2 = np.where(self.board == -1, 1.0, 0.0)
        board_to_play = np.full((11, 11), self.current_player, dtype="int32")
        return np.array([board_player1, board_player2, board_to_play])

    def legal_actions(self):
        while self.saved_actions is None:
            self.saved_actions = self.advance_game()
        return self.saved_actions
    
    def draw_cards(self,player_index:int,amount:int):
        """
        Draws a number of cards from the top of the deck and then
        adds them to a player's hand.

        If the deck runs out, it automatically uses up the
        discard pile to refresh the deck and then continues drawing.
        """
        p = self.players[player_index]
        while amount:
            c_drawn = self.deck.draw(1)[0]
            logger.debug(f"\t{ID_TO_PLAYER[player_index]} draws {c_drawn.name}")
            p.hand.append(c_drawn)
            if self.deck.size() == 0:
                self.deck.add(self.discard_pile) # includes shuffling
                self.discard_pile = []
            amount -= 1
    
    def get_card(self,player_index:int,card_id:int,location:str) -> Card:
        "Removes and returns the card from the given location for the player. location can be 'hand' or 'persistent'."
        loc = self.players[player_index].hand if (location == 'hand') else self.players[player_index].persistent_cards
        for i,c in enumerate(loc):
            if c.id == card_id:
                logger.debug(f"\t{c.name} removed from {location} of {ID_TO_PLAYER[player_index]}")
                return loc.pop(i)
            
    def discard_from_hand(self,player_index:int,card_id:int):
        "Makes a player discard a card of the matching id from their hand, assuming they have it."
        c_to_discard = self.get_card(player_index,card_id,"hand")
        logger.debug(f"\t{c_to_discard.name} added to discard pile")
        self.discard_pile.append(c_to_discard)
    
    def discard_from_persistent(self,player_index:int,card_id:int):
        "Makes a player discard a card of the matching id from their persistent cards, assuming they have it."
        c_to_discard = self.get_card(player_index,card_id,"persistent")
        logger.debug(f"\t{c_to_discard.name} added to discard pile")
        self.discard_pile.append(c_to_discard)

    def change_score(self,player_index:int,amount:int):
        "Makes a player score some amount of points. Use a negative amount to lose points."
        p = self.victory_points[player_index]
        self.victory_points[player_index] = max(0, p + amount)
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} Points changed by {amount}")
        logger.debug(f"\t\tNew Score: {self.victory_points}")
        self.points_scored_this_turn += amount

    def craft_card(self,player_index:int,card_id:int):
        "Makes the player craft the given card, assuming the action is legal."
        p = self.players[player_index]
        for i,c in enumerate(p.hand):
            if c.id == card_id:
                card_to_craft = c
                hand_i = i
                break

        item_id = card_to_craft.crafting_item
        if item_id != ITEM_NONE:
            # we are crafting an item
            logger.debug(f"\t{ID_TO_PLAYER[player_index]} crafts {ID_TO_ITEM[item_id]}")
            self.available_items[item_id] -= 1
            p.crafted_items[item_id] += 1
            
            # Disdain for Trade for the Eyrie (unless they have Builder leader)
            points_scored = 1 if (player_index == PIND_EYRIE and p.chosen_leader_index != LEADER_BUILDER) else card_to_craft.points
            self.change_score(player_index,points_scored)
            
            self.discard_from_hand(player_index,card_id)
        elif card_to_craft.is_persistent:
            # we are crafting a persistent card
            logger.debug(f"\t{ID_TO_PLAYER[player_index]} crafts {card_to_craft.name}")
            p.persistent_cards.append(card_to_craft)
            p.hand.pop(hand_i)
        elif card_id in CID_FAVORS:
            # a favor card has been activated
            logger.debug(f"\t{ID_TO_PLAYER[player_index]} crafts {card_to_craft.name}")
            points_scored,fh_list = self.board.resolve_favor(player_index,CLEARING_SUITS[card_to_craft.suit])
            # clear out each clearing
            for cid in CLEARING_SUITS[card_to_craft.suit]:
                clearing = self.board.clearings[cid]
                for faction_i in {j for j in range(N_PLAYERS) if j != player_index}:
                    player = self.players[faction_i]
                    foo = clearing.get_num_warriors(faction_i)
                    clearing.change_num_warriors(faction_i,-foo)
                    player.change_num_warriors(foo)
                    while len(clearing.buildings[faction_i]) > 0:
                        foo = clearing.buildings[faction_i].pop()
                        player.change_num_buildings(foo,1)
                    while len(clearing.tokens[faction_i]) > 0:
                        foo = clearing.tokens[faction_i].pop()
                        player.change_num_tokens(foo,1)

            self.change_score(player_index,points_scored)
            if bool(fh_list):
                self.field_hospitals += sorted(fh_list)
            self.discard_from_hand(player_index, card_id)
        for i in range(3):
            self.remaining_craft_power[i] -= card_to_craft.crafting_recipe[i]

    def craft_royal_claim(self,player_index:int,action:int):
        "Crafts Royal Claim for the given player using a specific crafting power."
        p = self.players[player_index]
        for i,c in enumerate(p.hand):
            if c.id == CID_ROYAL_CLAIM:
                card_to_craft = c
                hand_i = i
                break
        p.persistent_cards.append(card_to_craft)
        p.hand.pop(hand_i)
        recipe_used = AID_CRAFT_RC_MAPPING[action]
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} crafts {card_to_craft.name} with recipe {recipe_used}")
        for i in range(3):
            self.remaining_craft_power[i] -= recipe_used[i]

    # BATTLE FUNCTIONS
    def keep_is_up(self):
        "Returns True only if the Marquise's Keep token is still on the map."
        mplayer = self.players[PIND_MARQUISE]
        return self.board.clearings[mplayer.keep_clearing_id].get_num_tokens(PIND_MARQUISE,TIND_KEEP) > 0

    def activate_field_hospitals(self,amount:int,payment_card_id:int):
        "Places 'amount' of warriors at the Marquise's Keep and discards the given card from their hand."
        logger.debug("\tField Hospitals activated...")
        keep_clearing = self.players[PIND_MARQUISE].keep_clearing_id
        self.board.place_warriors(PIND_MARQUISE,amount,keep_clearing)
        self.discard_from_hand(PIND_MARQUISE,payment_card_id)

    def score_battle_points(self,faction_index:int,is_attacker:bool,cardboard_removed:int):
        """
        Given the number of cardboard pieces removed, make the given faction
        score the right number of points. Accounts for the Eyrie Despot with
        extra info stored in the current Battle object.
        """
        points = cardboard_removed
        if (faction_index == PIND_EYRIE) and (self.players[faction_index].chosen_leader_index == LEADER_DESPOT) and cardboard_removed:
            # if the Eyrie with Despot are removing cardboard, score them an extra point if they haven't
            # received an extra point thus far for doing so
            if (not self.battle.att_cardboard_removed) and is_attacker:
                points += 1
                self.battle.att_cardboard_removed = True
            elif (not self.battle.def_cardboard_removed) and (not is_attacker):
                points += 1
                self.battle.def_cardboard_removed = True
        self.change_score(faction_index,points)

    def deal_hits(self,faction_index:int,amount:int,clearing_index:int):
        """
        Make the given faction take a certain number of hits in the given clearing.
        Removes warriors first, then buildings/tokens if necessary.

        Returns a 3-tuple:
        - 1. The number of hits left to deal. A positive amount means a choice must be made.
        - 2. The number of warriors killed.
        - 3. The number of pieces of cardboard removed (buildings + tokens)
        """
        target_clearing = self.board.clearings[clearing_index]
        target_faction = self.players[faction_index]
        warriors_removed = cardboard_removed = 0
        while amount > 0:
            # first take out warriors
            if target_clearing.get_num_warriors(faction_index) > 0:
                target_clearing.change_num_warriors(faction_index,-1)
                target_faction.change_num_warriors(1)
                warriors_removed += 1
                amount -= 1
            # then check if there is a choice of building / token
            elif faction_index == PIND_MARQUISE:
                # find how many choices the Marquise have of removing tokens/buildings
                building_choices = sum((target_clearing.get_num_buildings(faction_index,bid) > 0) for bid in range(3))
                token_choices = sum((target_clearing.get_num_tokens(faction_index,tid) > 0) for tid in range(2))
                # if they have a choice at all, then leave with 'amount' > 0 to indicate this
                if (building_choices + token_choices) > 1:
                    break
                # otherwise, there is no choice in what to remove
                # if it is a building, remove one of them
                elif building_choices == 1:
                    for bid in range(3):
                        if target_clearing.get_num_buildings(faction_index,bid) > 0:
                            target_clearing.remove_building(faction_index,bid)
                            target_faction.change_num_buildings(bid,1)
                            cardboard_removed += 1
                            amount -= 1
                # if it is a token, remove one of them
                elif token_choices == 1:
                    for tid in range(2):
                        if target_clearing.get_num_tokens(faction_index,tid) > 0:
                            target_clearing.remove_token(faction_index,tid)
                            target_faction.change_num_tokens(tid,1)
                            cardboard_removed += 1
                            amount -= 1
                # if no other item is present, the remaining hits are lost
                else:
                    amount = 0
            elif faction_index == PIND_EYRIE:
                # the Eyrie can only have roosts, and have no tokens
                if target_clearing.get_num_buildings(faction_index,BIND_ROOST) > 0:
                    target_clearing.remove_building(faction_index,BIND_ROOST)
                    target_faction.change_num_buildings(BIND_ROOST,1)
                    cardboard_removed += 1
                    amount -= 1
                else:
                    amount = 0
        return amount, warriors_removed, cardboard_removed

    def resolve_battle_action(self,action):
        """
        Given an action number, performs the given action given the
        current information stored about any battles currently going on.

        Assumes that self.battle points to an existing Battle object.
        """
        defender = self.players[self.battle.defender_id]
        clearing = self.board.clearings[self.battle.clearing_id]
        if self.battle.stage is None:
            # the battle just started, assume a brand new Battle object was just created
            logger.debug(f"\t--- BATTLE STARTED: {ID_TO_PLAYER[self.battle.attacker_id]} Attacks {ID_TO_PLAYER[self.battle.defender_id]} in clearing {self.battle.clearing_id}")
            ans = defender.get_ambush_actions(clearing.suit)
            if bool(ans):
                # the defender chooses to ambush or not
                self.battle.stage = Battle.STAGE_DEF_AMBUSH
                self.current_player = self.index_to_id(self.battle.defender_id)
                return ans
            # no ambush is possible, so we move straight to the dice roll
            logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} chose not to ambush")
            self.battle.stage = Battle.STAGE_DICE_ROLL

        attacker = self.players[self.battle.attacker_id]
        if self.battle.stage == Battle.STAGE_DEF_ORDER:
            logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} chose what piece to remove")
            # action is what defender building/token to hit with the next hit
            if action in {AID_ORDER_KEEP,AID_ORDER_WOOD}:
                clearing.remove_token(self.battle.defender_id,action - AID_ORDER_KEEP)
                defender.change_num_tokens(action - AID_ORDER_KEEP,1)
            else:
                clearing.remove_building(self.battle.defender_id,action - AID_ORDER_SAWMILL)
                defender.change_num_buildings(action - AID_ORDER_SAWMILL,1)
            # see if there is a choice anymore
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.defender_id, self.battle.att_hits_to_deal - 1, self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.att_hits_to_deal > 0:
                # defender still has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.defender_id)
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.defender_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.defender_id,tid) > 0)]
                return building_choices + token_choices
            
            # all hits needed have been dealt to defender
            # it is now the attacker's turn to take hits
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id, self.battle.def_hits_to_deal, self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))
            
            self.current_player = self.index_to_id(self.battle.attacker_id)
            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice on what to remove
                self.battle.stage = Battle.STAGE_ATT_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                return building_choices + token_choices
            else:
                # the battle is over
                logger.debug(f"--- BATTLE FINISHED")
                self.battle.stage = Battle.STAGE_DONE
                return []
            
        if self.battle.stage == Battle.STAGE_ATT_ORDER:
            logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} chose what piece to remove")
            # action is what attacker building/token to hit with the next hit
            if action in {AID_ORDER_KEEP,AID_ORDER_WOOD}:
                clearing.remove_token(self.battle.attacker_id,action - AID_ORDER_KEEP)
                attacker.change_num_tokens(action - AID_ORDER_KEEP,1)
            else:
                clearing.remove_building(self.battle.attacker_id,action - AID_ORDER_SAWMILL)
                attacker.change_num_buildings(action - AID_ORDER_SAWMILL,1)
            # see if there is a choice anymore
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id, self.battle.def_hits_to_deal - 1, self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))
            
            self.current_player = self.index_to_id(self.battle.attacker_id)
            if self.battle.def_hits_to_deal > 0:
                # attacker still has a choice of what to remove
                self.battle.stage = Battle.STAGE_ATT_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                return building_choices + token_choices
            
            # All hits have been dealt, so we are in one of two possible situations:
            # 1. The dice have not been rolled. If the -attacker- is choosing buildings to destroy,
            #    then that means they attacked with 1 warrior and were ambushed, and now had to
            #    choose one of their buildings to remove. They have no warriors and the battle is over.
            # 2. The dice have been rolled and extra effects have been chosen. However, the attacker is
            #    last to pick which things get hit in what order, so the battle must be over.
            logger.debug(f"--- BATTLE FINISHED")
            self.battle.stage = Battle.STAGE_DONE
            return []
        
        if self.battle.stage == Battle.STAGE_DEF_AMBUSH:
            # action is the defender's choice to ambush or not
            if action == AID_AMBUSH_NONE:
                logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} chose not to ambush")
                # we immediately go to the dice roll
                self.battle.stage = Battle.STAGE_DICE_ROLL
            else:
                # save which ambush card is played
                logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} chooses to AMBUSH!")
                if action == AID_AMBUSH_BIRD:
                    self.battle.def_ambush_id = CID_AMBUSH_BIRD
                elif action == AID_AMBUSH_MOUSE:
                    self.battle.def_ambush_id = CID_AMBUSH_MOUSE
                elif action == AID_AMBUSH_RABBIT:
                    self.battle.def_ambush_id = CID_AMBUSH_RABBIT
                elif action == AID_AMBUSH_FOX:
                    self.battle.def_ambush_id = CID_AMBUSH_FOX
                # make the defender discard this card
                self.discard_from_hand(self.battle.defender_id,self.battle.def_ambush_id)

                # check if the attacker has Scouting Party (nullifies ambush cards used up)
                if any((c.id == CID_SCOUTING_PARTY) for c in attacker.hand):
                    logger.debug("The ambush is thwarted by a Scouting Party!")
                    self.battle.stage = Battle.STAGE_DICE_ROLL
                # otherwise, see if attacker can choose to counter ambush
                ans = attacker.get_ambush_actions(clearing.suit)
                if bool(ans):
                    self.battle.stage = Battle.STAGE_ATT_AMBUSH
                    self.current_player = self.index_to_id(self.battle.attacker_id)
                    return ans
                # otherwise, the ambush triggers and 2 hits are dealt
                logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} chose not to counter-ambush")
                self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id, 2, self.battle.clearing_id)
                if cardboard_removed:
                    self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
                if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                    self.field_hospitals.append((warriors_killed,clearing.suit))

                # check if a choice must be made from hits
                if self.battle.def_hits_to_deal > 0:
                    self.current_player = self.index_to_id(self.battle.attacker_id)
                    self.battle.stage = Battle.STAGE_ATT_ORDER
                    building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                    token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                    return building_choices + token_choices
                # if the hits are all dealt, we check if a battle can still occur
                elif clearing.get_num_warriors(self.battle.attacker_id) > 0:
                    logger.debug("Continuing to the dice roll...")
                    self.battle.stage = Battle.STAGE_DICE_ROLL
                # otherwise, the ambush wiped out all attackers
                else:
                    logger.debug("Ouch, should have brought more backup...")
                    logger.debug(f"--- BATTLE FINISHED")
                    self.battle.stage = Battle.STAGE_DONE
                    self.current_player = self.index_to_id(self.battle.attacker_id)
                    return []

        if self.battle.stage == Battle.STAGE_ATT_AMBUSH:
            # action is the attacker's choice to counter ambush or not
            if action == AID_AMBUSH_NONE:
                logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} chose not to counter-ambush")
                # the ambush triggers and 2 hits are dealt
                # deal_hits returns the number of remaining hits there are; if >0, it means a choice is possible for the one getting hit
                self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id, 2, self.battle.clearing_id)
                if cardboard_removed:
                    self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
                if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                    self.field_hospitals.append((warriors_killed,clearing.suit))

                # check if a choice must be made from hits
                if self.battle.def_hits_to_deal > 0:
                    self.current_player = self.index_to_id(self.battle.attacker_id)
                    self.battle.stage = Battle.STAGE_ATT_ORDER
                    building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                    token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                    return building_choices + token_choices
                # if the hits are all dealt, we check if a battle can still occur
                elif clearing.get_num_warriors(self.battle.attacker_id) > 0:
                    logger.debug("Continuing to the dice roll...")
                    self.battle.stage = Battle.STAGE_DICE_ROLL
                # otherwise, the ambush wiped out all attackers
                else:
                    logger.debug("Ouch, should have brought more backup...")
                    logger.debug(f"--- BATTLE FINISHED")
                    self.battle.stage = Battle.STAGE_DONE
                    self.current_player = self.index_to_id(self.battle.attacker_id)
                    return []
            else:
                # save which ambush card is played
                logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} chooses to COUNTER-AMBUSH!")
                if action == AID_AMBUSH_BIRD:
                    self.battle.att_ambush_id = CID_AMBUSH_BIRD
                elif action == AID_AMBUSH_MOUSE:
                    self.battle.att_ambush_id = CID_AMBUSH_MOUSE
                elif action == AID_AMBUSH_RABBIT:
                    self.battle.att_ambush_id = CID_AMBUSH_RABBIT
                elif action == AID_AMBUSH_FOX:
                    self.battle.att_ambush_id = CID_AMBUSH_FOX
                # make the attacker discard this card
                self.discard_from_hand(self.battle.attacker_id,self.battle.att_ambush_id)
                # we immediately go to the dice roll, since the defender's ambush is cancelled
                logger.debug("Continuing to the dice roll...")
                self.battle.stage = Battle.STAGE_DICE_ROLL

        if self.battle.stage == Battle.STAGE_DICE_ROLL:
            # the dice must be rolled before continuing
            roll = [random.randint(0,3) for i in range(2)]
            logger.debug(f"--- DICE ROLL: {roll}")
            self.battle.att_rolled_hits = min(clearing.get_num_warriors(self.battle.attacker_id), max(roll))
            self.battle.def_rolled_hits = min(clearing.get_num_warriors(self.battle.defender_id), min(roll))
            # defenseless
            if clearing.get_num_warriors(self.battle.defender_id) == 0:
                logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} is defenseless (+1 hit taken)")
                self.battle.att_extra_hits += 1
            # Eyrie Commander Leader
            if (self.battle.attacker_id == PIND_EYRIE) and (attacker.chosen_leader_index == LEADER_COMMANDER):
                logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} is led by the Commander (+1 hit dealt)")
                self.battle.att_extra_hits += 1

            # check if the attacker can choose extra effects
            ans = attacker.get_attacker_card_actions()
            if bool(ans):
                self.current_player = self.index_to_id(self.battle.attacker_id)
                self.battle.stage = Battle.STAGE_ATT_EFFECTS
                return ans
            # check if the defender can choose extra effects
            ans = defender.get_defender_card_actions()
            if bool(ans):
                self.current_player = self.index_to_id(self.battle.defender_id)
                self.battle.stage = Battle.STAGE_DEF_EFFECTS
                return ans
            
            # no extra effects can be chosen, so deal the hits next
            # next, the defender takes hits first
            logger.debug("--- Dealing hits to defender...")
            self.battle.def_hits_to_deal = self.battle.def_rolled_hits
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.defender_id)
                self.battle.stage = Battle.STAGE_DEF_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.defender_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.defender_id,tid) > 0)]
                return building_choices + token_choices
            # lastly, attacker takes hits
            logger.debug("--- Dealing hits to attacker...")
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id,self.battle.def_hits_to_deal,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.attacker_id)
                self.battle.stage = Battle.STAGE_ATT_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                return building_choices + token_choices
            # battle is over
            logger.debug(f"--- BATTLE FINISHED")
            self.battle.stage = Battle.STAGE_DONE
            self.current_player = self.index_to_id(self.battle.attacker_id)
            return []
        
        if self.battle.stage == Battle.STAGE_ATT_EFFECTS:
            # the attacker has chosen what extra effects to use
            if action in {AID_EFFECTS_ARMORERS,AID_EFFECTS_ARM_BT}:
                # Armorers is used up
                logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} activates Armorers (ignores rolled hits)")
                self.battle.def_rolled_hits = 0
                self.discard_from_persistent(self.battle.attacker_id,CID_ARMORERS)
            if action in {AID_EFFECTS_BRUTTACT,AID_EFFECTS_ARM_BT}:
                # brutal tactics is used
                logger.debug(f"{ID_TO_PLAYER[self.battle.attacker_id]} activates Brutal Tactics (+1 hit dealt)")
                self.battle.att_extra_hits += 1
                self.change_score(self.battle.defender_id,1)
            # check if the defender can choose extra effects
            ans = defender.get_defender_card_actions()
            if bool(ans):
                self.current_player = self.index_to_id(self.battle.defender_id)
                self.battle.stage = Battle.STAGE_DEF_EFFECTS
                return ans
            
            # next, the defender takes hits first
            logger.debug("--- Dealing hits to defender...")
            self.battle.def_hits_to_deal = self.battle.def_rolled_hits
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.defender_id)
                self.battle.stage = Battle.STAGE_DEF_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.defender_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.defender_id,tid) > 0)]
                return building_choices + token_choices
            # lastly, attacker takes hits
            logger.debug("--- Dealing hits to attacker...")
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id,self.battle.def_hits_to_deal,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.attacker_id)
                self.battle.stage = Battle.STAGE_ATT_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                return building_choices + token_choices
            # battle is over
            logger.debug(f"--- BATTLE FINISHED")
            self.battle.stage = Battle.STAGE_DONE
            self.current_player = self.index_to_id(self.battle.attacker_id)
            return []
        
        if self.battle.stage == Battle.STAGE_DEF_EFFECTS:
            # the defender has chosen what extra effects to use
            if action in {AID_EFFECTS_ARMORERS,AID_EFFECTS_ARMSAP}:
                # Armorers is used up
                logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} activates Armorers (ignores rolled hits)")
                self.battle.att_rolled_hits = 0
                self.discard_from_persistent(self.battle.defender_id,CID_ARMORERS)
            if action in {AID_EFFECTS_SAPPERS,AID_EFFECTS_ARMSAP}:
                # sappers is used
                logger.debug(f"{ID_TO_PLAYER[self.battle.defender_id]} activates Sappers (+1 hit dealt)")
                self.battle.def_extra_hits += 1
                self.discard_from_persistent(self.battle.defender_id,CID_SAPPERS)
            # next, the defender takes hits first
            logger.debug("--- Dealing hits to defender...")
            self.battle.def_hits_to_deal = self.battle.def_rolled_hits + self.battle.def_extra_hits
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.defender_id)
                self.battle.stage = Battle.STAGE_DEF_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.defender_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.defender_id,tid) > 0)]
                return building_choices + token_choices
            # lastly, attacker takes hits
            logger.debug("--- Dealing hits to attacker...")
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.deal_hits(self.battle.attacker_id,self.battle.def_hits_to_deal,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.field_hospitals.append((warriors_killed,clearing.suit))

            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice of what to remove
                self.current_player = self.index_to_id(self.battle.attacker_id)
                self.battle.stage = Battle.STAGE_ATT_ORDER
                building_choices = [bid+AID_ORDER_SAWMILL for bid in range(3) if (clearing.get_num_buildings(self.battle.attacker_id,bid) > 0)]
                token_choices = [tid+AID_ORDER_KEEP for tid in range(2) if (clearing.get_num_tokens(self.battle.attacker_id,tid) > 0)]
                return building_choices + token_choices
            # battle is over
            logger.debug(f"--- BATTLE FINISHED")
            self.battle.stage = Battle.STAGE_DONE
            self.current_player = self.index_to_id(self.battle.attacker_id)
            return []


    # Activating Card Effects
    def activate_royal_claim(self,player_index:int):
        "In Birdsong, may discard this to score one point per clearing you rule."
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} activates Royal Claim...")
        points = sum((i == player_index) for i in self.board.get_rulers())
        self.change_score(player_index,points)
        self.discard_from_persistent(player_index, CID_ROYAL_CLAIM)
    
    def activate_stand_and_deliver(self,player_index:int,target_index:int):
        "In Birdsong, may take a random card from another player. That player scores one point."
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} activates Stand and Deliver on {ID_TO_PLAYER[target_index]}...")
        target_p_hand = self.players[target_index].hand
        chosen_i = random.randint(0,len(target_p_hand) - 1)
        chosen_card = target_p_hand.pop(chosen_i)
        logger.debug(f"\t\tCard Taken: {chosen_card.name}")

        self.players[player_index].hand.append(chosen_card)
        self.change_score(target_index,1)

    def activate_tax_collector(self,player_index:int,clearing_index:int):
        "Once in Daylight, may remove one of your warriors from the map to draw a card."
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} activates Tax Collector...")
        self.board.place_warriors(player_index,-1,clearing_index)
        self.draw_cards(player_index,1)
        self.field_hospitals.append((1,self.board.clearings[clearing_index].suit))

    def activate_better_burrow(self,player_index:int,target_index:int):
        "At start of Birdsong, you and another player draw a card."
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} activates Better Burrow Bank...")
        self.draw_cards(player_index,1)
        self.draw_cards(target_index,1)
    
    def activate_codebreakers(self,player_index:int,target_index:int):
        "TODO: Implement"
        logger.debug(f"\t{ID_TO_PLAYER[player_index]} activates Codebreakers...")
        

    def can_craft(self,card:Card,player:Player):
        "Returns True only if the current player can currently craft the given card. Checks the remaining crafting power."
        r = card.crafting_recipe
        if max(r) == 0:
            return False # card cannot be crafted at all
        if card.is_persistent and card.id in {c.id for c in player.persistent_cards}:
            return False # we already have this card crafted
        if card.crafting_item != ITEM_NONE and self.available_items[card.crafting_item] == 0:
            return False # enough of this item has been crafted already
        
        wild = r[3]
        if wild > 0:
            # wildcards can use any crafting power
            return sum(self.remaining_craft_power) >= wild
        for i in range(3):
            if r[i] > self.remaining_craft_power[i]:
                return False # not enough crafting power left
        return True
    
    def get_craftable_ids(self,player:Player):
        "Returns a list of every card ID that the given player can currently craft, given the remaining crafting power."
        return [c.id for c in player.hand if self.can_craft(c,player)]

    def get_royal_claim_craft_ids(self):
        """
        Returns a list of integers: each is the Action ID of a valid way
        that Royal Claim can be crafted with the current remaining crafting power.
        """
        ans = []
        for aid,recipe in AID_CRAFT_RC_MAPPING.items():
            if all(self.remaining_craft_power[i] >= recipe[i] for i in range(3)):
                ans.append(aid)
        return ans

    def place_marquise_wood(self,mplayer:Marquise):
        """
        Places 1 wood token at each Sawmill, unless there is not enough wood.

        Returns True only if all of the wood could be automatically placed, False otherwise.
        """
        sawmill_counts = self.board.get_total_building_counts(PIND_MARQUISE,BIND_SAWMILL)
        wood_in_store = mplayer.get_num_tokens_in_store(TIND_WOOD)
        if wood_in_store == 0 or sum(sawmill_counts) == 0:
            logger.debug("\tNo wood to be placed / No sawmills to generate wood at")
            return True
        # there is at least 1 wood and at least 1 sawmill to place at
        if sum(sawmill_counts) > wood_in_store:
            self.available_wood_spots = sawmill_counts
            return False
        # place a wood token for each sawmill at each clearing with a sawmill
        logger.debug("\tWood can be placed automatically...")
        clearings_with_sawmill_ids = {i for i,n in enumerate(sawmill_counts) if n > 0}
        for i in clearings_with_sawmill_ids:
            n_sawmills = sawmill_counts[i]
            while n_sawmills:
                mplayer.change_num_tokens(TIND_WOOD, -1)
                self.board.place_token(PIND_MARQUISE,TIND_WOOD,i)
                n_sawmills -= 1
        return True

    def place_marquise_warriors(self,mplayer:Marquise):
        """
        Places 1 Marquise warrior at each Recruiter, unless there is not enough warriors in store.

        Returns True only if all of the warriors could be automatically placed, False otherwise.
        """
        recruiter_counts = self.board.get_total_building_counts(PIND_MARQUISE,BIND_RECRUITER)
        if sum(recruiter_counts) > mplayer.warrior_storage:
            self.available_recruiters = recruiter_counts
            return False
        # place a warrior for each recruiter at each clearing with a recruiter
        logger.debug("\tWarriors can be recruited automatically...")
        clearings_with_recruiter_ids = {i for i,n in enumerate(recruiter_counts) if n > 0}
        for i in clearings_with_recruiter_ids:
            n_recruiters = recruiter_counts[i]
            mplayer.change_num_warriors(-n_recruiters)
            self.board.place_warriors(PIND_MARQUISE,n_recruiters,i)
        return True
    
    def place_marquise_building(self,mplayer:Marquise,building_index:int,clearing_index:int):
        """
        Tries to automatically place the given building in the given clearing. Assumes that
        there is an open building slot, that the Marquise player can build this building,
        that there is enough connected wood, etc. Places the given building / adjusts points
        and everything automatically before checking wood.

        Returns True only if there was no choice in where to spend wood:
        - All the wood connected would have to be spent
        - All the available wood is in only one clearing
        """
        # place the building
        wood_cost,points_scored = mplayer.update_from_building_placed(building_index)
        self.board.place_building(PIND_MARQUISE,building_index,clearing_index)
        self.change_score(PIND_MARQUISE,points_scored)

        usable_wood = self.board.get_wood_to_build_in(clearing_index)
        one_clearing_id = -1
        total_usable = 0
        for i,amount in enumerate(usable_wood):
            if amount > 0:
                total_usable += amount
                if one_clearing_id == -1:
                    one_clearing_id = i
                else:
                    one_clearing_id = None
        # if there is only one clearing with wood, just take the cost from that clearing
        if one_clearing_id is not None:
            logger.debug(f"\tRemoving wood cost solely from clearing {one_clearing_id}...")
            for i in range(wood_cost):
                self.board.clearings[one_clearing_id].remove_token(PIND_MARQUISE,TIND_WOOD)
            mplayer.change_num_tokens(TIND_WOOD,wood_cost)
            return True
        # if we have exactly enough wood to pay, then use up all of the usable wood
        if total_usable == wood_cost:
            logger.debug(f"\tRemoving all usable wood to pay...")
            for i,amount in enumerate(usable_wood):
                while amount > 0:
                    self.board.clearings[i].remove_token(PIND_MARQUISE,TIND_WOOD)
                    amount -= 1
            mplayer.change_num_tokens(TIND_WOOD,wood_cost)
            return True
        # wood is in more than 1 clearing and we have too much, so
        # we have to choose where to take it from
        self.available_wood_spots = usable_wood
        self.remaining_wood_cost = wood_cost
        return False
    
    def get_marquise_building_actions(self,mplayer:Marquise):
        """
        Finds all of the AID's for building each building for the Marquise.
        Returns a list of integers. 
        """
        ans = []
        usable_wood_per_clearing = self.board.get_wood_available()
        empty_slots = self.board.get_empty_building_slot_counts()
        ids = [(BIND_SAWMILL,AID_BUILD1),(BIND_WORKSHOP,AID_BUILD2),(BIND_RECRUITER,AID_BUILD3)]
        for bid,aid in ids:
            n_left_to_build = mplayer.get_num_buildings_on_track(bid)
            if n_left_to_build > 0:
                building_cost = mplayer.building_costs[6 - n_left_to_build]
                ans += [aid+i for i,amount in enumerate(usable_wood_per_clearing) if (amount >= building_cost and empty_slots[i] > 0)]
        return ans
    
    def get_marquise_overwork_actions(self,mplayer:Marquise):
        "Returns a list of integers: All the Overwork AID's for the Marquise."
        ans = []
        seen = set()
        sawmill_clearings = [i for i,count in enumerate(self.board.get_total_building_counts(PIND_MARQUISE,BIND_SAWMILL)) if (count > 0)]
        for card in mplayer.hand:
            if card.id not in seen:
                seen.add(card.id)
                for i in sawmill_clearings:
                    clearing = self.board.clearings[i]
                    if (card.suit == SUIT_BIRD) or (clearing.suit == card.suit):
                        ans.append(AID_OVERWORK + i + card.id*12)
        return ans
    
    def reduce_decree_count(self,decree_index:int,suit:int):
        """
        Marks a certain required action on the current decree as completed
        by subtracting one from the counter, given the suit of the clearing.

        Prioritizes the exact suit before counting an action as a bird action.
        """
        if self.remaining_decree[decree_index][suit] > 0:
            logger.debug(f"\tFulfilled {ID_TO_SUIT[suit]} {ID_TO_DECREE[decree_index]} requirement on Decree")
            self.remaining_decree[decree_index][suit] -= 1
        else:
            logger.debug(f"\tFulfilled Bird {ID_TO_DECREE[decree_index]} requirement on Decree")
            self.remaining_decree[decree_index][SUIT_BIRD] -= 1
    
    def setup_decree_counter(self,eplayer:Eyrie):
        "Sets up the self.remaining_decree object given the eplayer's decree."
        logger.debug("\tTallying required decree...")
        for decree_index,card_list in eplayer.decree.items():
            for card in card_list:
                self.remaining_decree[decree_index][card.suit] += 1

    def get_eyrie_decree_add_actions(self,eplayer:Eyrie):
        "Returns a list of int: All of the legal Add to Decree AID's for the Eyrie."
        ans = []
        ids = [AID_DECREE_RECRUIT,AID_DECREE_MOVE,AID_DECREE_BATTLE,AID_DECREE_BUILD]
        for card in eplayer.hand:
            if (card.suit == SUIT_BIRD) and (self.eyrie_bird_added == 1):
                continue
            ans += [i+card.id for i in ids]
        return ans

    def get_decree_resolving_actions(self,eplayer:Eyrie):
        """
        Assuming that there are still actions to do in the decree, finds all
        of the AID's that will help resolve the current step in the decree, if
        any are currently possible. 
        """
        ans = []
        valid_suits = set()
        if sum(self.remaining_decree[DECREE_RECRUIT]) > 0:
            if eplayer.warrior_storage == 0:
                return ans
            remaining = self.remaining_decree[DECREE_RECRUIT]
            if remaining[SUIT_BIRD] > 0:
                valid_suits = {SUIT_MOUSE,SUIT_RABBIT,SUIT_FOX}
            else:
                for i in range(3):
                    if remaining[i] > 0:
                        valid_suits.add(i)
            roost_clearing_indices = [i for i,count in enumerate(self.board.get_total_building_counts(PIND_EYRIE,BIND_ROOST)) if (count > 0)]
            for i in roost_clearing_indices:
                if self.board.clearings[i].suit in valid_suits:
                    ans.append(i + AID_CHOOSE_CLEARING)
        elif sum(self.remaining_decree[DECREE_MOVE]) > 0:
            remaining = self.remaining_decree[DECREE_MOVE]
            if remaining[SUIT_BIRD] > 0:
                valid_suits = {SUIT_MOUSE,SUIT_RABBIT,SUIT_FOX}
            else:
                for i in range(3):
                    if remaining[i] > 0:
                        valid_suits.add(i)
            ans += self.board.get_legal_move_actions(PIND_EYRIE,valid_suits)
        elif sum(self.remaining_decree[DECREE_BATTLE]) > 0:
            remaining = self.remaining_decree[DECREE_BATTLE]
            if remaining[SUIT_BIRD] > 0:
                valid_suits = {SUIT_MOUSE,SUIT_RABBIT,SUIT_FOX}
            else:
                for i in range(3):
                    if remaining[i] > 0:
                        valid_suits.add(i)
            possible_battle_clearings = [i for i,x in enumerate(self.board.get_possible_battles(PIND_EYRIE,PIND_MARQUISE)) if x]
            for i in possible_battle_clearings:
                if self.board.clearings[i].suit in valid_suits:
                    ans.append(i + AID_BATTLE)
        elif sum(self.remaining_decree[DECREE_BUILD]) > 0:
            remaining = self.remaining_decree[DECREE_BUILD]
            if remaining[SUIT_BIRD] > 0:
                valid_suits = {SUIT_MOUSE,SUIT_RABBIT,SUIT_FOX}
            else:
                for i in range(3):
                    if remaining[i] > 0:
                        valid_suits.add(i)
            for i in range(12):
                c = self.board.clearings[i]
                if (c.suit in valid_suits) and (c.is_ruler(PIND_EYRIE)) and (c.get_num_buildings(PIND_EYRIE,BIND_ROOST) == 0):
                    ans.append(i + AID_BUILD1)
        return ans

    # GAME ADVANCEMENT
    def advance_game(self):
        """
        Assumes that an action has just been resolved, and advances the game
        to the next required choice, skipping over steps / stages where
        there is no choice (as much as possible).
        """
        if self.phase == self.PHASE_SETUP_MARQUISE:
            if self.phase_steps == 0:
                logger.debug(f"\t\t--- GAME START ---\nStart Player: {ID_TO_PLAYER[0 if (self.first_player == 1) else 1]}")
                return [i+AID_CHOOSE_CLEARING for i,x in enumerate(self.board.clearings) if (x.opposite_corner_id >= 0)]
            if self.phase_steps == 1:
                i = self.players[PIND_MARQUISE].keep_clearing_id
                starting_clearing = self.board.clearings[i]
                self.starting_build_spots = list(starting_clearing.adjacent_clearing_ids) + [i]
                return [x + AID_BUILD1 for x in self.starting_build_spots]
            if self.phase_steps == 2:
                return [x + AID_BUILD2 for x in self.starting_build_spots if (self.board.clearings[x].get_num_empty_slots() > 0)]
            if self.phase_steps == 3:
                return [x + AID_BUILD3 for x in self.starting_build_spots if (self.board.clearings[x].get_num_empty_slots() > 0)]
            if self.phase_steps == 4:
                self.phase = self.PHASE_SETUP_EYRIE
                self.phase_steps = 0
                self.current_player = -1
                return [x for x in range(AID_CHOOSE_LEADER,AID_CHOOSE_LEADER + 4)]
        if self.phase == self.PHASE_SETUP_EYRIE and self.phase_steps == 1:
            # START GAME - Random Starting Player?
            self.phase_steps = 0
            if self.first_player == 1: # Marquise start
                self.phase = self.PHASE_BIRDSONG_MARQUISE
                self.current_player = 1
            else: # Eyrie start
                self.phase = self.PHASE_BIRDSONG_EYRIE
                self.current_player = -1

        current_player_index = self.to_play()
        if current_player_index == PIND_MARQUISE:
            return self.advance_marquise(self.players[current_player_index])
        elif current_player_index == PIND_EYRIE:
            return self.advance_eyrie(self.players[current_player_index])
    
    def advance_marquise(self,current_player:Marquise):
        "Advances the game assuming we are in the middle of the Marquise's turn."
        if self.phase == self.PHASE_BIRDSONG_MARQUISE:
            if self.phase_steps == 0: # Start of Birdsong
                self.reset_for_marquise()
                # can they use BBB?
                if CID_BBB in {c.id for c in current_player.persistent_cards}:
                    return [AID_GENERIC_SKIP,AID_CARD_BBB]
                self.phase_steps = 1
            if self.phase_steps == 1:
                if not self.wood_placement_started:
                    self.wood_placement_started = True
                    wood_placement_done = self.place_marquise_wood(current_player)
                    if not wood_placement_done:
                        return [i+AID_CHOOSE_CLEARING for i,count in enumerate(self.available_wood_spots) if (count > 0)]
                    # we are finished placing wood
                    self.phase_steps = 2
                else:
                    # we are not finished placing wood
                    # and we still have a choice of placement
                    return [i+AID_CHOOSE_CLEARING for i,count in enumerate(self.available_wood_spots) if (count > 0)]
            if self.phase_steps == 2:
                # can they use Royal Claim or Stand/Deliver?
                unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                ans = []
                if CID_STAND_AND_DELIVER in unused_pers:
                    ans.append(AID_CARD_STAND_DELIVER)
                if CID_ROYAL_CLAIM in unused_pers:
                    ans.append(AID_CARD_ROYAL_CLAIM)
                if bool(ans):
                    return [AID_GENERIC_SKIP] + ans
                self.phase_steps = 3
            if self.phase_steps == 3:
                self.phase_steps = 0
                self.phase = self.PHASE_DAYLIGHT_MARQUISE
                
        if self.phase == self.PHASE_DAYLIGHT_MARQUISE:
            if self.phase_steps == 0:
                # can they use Command Warren?
                if CID_COMMAND_WARREN in {c.id for c in current_player.persistent_cards}:
                    foo = self.board.get_possible_battles(PIND_MARQUISE,PIND_EYRIE)
                    if bool(foo):
                        return [AID_GENERIC_SKIP] + [i+AID_CARD_COMMAND_WARREN for i,x in enumerate(foo) if x]
                self.phase_steps = 1
            if self.phase_steps == 1:
                if len(self.remaining_craft_power) == 1:
                    self.remaining_craft_power = self.board.get_crafting_power(PIND_MARQUISE)
                ans = [i+AID_CRAFT_CARD for i in self.get_craftable_ids(current_player)]
                if (CID_ROYAL_CLAIM+AID_CRAFT_CARD) in ans:
                    # find all ways to craft royal claim
                    ans.remove(CID_ROYAL_CLAIM+AID_CRAFT_CARD)
                    ans += self.get_royal_claim_craft_ids()
                if bool(ans):
                    unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                    if CID_CODEBREAKERS in unused_pers:
                        ans.append(AID_CARD_CODEBREAKERS)
                    if CID_TAX_COLLECTOR in unused_pers:
                        foo = self.board.get_num_warriors(PIND_MARQUISE)
                        ans += [i+AID_CARD_TAX_COLLECTOR for i,amount in enumerate(foo) if (amount > 0)]
                    return [AID_GENERIC_SKIP] + ans
                else:
                    # no crafting possible, so move onto the main phase
                    self.phase_steps = 2
            while self.phase_steps < 6:
                if self.phase_steps == 2:
                    ans = []
                    # check for persistent cards to use
                    unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                    if CID_CODEBREAKERS in unused_pers:
                        ans.append(AID_CARD_CODEBREAKERS)
                    if CID_TAX_COLLECTOR in unused_pers:
                        foo = self.board.get_num_warriors(PIND_MARQUISE)
                        ans += [i+AID_CARD_TAX_COLLECTOR for i,amount in enumerate(foo) if (amount > 0)]
                    # check for spending bird cards
                    seen = set()
                    for c in current_player.hand:
                        if (c.suit == SUIT_BIRD) and (c.id not in seen):
                            ans.append(BIRD_ID_TO_ACTION[c.id])
                            seen.add(c.id)
                    # standard actions
                    if self.marquise_actions > 0:
                        # starting a battle
                        foo = self.board.get_possible_battles(PIND_MARQUISE,PIND_EYRIE)
                        ans += [i+AID_BATTLE for i,x in enumerate(foo) if x]
                        # starting a march
                        ans += self.board.get_legal_move_actions(PIND_MARQUISE,{0,1,2})
                        # recruiting
                        if (not self.recruited_this_turn) and (current_player.warrior_storage > 0) and (current_player.get_num_buildings_on_track(BIND_RECRUITER) < 6):
                            ans.append(AID_RECRUIT)
                        # building
                        ans += self.get_marquise_building_actions(current_player)
                        # overworking
                        ans += self.get_marquise_overwork_actions(current_player)
                    if bool(ans):
                        return [AID_GENERIC_SKIP] + ans
                    # if we get here, then we are done with the daylight phase
                    self.phase_steps = 6
                if self.phase_steps == 3: # we are mid-march
                    ans = self.board.get_legal_move_actions(PIND_MARQUISE,{0,1,2})
                    if not bool(ans):
                        self.marquise_moves = 2
                        self.phase_steps = 2
                    else:
                        return [AID_GENERIC_SKIP] + ans
                if self.phase_steps == 4: # choosing where to recruit
                    return [i+AID_CHOOSE_CLEARING for i,count in enumerate(self.available_recruiters) if (count > 0)]
                if self.phase_steps == 5:
                    return [i+AID_CHOOSE_CLEARING for i,count in enumerate(self.available_wood_spots) if (count > 0)]
            if self.phase_steps == 6:
                self.phase_steps = 0
                self.phase = self.PHASE_EVENING_MARQUISE
        if self.phase == self.PHASE_EVENING_MARQUISE:
            if self.phase_steps == 0:
                unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                if CID_COBBLER in unused_pers:
                    ans = self.board.get_legal_move_actions(PIND_MARQUISE,{0,1,2})
                    if bool(ans):
                        return [AID_GENERIC_SKIP] + ans
                self.phase_steps = 1
            # Evening Phase
            if self.phase_steps == 1:
                self.draw_cards(PIND_MARQUISE,current_player.get_num_cards_to_draw())
                self.phase_steps = 2
            if self.phase_steps == 2 and len(current_player.hand) > 5:
                ans = {c.id+AID_DISCARD_CARD for c in current_player.hand}
                return list(ans)
            # turn done!
            self.phase_steps = 0
            self.phase = self.PHASE_BIRDSONG_EYRIE
            self.current_player = -1
            return self.advance_eyrie(self.players[PIND_EYRIE])
    
    def advance_eyrie(self,current_player:Eyrie):
        "Advances the game assuming we are in the middle of the Eyrie's turn."
        if self.phase == self.PHASE_BIRDSONG_EYRIE:
            if self.phase_steps == 0: # Start of Birdsong
                self.reset_for_eyrie()
                # can they use BBB?
                if CID_BBB in {c.id for c in current_player.persistent_cards}:
                    return [AID_GENERIC_SKIP,AID_CARD_BBB]
                self.phase_steps = 1
            if self.phase_steps == 1: # drawing emergency card
                if len(current_player.hand) == 0:
                    self.draw_cards(PIND_EYRIE,1)
                self.phase_steps = 2
            if self.phase_steps == 2: # adding to decree
                unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                ans = []
                if CID_STAND_AND_DELIVER in unused_pers:
                    ans.append(AID_CARD_STAND_DELIVER)
                if CID_ROYAL_CLAIM in unused_pers:
                    ans.append(AID_CARD_ROYAL_CLAIM)
                ans += self.get_eyrie_decree_add_actions(current_player)
                if not bool(ans):
                    self.phase_steps = 3
                elif self.eyrie_cards_added > 0:
                    return [AID_GENERIC_SKIP] + ans
                else:
                    return ans
            if self.phase_steps == 3:
                # setup decree to complete
                self.setup_decree_counter(current_player)
                # a new roost (no roosts on map)
                if current_player.get_num_buildings_on_track(BIND_ROOST) == 7:
                    total_warriors = [self.board.get_num_warriors(PIND_MARQUISE)[i] + self.board.get_num_warriors(PIND_EYRIE)[i] for i in range(12)]
                    ans = [i+AID_BUILD1 for i,count in enumerate(total_warriors) if (count == min(total_warriors))]
                    if len(ans) == 1:
                        # automatically place the roost
                        current_player.place_roost()
                        self.board.place_building(PIND_EYRIE, BIND_ROOST, ans[0] - AID_BUILD1)
                        n_warriors = min(3,current_player.warrior_storage)
                        self.board.place_warriors(PIND_EYRIE, n_warriors, ans[0] - AID_BUILD1)
                        current_player.change_num_warriors(-n_warriors)
                    else:
                        return ans
                self.phase_steps = 4
            if self.phase_steps == 4:
                # can they use Royal Claim or Stand/Deliver?
                unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                ans = []
                if CID_STAND_AND_DELIVER in unused_pers:
                    ans.append(AID_CARD_STAND_DELIVER)
                if CID_ROYAL_CLAIM in unused_pers:
                    ans.append(AID_CARD_ROYAL_CLAIM)
                if bool(ans):
                    return [AID_GENERIC_SKIP] + ans
                self.phase_steps = 5
            if self.phase_steps == 5:
                self.phase_steps = 0
                self.phase = self.PHASE_DAYLIGHT_EYRIE
        if self.phase == self.PHASE_DAYLIGHT_EYRIE:
            if self.phase_steps == 0:
                # can they use Command Warren?
                if CID_COMMAND_WARREN in {c.id for c in current_player.persistent_cards}:
                    foo = self.board.get_possible_battles(PIND_EYRIE,PIND_MARQUISE)
                    if bool(foo):
                        return [AID_GENERIC_SKIP] + [i+AID_CARD_COMMAND_WARREN for i,x in enumerate(foo) if x]
                self.phase_steps = 1
            if self.phase_steps == 1:
                if len(self.remaining_craft_power) == 1:
                    self.remaining_craft_power = self.board.get_crafting_power(PIND_EYRIE)
                ans = [i+AID_CRAFT_CARD for i in self.get_craftable_ids(current_player)]
                if (CID_ROYAL_CLAIM+AID_CRAFT_CARD) in ans:
                    # find all ways to craft royal claim
                    ans.remove(CID_ROYAL_CLAIM+AID_CRAFT_CARD)
                    ans += self.get_royal_claim_craft_ids()
                if bool(ans):
                    unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                    if CID_CODEBREAKERS in unused_pers:
                        ans.append(AID_CARD_CODEBREAKERS)
                    if CID_TAX_COLLECTOR in unused_pers:
                        foo = self.board.get_num_warriors(PIND_EYRIE)
                        ans += [i+AID_CARD_TAX_COLLECTOR for i,amount in enumerate(foo) if (amount > 0)]
                    return [AID_GENERIC_SKIP] + ans
                else:
                    # no crafting possible, so move onto resolving the decree
                    self.phase_steps = 2
            if self.phase_steps == 2:
                # RESOLVING THE DECREE
                ans = []
                # check for persistent cards to use
                unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                if CID_CODEBREAKERS in unused_pers:
                    ans.append(AID_CARD_CODEBREAKERS)
                if CID_TAX_COLLECTOR in unused_pers:
                    foo = self.board.get_num_warriors(PIND_EYRIE)
                    ans += [i+AID_CARD_TAX_COLLECTOR for i,amount in enumerate(foo) if (amount > 0)]
                if any(any(x) for x in self.remaining_decree.values()):
                    # an action must be taken if possible!
                    # some of decree still remains to resolve
                    decree_actions = self.get_decree_resolving_actions(current_player)
                    if bool(decree_actions): # there is an action to take for the decree
                        return ans + decree_actions
                    # otherwise, we will turmoil
                    if bool(ans): # give them one last chance to use cards
                        return [AID_GENERIC_SKIP] + ans
                    # if no persistent to use, turmoil now
                    self.phase_steps = 3
                else:
                    # decree is done
                    if bool(ans):
                        return [AID_GENERIC_SKIP] + ans
                    self.phase_steps = 4
            if self.phase_steps == 3: # we are turmoiling
                to_discard,pts = current_player.turmoil_helper()
                self.change_score(PIND_EYRIE,-pts)
                self.discard_pile += to_discard
                return [i+AID_CHOOSE_LEADER for i in current_player.available_leaders]
            if self.phase_steps == 4: # End of daylight
                self.phase_steps = 0
                self.phase = self.PHASE_EVENING_EYRIE
        if self.phase == self.PHASE_EVENING_EYRIE:
            if self.phase_steps == 0:
                unused_pers = {c.id for c in current_player.persistent_cards} - self.persistent_used_this_turn
                if CID_COBBLER in unused_pers:
                    ans = self.board.get_legal_move_actions(PIND_EYRIE,{0,1,2})
                    if bool(ans):
                        return [AID_GENERIC_SKIP] + ans
                self.phase_steps = 1
            # Evening Phase
            if self.phase_steps == 1:
                self.change_score(PIND_EYRIE,current_player.get_points_to_score())
                self.draw_cards(PIND_EYRIE,current_player.get_num_cards_to_draw())
                self.phase_steps = 2
            if self.phase_steps == 2 and len(current_player.hand) > 5:
                ans = {c.id+AID_DISCARD_CARD for c in current_player.hand}
                return list(ans)
            # turn done!
            self.phase_steps = 0
            self.phase = self.PHASE_BIRDSONG_MARQUISE
            self.current_player = 1
            return self.advance_marquise(self.players[PIND_MARQUISE])

    # ACTION RESOLUTION
    def resolve_action(self,action:int):
        """
        One of the big ones.
        Given an action number, alters the board itself according
        to the current player. It uses the saved information about the
        state of the board to exactly update the state as if only the
        given action was performed.

        Does NOT try to advance the game, or find who should make
        the next action. That should be done in the advancement function. TODO
        """
        current_player = self.players[self.to_play()]
        # go by current phase of the current turn
        ### STANDARD TURNS
        if self.phase == self.PHASE_DAYLIGHT_MARQUISE:
            self.marquise_daylight(action,current_player)
        elif self.phase == self.PHASE_DAYLIGHT_EYRIE:
            self.eyrie_daylight(action,current_player)
        elif self.phase == self.PHASE_BIRDSONG_MARQUISE:
            self.marquise_birdsong(action,current_player)
        elif self.phase == self.PHASE_BIRDSONG_EYRIE:
            self.eyrie_birdsong(action,current_player)
        elif self.phase == self.PHASE_EVENING_MARQUISE:
            self.marquise_evening(action)
        elif self.phase == self.PHASE_EVENING_EYRIE:
            self.eyrie_evening(action)
        ### INITIAL SETUP
        elif self.phase == self.PHASE_SETUP_MARQUISE:
            self.marquise_setup(action,current_player)
        elif self.phase == self.PHASE_SETUP_EYRIE:
            self.eyrie_setup(action,current_player)

    def marquise_setup(self,action:int,current_player:Marquise):
        "Performs the corresponding Marquise setup action."
        s = self.phase_steps
        if s == 0: # choosing where to put the Keep
            chosen_clearing = action - AID_CHOOSE_CLEARING
            current_player.keep_clearing_id = chosen_clearing
            current_player.change_num_tokens(TIND_KEEP,-1)
            self.board.place_token(PIND_MARQUISE,TIND_KEEP,chosen_clearing)
            # Garrison
            skip = self.board.clearings[chosen_clearing].opposite_corner_id
            for i in range(12):
                if i != skip:
                    self.board.place_warriors(PIND_MARQUISE,1,i)
            current_player.change_num_warriors(-11)
        elif s == 1: # choosing where to place a sawmill
            chosen_clearing = action - AID_BUILD1
            current_player.update_from_building_placed(BIND_SAWMILL)
            self.board.place_building(PIND_MARQUISE,BIND_SAWMILL,chosen_clearing)
        elif s == 2: # choosing where to place a workshop
            chosen_clearing = action - AID_BUILD2
            current_player.update_from_building_placed(BIND_WORKSHOP)
            self.board.place_building(PIND_MARQUISE,BIND_WORKSHOP,chosen_clearing)
        elif s == 3: # choosing where to place a recruiter
            chosen_clearing = action - AID_BUILD3
            current_player.update_from_building_placed(BIND_RECRUITER)
            self.board.place_building(PIND_MARQUISE,BIND_RECRUITER,chosen_clearing)
        self.phase_steps += 1

    def marquise_birdsong(self,action:int,current_player:Marquise):
        "Performs the action during the Marquise's birdsong / changes the turn stage."
        if action >= AID_CHOOSE_CLEARING and action <= AID_CHOOSE_CLEARING + 11: # choose where to place wood
            self.available_wood_spots[action - AID_CHOOSE_CLEARING] -= 1
            current_player.change_num_tokens(TIND_WOOD,-1)
            self.board.place_token(PIND_MARQUISE,TIND_WOOD,action - AID_CHOOSE_CLEARING)
            can_place_wood = [(x > 0) for x in self.available_wood_spots]
            if (current_player.get_num_tokens_in_store(TIND_WOOD) == 0) or (sum(can_place_wood) == 0):
                # finished placing wood
                # (no wood / no sawmills left to cover)
                self.phase_steps = 2
            elif sum(can_place_wood) == 1:
                # there is no choice left of where to place
                i = can_place_wood.index(True)
                foo = self.available_wood_spots[i]
                amount_to_place = min(foo, current_player.get_num_tokens_in_store(TIND_WOOD))
                while amount_to_place > 0:
                    current_player.change_num_tokens(TIND_WOOD,-1)
                    self.board.place_token(PIND_MARQUISE,TIND_WOOD,i)
                    amount_to_place -= 1
                self.phase_steps = 2
            # if neither of the two conditions above are
            # satisfied, then we still have a choice and
            # do not move on to phase_steps 2
        elif action == AID_CARD_BBB:
            self.activate_better_burrow(PIND_MARQUISE,PIND_EYRIE)
            self.persistent_used_this_turn.add(CID_BBB)
            self.phase_steps = 1
        elif action == AID_GENERIC_SKIP:
            self.phase_steps = 3
        elif action == AID_CARD_STAND_DELIVER:
            self.activate_stand_and_deliver(PIND_MARQUISE,PIND_EYRIE)
            self.persistent_used_this_turn.add(CID_STAND_AND_DELIVER)
        elif action == AID_CARD_ROYAL_CLAIM:
            self.activate_royal_claim(PIND_MARQUISE)
            self.persistent_used_this_turn.add(CID_ROYAL_CLAIM)
    
    def marquise_daylight(self,action:int,current_player:Marquise):
        "Performs the given daylight action for the Marquise."
        if action >= AID_CRAFT_CARD and action <= AID_CRAFT_CARD + 40: # craft a card
            self.craft_card(PIND_MARQUISE,action - AID_CRAFT_CARD)
        elif action == AID_GENERIC_SKIP:
            if self.phase_steps in {0,1}: # skipping using CWARREN / crafting / using cards 
                self.phase_steps += 1
            elif self.phase_steps == 2:
                self.phase_steps = 6
            elif self.phase_steps == 3: # we forfeit second move of a march
                self.phase_steps = 2
                self.marquise_moves = 2

        elif action >= AID_SPEND_BIRD and action <= AID_SPEND_BIRD + 9:
            self.discard_from_hand(PIND_MARQUISE, ACTION_TO_BIRD_ID[action])
            self.marquise_actions += 1
        elif action >= AID_BATTLE and action <= AID_BATTLE + 11:
            self.battle = Battle(PIND_MARQUISE,PIND_EYRIE,action - AID_BATTLE)
            self.marquise_actions -= 1
        elif action >= AID_MOVE and action <= AID_MOVE + 3599:
            start,foo = divmod(action - AID_MOVE,300)
            end,amount = divmod(foo,25)
            self.board.move_warriors(PIND_MARQUISE,amount + 1,start,end)
            if self.marquise_moves == 1: # we just marched a second time
                self.marquise_moves = 2
                self.phase_steps = 2
            else: # we just made the first move in a march
                self.marquise_actions -= 1
                self.marquise_moves = 1
                self.phase_steps = 3
        elif action == AID_RECRUIT:
            all_recruited = self.place_marquise_warriors(current_player)
            self.recruited_this_turn = 1
            self.marquise_actions -= 1
            if not all_recruited:
                self.phase_steps = 4
        elif action >= AID_BUILD1 and action <= AID_BUILD1 + 11:
            # building a Sawmill
            wood_spent = self.place_marquise_building(current_player, BIND_SAWMILL, action - AID_BUILD1)
            self.marquise_actions -= 1
            if not wood_spent:
                self.phase_steps = 5
        elif action >= AID_BUILD2 and action <= AID_BUILD2 + 11:
            # building a Workshop
            wood_spent = self.place_marquise_building(current_player, BIND_WORKSHOP, action - AID_BUILD2)
            self.marquise_actions -= 1
            if not wood_spent:
                self.phase_steps = 5
        elif action >= AID_BUILD3 and action <= AID_BUILD3 + 11:
            # building a Recruiter
            wood_spent = self.place_marquise_building(current_player, BIND_RECRUITER, action - AID_BUILD3)
            self.marquise_actions -= 1
            if not wood_spent:
                self.phase_steps = 5
        elif action >= AID_OVERWORK and action <= AID_OVERWORK + 503:
            card_id,clearing_id = divmod(action - AID_OVERWORK, 12)
            self.marquise_actions -= 1
            self.discard_from_hand(PIND_MARQUISE,card_id)
            current_player.change_num_tokens(TIND_WOOD,-1)
            self.board.place_token(PIND_MARQUISE,TIND_WOOD,clearing_id)
        elif self.phase_steps == 5:
            # we are choosing where to take wood from
            self.board.clearings[action - AID_CHOOSE_CLEARING].remove_token(PIND_MARQUISE,TIND_WOOD)
            current_player.change_num_tokens(TIND_WOOD,1)
            self.remaining_wood_cost -= 1
            self.available_wood_spots[action - AID_CHOOSE_CLEARING] -= 1
            can_spend = [(x > 0) for x in self.available_wood_spots]
            if self.remaining_wood_cost == 0:
                # we have taken the last wood needed to spend
                self.phase_steps = 2
            elif sum(can_spend) == 1:
                # we can only take wood from this one spot
                i = can_spend.index(True)
                amount_to_take = self.available_wood_spots[i]
                while amount_to_take:
                    current_player.change_num_tokens(TIND_WOOD,1)
                    self.board.clearings[i].remove_token(PIND_MARQUISE,TIND_WOOD)
                    self.remaining_wood_cost -= 1
                    amount_to_take -= 1
                self.phase_steps = 2
            # if neither of the two conditions above are
            # satisfied, then we still have a choice and
            # do not move on to phase_steps 2

        elif self.phase_steps == 4:
            # we are choosing where to recruit
            current_player.change_num_warriors(-1)
            self.board.place_warriors(PIND_MARQUISE,1,action - AID_CHOOSE_CLEARING)
            self.available_recruiters[action - AID_CHOOSE_CLEARING] -= 1
            can_recruit = [(x > 0) for x in self.available_recruiters]
            if (current_player.warrior_storage == 0) or (sum(can_recruit) == 0):
                # we are done recruiting
                self.phase_steps = 2
            elif sum(can_recruit) == 1:
                # there is no choice left of where to place
                i = can_recruit.index(True)
                foo = self.available_recruiters[i]
                amount_to_place = min(foo, current_player.warrior_storage)
                current_player.change_num_warriors(-amount_to_place)
                self.board.place_warriors(PIND_MARQUISE,amount_to_place,action - AID_CHOOSE_CLEARING)
                self.phase_steps = 2
            # if neither of the two conditions above are
            # satisfied, then we still have a choice and
            # do not move on to phase_steps 2

        elif action == AID_CARD_CODEBREAKERS:
            self.persistent_used_this_turn.add(CID_CODEBREAKERS)
            self.activate_codebreakers(PIND_MARQUISE,PIND_EYRIE)
        elif action >= AID_CARD_TAX_COLLECTOR and action <= AID_CARD_TAX_COLLECTOR + 11: # activate tax collector
            self.persistent_used_this_turn.add(CID_TAX_COLLECTOR)
            self.activate_tax_collector(PIND_MARQUISE,action - AID_CARD_TAX_COLLECTOR)
        elif action >= AID_CARD_COMMAND_WARREN and action <= AID_CARD_COMMAND_WARREN + 11: # activate command warren
            self.phase_steps = 1
            self.persistent_used_this_turn.add(CID_COMMAND_WARREN)
            self.battle = Battle(PIND_MARQUISE,PIND_EYRIE,action - AID_CARD_COMMAND_WARREN)
        elif action >= AID_CRAFT_ROYAL_CLAIM and action <= AID_CRAFT_ROYAL_CLAIM + 14: # craft Royal Claim
            self.craft_royal_claim(PIND_MARQUISE,action)
    
    def marquise_evening(self,action:int):
        "Performs the given action for the Marquise in Evening."
        if action >= AID_MOVE and action <= AID_MOVE + 3599: # Cobbler
            start,foo = divmod(action - AID_MOVE,300)
            end,amount = divmod(foo,25)
            self.board.move_warriors(PIND_MARQUISE,amount + 1,start,end)
            self.persistent_used_this_turn.add(CID_COBBLER)
            self.phase_steps = 1
        elif action == AID_GENERIC_SKIP: # choose not to use cobbler
            self.phase_steps = 1
        elif action >= AID_DISCARD_CARD and action <= AID_DISCARD_CARD + 41: # Discard excess card
            self.discard_from_hand(PIND_MARQUISE, action - AID_DISCARD_CARD)


    def eyrie_setup(self,action:int,current_player:Eyrie):
        "Performs the corresponding Eyrie setup action."
        s = self.phase_steps
        if s == 0: # choosing which leader to setup
            # initial setup
            keep_id = self.players[PIND_MARQUISE].keep_clearing_id
            setup_id = self.board.clearings[keep_id].opposite_corner_id
            current_player.place_roost()
            current_player.change_num_warriors(-6)
            self.board.place_building(PIND_EYRIE,BIND_ROOST,setup_id)
            self.board.place_warriors(PIND_EYRIE,6,setup_id)
            # action is the leader that was chosen
            current_player.choose_new_leader(action - AID_CHOOSE_LEADER)
        self.phase_steps += 1
    
    def eyrie_birdsong(self,action:int,current_player:Eyrie):
        "Performs the action during the Eyrie's birdsong / changes the turn stage."
        if action == AID_CARD_BBB:
            self.activate_better_burrow(PIND_EYRIE,PIND_MARQUISE)
            self.persistent_used_this_turn.add(CID_BBB)
            self.phase_steps = 1
        elif action == AID_GENERIC_SKIP: # don't use BBB OR Don't add second card to decree
            self.phase_steps += 1

        elif action >= AID_DECREE_RECRUIT and action <= AID_DECREE_RECRUIT + 41: # add card to RECRUIT
            c = self.get_card(PIND_EYRIE,action - AID_DECREE_RECRUIT,'hand')
            current_player.add_to_decree(c, DECREE_RECRUIT)
            self.eyrie_cards_added += 1
            if c.suit == SUIT_BIRD:
                self.eyrie_bird_added = 1
            if self.eyrie_cards_added == 2:
                self.phase_steps = 3
        elif action >= AID_DECREE_MOVE and action <= AID_DECREE_MOVE + 41: # add card to MOVE
            c = self.get_card(PIND_EYRIE,action - AID_DECREE_MOVE,'hand')
            current_player.add_to_decree(c, DECREE_MOVE)
            self.eyrie_cards_added += 1
            if c.suit == SUIT_BIRD:
                self.eyrie_bird_added = 1
            if self.eyrie_cards_added == 2:
                self.phase_steps = 3
        elif action >= AID_DECREE_BATTLE and action <= AID_DECREE_BATTLE + 41: # add card to BATTLE
            c = self.get_card(PIND_EYRIE,action - AID_DECREE_BATTLE,'hand')
            current_player.add_to_decree(c, DECREE_BATTLE)
            self.eyrie_cards_added += 1
            if c.suit == SUIT_BIRD:
                self.eyrie_bird_added = 1
            if self.eyrie_cards_added == 2:
                self.phase_steps = 3
        elif action >= AID_DECREE_BUILD and action <= AID_DECREE_BUILD + 41: # add card to BUILD
            c = self.get_card(PIND_EYRIE,action - AID_DECREE_BUILD,'hand')
            current_player.add_to_decree(c, DECREE_BUILD)
            self.eyrie_cards_added += 1
            if c.suit == SUIT_BIRD:
                self.eyrie_bird_added = 1
            if self.eyrie_cards_added == 2:
                self.phase_steps = 3

        elif action == AID_CARD_STAND_DELIVER:
            self.activate_stand_and_deliver(PIND_EYRIE,PIND_MARQUISE)
            self.persistent_used_this_turn.add(CID_STAND_AND_DELIVER)
        elif action == AID_CARD_ROYAL_CLAIM:
            self.activate_royal_claim(PIND_EYRIE)
            self.persistent_used_this_turn.add(CID_ROYAL_CLAIM)
        elif action >= AID_BUILD1 and action <= AID_BUILD1 + 11: # choose new roost location with no roosts
            current_player.place_roost()
            self.board.place_building(PIND_EYRIE, BIND_ROOST, action - AID_BUILD1)
            n_warriors = min(3,current_player.warrior_storage)
            self.board.place_warriors(PIND_EYRIE, n_warriors, action - AID_BUILD1)
            current_player.change_num_warriors(-n_warriors)
            self.phase_steps = 4
    
    def eyrie_daylight(self,action:int,current_player:Eyrie):
        "Performs the given daylight action for the Eyrie."
        if action >= AID_CRAFT_CARD and action <= AID_CRAFT_CARD + 40: # craft a card
            self.craft_card(PIND_EYRIE,action - AID_CRAFT_CARD)
        elif action == AID_GENERIC_SKIP:
            if self.phase_steps == 2: # we are choosing not to use cards when given a last choice
                if any(any(x) for x in self.remaining_decree.values()):
                    self.phase_steps = 3
                else:
                    self.phase_steps = 4
            else: # skipping using command warren / skipping crafting cards
                self.phase_steps += 1

        elif action >= AID_BATTLE and action <= AID_BATTLE + 11:
            self.battle = Battle(PIND_EYRIE,PIND_MARQUISE,action - AID_BATTLE)
            self.reduce_decree_count(DECREE_BATTLE, self.board.clearings[action - AID_BATTLE].suit)
        elif action >= AID_MOVE and action <= AID_MOVE + 3599:
            start,foo = divmod(action - AID_MOVE,300)
            end,amount = divmod(foo,25)
            self.board.move_warriors(PIND_EYRIE,amount + 1,start,end)
            self.reduce_decree_count(DECREE_MOVE, self.board.clearings[start].suit)
        elif action >= AID_CHOOSE_CLEARING and action <= AID_CHOOSE_CLEARING + 11:
            # choosing where to recruit (assuming we have the warriors to place ALL (even charismatic))
            amount = 2 if (current_player.chosen_leader_index == LEADER_CHARISMATIC) else 1
            current_player.change_num_warriors(-amount)
            self.board.place_warriors(PIND_EYRIE,amount,action - AID_CHOOSE_CLEARING)
            self.reduce_decree_count(DECREE_RECRUIT, self.board.clearings[action - AID_CHOOSE_CLEARING].suit)
        elif action >= AID_BUILD1 and action <= AID_BUILD1 + 11:
            # building a Roost
            self.board.place_building(PIND_EYRIE,BIND_ROOST,action - AID_BUILD1)
            current_player.place_roost()
            self.reduce_decree_count(DECREE_BUILD, self.board.clearings[action - AID_BUILD1].suit)
        elif self.phase_steps == 3:
            # we are turmoiling and choosing a new leader
            current_player.choose_new_leader(action - AID_CHOOSE_LEADER)
            self.phase_steps = 4

        elif action == AID_CARD_CODEBREAKERS:
            self.persistent_used_this_turn.add(CID_CODEBREAKERS)
            self.activate_codebreakers(PIND_EYRIE,PIND_MARQUISE)
        elif action >= AID_CARD_TAX_COLLECTOR and action <= AID_CARD_TAX_COLLECTOR + 11: # activate tax collector
            self.persistent_used_this_turn.add(CID_TAX_COLLECTOR)
            self.activate_tax_collector(PIND_EYRIE,action - AID_CARD_TAX_COLLECTOR)
        elif action >= AID_CARD_COMMAND_WARREN and action <= AID_CARD_COMMAND_WARREN + 11: # activate command warren
            self.phase_steps = 1
            self.persistent_used_this_turn.add(CID_COMMAND_WARREN)
            self.battle = Battle(PIND_EYRIE,PIND_MARQUISE,action - AID_CARD_COMMAND_WARREN)
        elif action >= AID_CRAFT_ROYAL_CLAIM and action <= AID_CRAFT_ROYAL_CLAIM + 14: # craft Royal Claim
            self.craft_royal_claim(PIND_EYRIE,action)
    
    def eyrie_evening(self,action:int):
        "Performs the given action for the Eyrie in Evening."
        if action >= AID_MOVE and action <= AID_MOVE + 3599: # Cobbler
            start,foo = divmod(action - AID_MOVE,300)
            end,amount = divmod(foo,25)
            self.board.move_warriors(PIND_EYRIE,amount + 1,start,end)
            self.persistent_used_this_turn.add(CID_COBBLER)
            self.phase_steps = 1
        elif action == AID_GENERIC_SKIP: # choose not to use cobbler
            self.phase_steps = 1
        elif action >= AID_DISCARD_CARD and action <= AID_DISCARD_CARD + 41: # Discard excess card
            self.discard_from_hand(PIND_EYRIE, action - AID_DISCARD_CARD)

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

if __name__ == "__main__":
    env = root2pCatsVsEyrie(MAP_AUTUMN,STANDARD_DECK_COMP)
    action_count = 0
    # while action_count < 50:
    while max(env.victory_points) < 10:
        legal_actions = env.legal_actions()
        logger.info(f"Player: {ID_TO_PLAYER[env.to_play()]}")
        logger.info(f"> Action {action_count} - Legal Actions: {legal_actions}")
        print(f"Player: {ID_TO_PLAYER[env.to_play()]}")
        print("Legal Actions:",legal_actions)

        # action = -1
        # while action not in legal_actions:
        #     action = int(input("Choose a valid action: "))
        action = random.choice(legal_actions)
        print(f"\tAction Chosen: {action}")
        logger.info(f"\t> Action Chosen: {action}")
        env.step(action)
        action_count += 1