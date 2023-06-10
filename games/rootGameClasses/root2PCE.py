import numpy as np
import math
import random
from classes import *


class root2pCatsVsEyrie:
    PHASE_SETUP_MARQUISE = 0
    PHASE_SETUP_EYRIE = 1
    PHASE_BIRDSONG_START_MARQUISE = 2
    PHASE_BIRDSONG_START_EYRIE = 3
    PHASE_BIRDSONG_MARQUISE = 4
    PHASE_BIRDSONG_EYRIE = 5
    PHASE_DAYLIGHT_START_MARQUISE = 6
    PHASE_DAYLIGHT_START_EYRIE = 7
    PHASE_DAYLIGHT_MARQUISE = 8
    PHASE_DAYLIGHT_EYRIE = 9
    PHASE_EVENING_START_MARQUISE = 10
    PHASE_EVENING_START_EYRIE= 11
    PHASE_EVENING_MARQUISE = 12
    PHASE_EVENING_EYRIE= 13

    def __init__(self, board_comp:list, deck_composition:list):
        self.n_players = N_PLAYERS
        self.current_player = 1
        self.players = [Marquise(0), Eyrie(1)]
        self.victory_points = [0,0]
        self.phase = self.PHASE_SETUP_MARQUISE
        self.num_field_hospitals = 0
        self.phase_steps = 0
        self.persistent_used_this_turn = set()
        self.remaining_craft_power = [0,0,0]
        self.available_sawmills = [0]
        self.available_recruiters = [0]
        self.marquise_actions = 0

        self.board = Board(board_comp)
        self.deck = Deck(deck_composition)
        self.battle = Battle(-1,-1,-1)
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
        # self.available_dominances = set()

    def to_play(self):
        return 0 if self.current_player == 1 else 1

    def reset(self):
        self.current_player = 1
        self.players = [Marquise(0), Eyrie(1)]
        self.victory_points = [0,0]
        self.phase = self.PHASE_SETUP_MARQUISE
        self.num_field_hospitals = 0
        self.phase_steps = 0
        self.persistent_used_this_turn = set()
        self.remaining_craft_power = [0,0,0]
        self.available_sawmills = [0]
        self.available_recruiters = [0]
        self.marquise_actions = 0

        self.board.reset()
        self.deck.reset()
        self.battle = Battle(-1,-1,-1)
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
        # self.available_dominances = set()

        return self.get_observation()

    def step(self, action):
        x = math.floor(action / self.board_size)
        y = action % self.board_size
        self.board[x][y] = self.current_player

        done = self.is_finished()

        reward = 1 if done else 0

        self.current_player *= -1

        return self.get_observation(), reward, done

    def get_observation(self):
        board_player1 = np.where(self.board == 1, 1.0, 0.0)
        board_player2 = np.where(self.board == -1, 1.0, 0.0)
        board_to_play = np.full((11, 11), self.current_player, dtype="int32")
        return np.array([board_player1, board_player2, board_to_play])

    def legal_actions(self):
        legal = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    legal.append(i * self.board_size + j)
        return legal
    
    def draw_cards(self,player_index:int,amount:int):
        """
        Draws a number of cards from the top of the deck and then
        adds them to a player's hand.

        If the deck runs out, it automatically uses up the
        discard pile to refresh the deck and then continues drawing.
        """
        p = self.players[player_index]
        while amount:
            if self.deck.size() == 0:
                self.deck.add(self.discard_pile)
                self.discard_pile = []
            p.hand += self.deck.draw(1)
            amount -= 1
    
    def get_card(self,player_index:int,card_id:int,location:str):
        "Removes and returns the card from the given location for the player. location can be 'hand' or 'persistent'."
        loc = self.players[player_index].hand if (location == 'hand') else self.players[player_index].persistent_cards
        for i,c in enumerate(loc):
            if c.id == card_id:
                return loc.pop(i)
            
    def discard_from_hand(self,player_index:int,card_id:int):
        "Makes a player discard a card of the matching id from their hand, assuming they have it."
        c_to_discard = self.get_card(player_index,card_id,"hand")
        self.discard_pile.append(c_to_discard)
    
    def discard_from_persistent(self,player_index:int,card_id:int):
        "Makes a player discard a card of the matching id from their persistent cards, assuming they have it."
        c_to_discard = self.get_card(player_index,card_id,"persistent")
        self.discard_pile.append(c_to_discard)

    def change_score(self,player_index:int,amount:int):
        "Makes a player score some amount of points. Use a negative amount to lose points."
        p = self.victory_points[player_index]
        self.victory_points[player_index] = max(0, p + amount)

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
            self.available_items[item_id] -= 1
            p.crafted_items[item_id] += 1
            
            # Disdain for Trade for the Eyrie (unless they have Builder leader)
            points_scored = 1 if (player_index == PIND_EYRIE and p.chosen_leader_index != LEADER_BUILDER) else card_to_craft.points
            self.change_score(player_index,points_scored)
            
            self.discard_from_hand(player_index,card_id)
        elif card_to_craft.is_persistent:
            # we are crafting a persistent card
            p.persistent_cards.append(card_to_craft)
            p.hand.pop(hand_i)
        elif card_id in CID_FAVORS:
            # a favor card has been activated
            points_scored,total_marqwars = self.board.resolve_favor(player_index,CLEARING_SUITS[card_to_craft.suit])
            self.change_score(player_index,points_scored)
            if total_marqwars:
                self.num_field_hospitals = total_marqwars
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
        for i in range(3):
            self.remaining_craft_power[i] -= recipe_used[i]

    # BATTLE FUNCTIONS
    def activate_field_hospitals(self,amount:int,payment_card_id:int):
        "Places 'amount' of warriors at the Marquise's Keep and discards the given card from their hand."
        keep_clearing = self.players[PIND_MARQUISE].keep_clearing_id
        self.board.clearings[keep_clearing].change_num_warriors(PIND_MARQUISE,amount)
        self.discard_from_hand(PIND_MARQUISE,payment_card_id)
        self.num_field_hospitals = 0

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

    def resolve_battle_action(self,action):
        """
        Given an action number, performs the given action given the
        current information stored about any battles currently going on.

        Assumes that self.battle points to an existing Battle object.
        """
        defender = self.players[self.battle.defender_id]
        if self.battle.stage is None:
            # the battle just started, assume a brand new Battle object was just created
            if defender.has_ambush_in_hand():
                # the defender chooses to ambush or not
                self.battle.stage = Battle.STAGE_DEF_AMBUSH
                return self.battle.defender_id
            # no ambush is possible, so we move straight to the dice roll
            self.battle.stage = Battle.STAGE_DICE_ROLL

        attacker = self.players[self.battle.attacker_id]
        clearing = self.board.clearings[self.battle.clearing_id]
        if self.battle.stage == Battle.STAGE_DEF_ORDER:
            # action is what defender building/token to hit with the next hit
            if action in {1,2,2,5,5,31,3}:
                clearing.remove_token(self.battle.defender_id,action - 235235)
            else:
                clearing.remove_building(self.battle.defender_id,action - 23452)
            # see if there is a choice anymore
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.defender_id, self.battle.att_hits_to_deal - 1, self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.att_hits_to_deal > 0:
                # defender still has a choice of what to remove
                return self.battle.defender_id
            
            # all hits needed have been dealt to defender
            # it is now the attacker's turn to take hits
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id, self.battle.def_hits_to_deal, self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed
            
            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice on what to remove
                self.battle.stage = Battle.STAGE_ATT_ORDER
            else:
                # the battle is over
                self.battle.stage = Battle.STAGE_DONE
            return self.battle.attacker_id
            
        if self.battle.stage == Battle.STAGE_ATT_ORDER:
            # action is what attacker building/token to hit with the next hit
            if action in {1,2,2,5,5,31,3}:
                clearing.remove_token(self.battle.attacker_id,action - 235235)
            else:
                clearing.remove_building(self.battle.attacker_id,action - 23452)
            # see if there is a choice anymore
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id, self.battle.def_hits_to_deal - 1, self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed
            
            if self.battle.def_hits_to_deal > 0:
                # attacker still has a choice of what to remove
                return self.battle.attacker_id
            
            # All hits have been dealt, so we are in one of two possible situations:
            # 1. The dice have not been rolled. If the -attacker- is choosing buildings to destroy,
            #    then that means they attacked with 1 warrior and were ambushed, and now had to
            #    choose one of their buildings to remove. They have no warriors and the battle is over.
            # 2. The dice have been rolled and extra effects have been chosen. However, the attacker is
            #    last to pick which things get hit in what order, so the battle must be over.
            self.battle.stage = Battle.STAGE_DONE
            return self.battle.attacker_id
        
        if self.battle.stage == Battle.STAGE_DEF_AMBUSH:
            # action is the defender's choice to ambush or not
            if action == AID_AMBUSH_NONE:
                # we immediately go to the dice roll
                self.battle.stage = Battle.STAGE_DICE_ROLL
            else:
                # save which ambush card is played
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
                    self.battle.stage = Battle.STAGE_DICE_ROLL
                # otherwise, see if attacker can choose to counter ambush
                elif attacker.has_ambush_in_hand():
                    self.battle.stage = Battle.STAGE_ATT_AMBUSH
                    return self.battle.attacker_id
                # otherwise, the ambush triggers and 2 hits are dealt
                self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id, 2, self.battle.clearing_id)
                if cardboard_removed:
                    self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
                if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                    self.num_field_hospitals = warriors_killed

                # check if a choice must be made from hits
                if self.battle.def_hits_to_deal > 0:
                    self.battle.stage = Battle.STAGE_ATT_ORDER
                    return self.battle.attacker_id
                # if the hits are all dealt, we check if a battle can still occur
                elif clearing.get_num_warriors(self.battle.attacker_id) > 0:
                    self.battle.stage = Battle.STAGE_DICE_ROLL
                # otherwise, the ambush wiped out all attackers
                else:
                    self.battle.stage = Battle.STAGE_DONE
                    return self.battle.attacker_id

        if self.battle.stage == Battle.STAGE_ATT_AMBUSH:
            # action is the attacker's choice to counter ambush or not
            if action == AID_AMBUSH_NONE:
                # the ambush triggers and 2 hits are dealt
                # deal_hits returns the number of remaining hits there are; if >0, it means a choice is possible for the one getting hit
                self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id, 2, self.battle.clearing_id)
                if cardboard_removed:
                    self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
                if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                    self.num_field_hospitals = warriors_killed

                # check if a choice must be made from hits
                if self.battle.def_hits_to_deal > 0:
                    self.battle.stage = Battle.STAGE_ATT_ORDER
                    return self.battle.attacker_id
                # if the hits are all dealt, we check if a battle can still occur
                elif clearing.get_num_warriors(self.battle.attacker_id) > 0:
                    self.battle.stage = Battle.STAGE_DICE_ROLL
                # otherwise, the ambush wiped out all attackers
                else:
                    self.battle.stage = Battle.STAGE_DONE
                    return self.battle.attacker_id
            else:
                # save which ambush card is played
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
                self.battle.stage = Battle.STAGE_DICE_ROLL

        if self.battle.stage == Battle.STAGE_DICE_ROLL:
            # the dice must be rolled before continuing
            roll = [random.randint(0,3) for i in range(2)]
            self.battle.att_rolled_hits = min(clearing.get_num_warriors(self.battle.attacker_id), max(roll))
            self.battle.def_rolled_hits = min(clearing.get_num_warriors(self.battle.defender_id), min(roll))
            # defenseless
            if clearing.get_num_warriors(self.battle.defender_id) == 0:
                self.battle.att_extra_hits += 1
            # Eyrie Commander Leader
            if (self.battle.attacker_id == PIND_EYRIE) and (attacker.chosen_leader_index == LEADER_COMMANDER):
                self.battle.att_extra_hits += 1

            # check if the attacker can choose extra effects
            if any((c.id in {CID_ARMORERS,CID_BRUTAL_TACTICS}) for c in attacker.persistent_cards):
                self.battle.stage = Battle.STAGE_ATT_EFFECTS
                return self.battle.attacker_id
            # check if the defender can choose extra effects
            if any((c.id in {CID_ARMORERS,CID_SAPPERS}) for c in defender.persistent_cards):
                self.battle.stage = Battle.STAGE_DEF_EFFECTS
                return self.battle.defender_id
            
            # no extra effects can be chosen, so deal the hits next
            # next, the defender takes hits first
            self.battle.def_hits_to_deal = self.battle.def_rolled_hits
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.battle.stage = Battle.STAGE_DEF_ORDER
                return self.battle.defender_id
            # lastly, attacker takes hits
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id,self.battle.def_hits_to_deal,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice of what to remove
                self.battle.stage = Battle.STAGE_ATT_ORDER
                return self.battle.attacker_id
            # battle is over
            self.battle.stage = Battle.STAGE_DONE
            return self.battle.attacker_id
        
        if self.battle.stage == Battle.STAGE_ATT_EFFECTS:
            # the attacker has chosen what extra effects to use
            if action in {AID_EFFECTS_ARMORERS,AID_EFFECTS_ARM_BT}:
                # Armorers is used up
                self.battle.def_rolled_hits = 0
                self.discard_from_persistent(self.battle.attacker_id,CID_ARMORERS)
            if action in {AID_EFFECTS_BRUTTACT,AID_EFFECTS_ARM_BT}:
                # brutal tactics is used
                self.battle.att_extra_hits += 1
                self.change_score(self.battle.defender_id,1)
            # check if the defender can choose extra effects
            if any((c.id in {CID_ARMORERS,CID_SAPPERS}) for c in defender.persistent_cards):
                self.battle.stage = Battle.STAGE_DEF_EFFECTS
                return self.battle.defender_id
            
            # next, the defender takes hits first
            self.battle.def_hits_to_deal = self.battle.def_rolled_hits
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.battle.stage = Battle.STAGE_DEF_ORDER
                return self.battle.defender_id
            # lastly, attacker takes hits
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id,self.battle.def_hits_to_deal,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice of what to remove
                self.battle.stage = Battle.STAGE_ATT_ORDER
                return self.battle.attacker_id
            # battle is over
            self.battle.stage = Battle.STAGE_DONE
            return self.battle.attacker_id
        
        if self.battle.stage == Battle.STAGE_DEF_EFFECTS:
            # the defender has chosen what extra effects to use
            if action in {AID_EFFECTS_ARMORERS,AID_EFFECTS_ARMSAP}:
                # Armorers is used up
                self.battle.att_rolled_hits = 0
                self.discard_from_persistent(self.battle.defender_id,CID_ARMORERS)
            if action in {AID_EFFECTS_SAPPERS,AID_EFFECTS_ARMSAP}:
                # sappers is used
                self.battle.def_extra_hits += 1
                self.discard_from_persistent(self.battle.defender_id,CID_SAPPERS)
            # next, the defender takes hits first
            self.battle.def_hits_to_deal = self.battle.def_rolled_hits + self.battle.def_extra_hits
            self.battle.att_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.attacker_id,True,cardboard_removed)
            if warriors_killed and self.battle.defender_id == PIND_MARQUISE and defender.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.battle.stage = Battle.STAGE_DEF_ORDER
                return self.battle.defender_id
            # lastly, attacker takes hits
            self.battle.def_hits_to_deal,warriors_killed,cardboard_removed = self.board.deal_hits(self.battle.attacker_id,self.battle.def_hits_to_deal,self.battle.clearing_id)
            if cardboard_removed:
                self.score_battle_points(self.battle.defender_id,False,cardboard_removed)
            if warriors_killed and self.battle.attacker_id == PIND_MARQUISE and attacker.has_suit_in_hand(clearing.suit):
                self.num_field_hospitals = warriors_killed

            if self.battle.def_hits_to_deal > 0:
                # attacker has a choice of what to remove
                self.battle.stage = Battle.STAGE_ATT_ORDER
                return self.battle.attacker_id
            # battle is over
            self.battle.stage = Battle.STAGE_DONE
            return self.battle.attacker_id


    # Activating Card Effects
    def activate_royal_claim(self,player_index:int):
        "In Birdsong, may discard this to score one point per clearing you rule."
        points = sum((i == player_index) for i in self.board.get_rulers())
        self.change_score(player_index,points)
        self.discard_from_persistent(player_index, CID_ROYAL_CLAIM)
    
    def activate_stand_and_deliver(self,player_index:int,target_index:int):
        "In Birdsong, may take a random card from another player. That player scores one point."
        target_p_hand = self.players[target_index].hand
        chosen_i = random.randint(0,len(target_p_hand) - 1)
        chosen_card = target_p_hand.pop(chosen_i)

        self.players[player_index].hand.append(chosen_card)
        self.change_score(target_index,1)

    def activate_tax_collector(self,player_index:int,clearing_index:int):
        "Once in Daylight, may remove one of your warriors from the map to draw a card."
        self.board.clearings[clearing_index].change_num_warriors(player_index,-1)
        self.draw_cards(player_index,1)
        self.num_field_hospitals = 1

    def activate_better_burrow(self,player_index:int,target_index:int):
        "At start of Birdsong, you and another player draw a card."
        self.draw_cards(player_index,1)
        self.draw_cards(target_index,1)
    
    def activate_codebreakers(self,player_index:int,target_index:int):
        "TODO: Implement"
        pass

    def can_craft(self,card:Card):
        "Returns True only if the current player can currently craft the given card. Checks the remaining crafting power."
        r = card.crafting_recipe
        if max(r) == 0:
            return False
        wild = r[3]
        if wild > 0:
            return sum(self.remaining_craft_power) >= wild
        for i in range(3):
            if r[i] > self.remaining_craft_power[i]:
                return False
        return True
    
    def can_craft_any_card(self,player:Player):
        "Returns True only if the given player can craft ANY card in their hand given the remaining crafting power."
        return any(self.can_craft(c) for c in player.hand)

    def get_craftable_ids(self,player:Player):
        "Returns a set of every card ID that the given player can currently craft, given the remaining crafting power."
        return {c.id for c in player.hand if self.can_craft(c)}

    def place_marquise_wood(self,mplayer:Marquise):
        """
        Places 1 wood token at each Sawmill, unless there is not enough wood.

        Returns True only if all of the wood could be automatically placed, False otherwise.
        """
        sawmill_counts = self.board.get_total_building_counts(PIND_MARQUISE,BIND_SAWMILL)
        if sum(sawmill_counts) > mplayer.get_num_tokens_in_store(TIND_WOOD):
            self.available_sawmills = sawmill_counts
            return False
        # place a wood token for each sawmill at each clearing with a sawmill
        clearings_with_sawmill_ids = {i for i,n in enumerate(sawmill_counts) if n > 0}
        for i in clearings_with_sawmill_ids:
            c = self.board.clearings[i]
            n_sawmills = sawmill_counts[i]
            while n_sawmills:
                mplayer.change_num_tokens(TIND_WOOD, -1)
                c.place_token(PIND_MARQUISE,TIND_WOOD)
                n_sawmills -= 1
        return True

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
        current_index = self.to_play()
        current_player = self.players[current_index]
        # go by current phase of the current turn
        ### INITIAL SETUP
        if self.phase == self.PHASE_SETUP_MARQUISE:
            self.marquise_setup(action,current_index,current_player)

        elif self.phase == self.PHASE_SETUP_EYRIE:
            self.eyrie_setup(action,current_index,current_player)
            if self.phase_steps == 1:
                # START GAME - Random Starting Player?
                if (random.randint(0,1)):# Marquise start
                    self.place_marquise_wood(self.players[PIND_MARQUISE])

                    self.phase = self.PHASE_DAYLIGHT_MARQUISE
                    return True
                else: # Eyrie start
                    self.phase = self.PHASE_BIRDSONG_START_EYRIE
                    return False
        
        ### STANDARD TURNS
        # TODO check for Marquise's Field Hospitals
        elif self.phase == self.PHASE_BIRDSONG_MARQUISE:
            self.marquise_birdsong(action,current_player)

    def marquise_setup(self,action:int,current_index:int,current_player:Marquise):
        "Performs the corresponding Marquise setup action."
        s = self.phase_steps
        if s == 0: # choosing where to put the Keep
            chosen_clearing = action - 1
            current_player.keep_clearing_id = chosen_clearing
            current_player.change_num_tokens(TIND_KEEP,-1)
            self.board.place_token(current_index,TIND_KEEP,chosen_clearing)
            # Garrison
            skip = self.board.clearings[chosen_clearing].opposite_corner_id
            for i in range(12):
                if i != skip:
                    self.board.place_warriors(current_index,1,i)
            current_player.change_num_warriors(-11)
        elif s == 1: # choosing where to place a sawmill
            chosen_clearing = action - 25
            current_player.update_from_building_placed(BIND_SAWMILL)
            self.board.place_building(current_index,BIND_SAWMILL,chosen_clearing)
        elif s == 2: # choosing where to place a workshop
            chosen_clearing = action - 49
            current_player.update_from_building_placed(BIND_WORKSHOP)
            self.board.place_building(current_index,BIND_WORKSHOP,chosen_clearing)
        elif s == 3: # choosing where to place a recruiter
            chosen_clearing = action - 37
            current_player.update_from_building_placed(BIND_RECRUITER)
            self.board.place_building(current_index,BIND_RECRUITER,chosen_clearing)
        self.phase_steps += 1

    def marquise_birdsong(self,action:int,current_player:Marquise):
        "Performs the action during the Marquise's birdsong / changes the turn stage."
        if action in range(1,13): # choose where to place wood
            self.available_sawmills[action - 1] -= 1
            current_player.change_num_tokens(TIND_WOOD,-1)
            self.board.clearings[action - 1].place_token(PIND_MARQUISE,TIND_WOOD)
        elif action == AID_CARD_BBB:
            self.activate_better_burrow(PIND_MARQUISE,PIND_EYRIE)
            self.persistent_used_this_turn.add(CID_BBB)
            self.phase_steps = 1
        elif action == AID_GENERIC_SKIP:
            self.phase_steps = 3
        # if self.phase_steps == 0: # sawmills have not generated wood yet
        #     wood_placed = self.place_marquise_wood(current_player)
        #     self.phase_steps = 1 if (not wood_placed) else 2 # 1 means waiting to place wood, 2 means wood placed, waiting for daylight
        #     return
        elif action == AID_CARD_STAND_DELIVER:
            self.activate_stand_and_deliver(PIND_MARQUISE,PIND_EYRIE)
            self.persistent_used_this_turn.add(CID_STAND_AND_DELIVER)
        elif action == AID_CARD_ROYAL_CLAIM:
            self.activate_royal_claim(PIND_MARQUISE)
            self.persistent_used_this_turn.add(CID_ROYAL_CLAIM)
    
    def marquise_daylight(self,action:int,current_player:Marquise):
        "Performs the given daylight action for the Marquise."
        if action == AID_CARD_CODEBREAKERS:
            self.persistent_used_this_turn.add(CID_CODEBREAKERS)
            self.activate_codebreakers(PIND_MARQUISE,PIND_EYRIE)
        elif action in range(AID_CARD_TAX_COLLECTOR,AID_CARD_TAX_COLLECTOR + 12): # activate tax collector
            self.persistent_used_this_turn.add(CID_TAX_COLLECTOR)
            self.activate_tax_collector(PIND_MARQUISE,action - AID_CARD_TAX_COLLECTOR)
        elif action in range(AID_CARD_COMMAND_WARREN,AID_CARD_COMMAND_WARREN + 12): # activate command warren
            self.phase_steps = 1
            self.persistent_used_this_turn.add(CID_COMMAND_WARREN)
            self.battle = Battle(PIND_MARQUISE,PIND_EYRIE,action - AID_CARD_COMMAND_WARREN)
        elif action in range(AID_CRAFT_CARD,AID_CRAFT_CARD + 41): # craft a card
            self.craft_card(PIND_MARQUISE,action - AID_CRAFT_CARD)
        elif action in range(AID_CRAFT_ROYAL_CLAIM,AID_CRAFT_ROYAL_CLAIM + 15): # craft Royal Claim
            self.craft_royal_claim(PIND_MARQUISE,action)

    def eyrie_setup(self,action:int,current_index:int,current_player:Eyrie):
        "Performs the corresponding Eyrie setup action."
        s = self.phase_steps
        if s == 0: # choosing which leader to setup
            # initial setup
            keep_id = self.players[PIND_MARQUISE].keep_clearing_id
            setup_id = self.board.clearings[keep_id].opposite_corner_id
            current_player.place_roost()
            current_player.change_num_warriors(-6)
            self.board.place_building(current_index,BIND_ROOST,setup_id)
            self.board.place_warriors(current_index,6,setup_id)
            # action is the leader that was chosen
            current_player.choose_new_leader(action - 4358)
        self.phase_steps += 1

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