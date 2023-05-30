import numpy as np
import math
from classes import *


class root2pCatsVsEyrie:
    def __init__(self, board_comp:list, deck_composition:list):
        self.n_players = N_PLAYERS
        self.current_player = 1
        self.players = [Marquise(0), Eyrie(1)]
        self.victory_points = [0,0]

        self.board = Board(board_comp)
        self.deck = Deck(deck_composition)
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
    
    def discard_card(self,player_index:int,card_id:int):
        "Makes a player discard a card of the matching id from their hand, assuming they have it."
        player_hand = self.players[player_index].hand
        for i,c in enumerate(player_hand):
            if c.id == card_id:
                c_to_discard = player_hand.pop(i)
                self.discard_pile.append(c_to_discard)
                return
    
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
            
            points_scored = 1 if (player_index == PIND_EYRIE and p.chosen_leader_index != LEADER_BUILDER) else card_to_craft.points
            self.change_score(player_index,points_scored)
            
            self.discard_card(player_index,card_id)
        elif card_to_craft.is_persistent:
            # we are crafting a persistent card
            p.persistent_cards.append(card_to_craft)
            p.hand.pop(hand_i)
        elif card_id in CID_FAVORS:
            # a favor card has been activated
            pass

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