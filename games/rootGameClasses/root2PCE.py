import numpy as np
import math
import random
from classes import *


class root2pCatsVsEyrie:
    def __init__(self, board_comp:list, deck_composition:list):
        self.n_players = N_PLAYERS
        self.current_player = 1
        self.players = [Marquise(0), Eyrie(1)]
        self.victory_points = [0,0]

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
            points_scored = self.board.resolve_favor(player_index,CLEARING_SUITS[card_to_craft.suit])
            self.change_score(player_index,points_scored)

            self.discard_from_hand(player_index, card_id)
    
    # BATTLE FUNCTIONS
    def activate_field_hospitals(self,amount:int,payment_card_id:int):
        "Places 'amount' of warriors at the Marquise's Keep and discards the given card from their hand."
        keep_clearing = self.players[PIND_MARQUISE].keep_clearing_id
        self.board.clearings[keep_clearing].change_num_warriors(PIND_MARQUISE,amount)
        self.discard_from_hand(PIND_MARQUISE,payment_card_id)

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

        clearing = self.board.clearings[self.battle.clearing_id]
        if self.battle.stage == Battle.STAGE_DEF_ORDER:
            # action is what defender building/token to hit with the next hit
            if action in {1,2,2,5,5,31,3}:
                clearing.remove_token(self.battle.defender_id,action - 235235)
            else:
                clearing.remove_building(self.battle.defender_id,action - 23452)
            # see if there is a choice anymore
            self.battle.att_hits_to_deal = self.board.deal_hits(self.battle.defender_id, self.battle.att_hits_to_deal - 1, self.battle.clearing_id)
            if self.battle.att_hits_to_deal > 0:
                # defender still has a choice of what to remove
                return self.battle.defender_id
            
            # all hits needed have been dealt to defender
            # it is now the attacker's turn to take hits
            self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id, self.battle.def_hits_to_deal, self.battle.clearing_id)
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
            self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id, self.battle.def_hits_to_deal - 1, self.battle.clearing_id)
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
        
        attacker = self.players[self.battle.attacker_id]
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
                self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id, 2, self.battle.clearing_id)
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
                self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id, 2, self.battle.clearing_id)
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
                self.battle.att_extra_hits = 1
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
            self.battle.att_hits_to_deal = self.board.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.battle.stage = Battle.STAGE_DEF_ORDER
                return self.battle.defender_id
            # lastly, attacker takes hits
            self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id,self.battle.def_rolled_hits,self.battle.clearing_id)
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
            self.battle.att_hits_to_deal = self.board.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.battle.stage = Battle.STAGE_DEF_ORDER
                return self.battle.defender_id
            # lastly, attacker takes hits
            self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id,self.battle.def_rolled_hits,self.battle.clearing_id)
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
            self.battle.att_hits_to_deal = self.board.deal_hits(self.battle.defender_id,self.battle.att_extra_hits+self.battle.att_rolled_hits,self.battle.clearing_id)
            if self.battle.att_hits_to_deal > 0:
                # defender has a choice of what to remove
                self.battle.stage = Battle.STAGE_DEF_ORDER
                return self.battle.defender_id
            # lastly, attacker takes hits
            self.battle.def_hits_to_deal = self.board.deal_hits(self.battle.attacker_id,self.battle.def_extra_hits+self.battle.def_rolled_hits,self.battle.clearing_id)
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

    def activate_better_burrow(self,player_index:int,target_index:int):
        "At start of Birdsong, you and another player draw a card."
        self.draw_cards(player_index,1)
        self.draw_cards(target_index,1)


    def resolve_action(self,action:int):
        """
        The big one.
        Given an action number, alters the board itself according
        to the current player.

        TODO: Return info about which player's turn it is / other things
        """
        p = self.players[self.to_play()]
        # if action

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