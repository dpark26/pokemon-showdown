from poke_env.player import Player, RandomPlayer
from BattleUtilities import get_defensive_type_multiplier, opponent_can_outspeed
from GameNode import GameNode
import asyncio
import time
import random

class MinimaxPlayer(Player):

    previous_action = None
    maxDepth = 3
    # The nodes keep track of battle states, moves are transitions between states
    def choose_move(self, battle):
        # HP values for you and your opponent's Pokemon are a dictionary that maps Pokemon to HP
        current_hp = {}
        for pokemon in battle.team.values():
            current_hp.update({pokemon : pokemon.current_hp})
        opponent_hp = {}
        for pokemon in battle.opponent_team.values():
            opponent_hp.update({pokemon : pokemon.current_hp})
        starting_node = GameNode(battle, battle.active_pokemon, current_hp, battle.opponent_active_pokemon, opponent_hp, None, float('-inf'), None, self.previous_action)
        if battle.active_pokemon.current_hp <= 0:
            # pokemon fainted
            self.pick_best_switch(starting_node, 0)
        else:
            alpha = float("-inf")
            beta = float("inf")
            self.minimax(starting_node, 0, True, alpha, beta)
        child_nodes = starting_node.children
        best_score = float('-inf')
        best_node = None
        for child in child_nodes:
            if child.score >= best_score: 
                best_score = child.score
                best_node = child
        if best_node == None:
            #print(f"Best node is none for some reason! Length of child_nodes is {len(child_nodes)}")
            self.previous_action = None
            return self.choose_default_move()
        #if isinstance(best_node.action, Pokemon): 
            #print(f"Switching from {battle.active_pokemon} (type matchup score {BattleUtilities.get_defensive_type_multiplier(battle.active_pokemon, battle.opponent_active_pokemon)}) to {best_node.action} (type matchup score {BattleUtilities.get_defensive_type_multiplier(best_node.action, battle.opponent_active_pokemon)}) against {battle.opponent_active_pokemon}")
        #else:
        #    print(f"Pokemon {battle.active_pokemon} attacking with {best_node.action} against {battle.opponent_active_pokemon}")
        self.previous_action = best_node.action
        return self.create_order(best_node.action)



    def minimax(self, node, depth, is_bot_turn, alpha, beta):
        if depth == self.maxDepth or self.is_terminal(node): 
            self.score(node)
            return node.score
        if is_bot_turn:
            score = float('-inf')
            bot_moves = node.generate_bot_moves()
            for move in bot_moves: 
                child_score = self.minimax(move, depth, False, alpha, beta)
                if child_score > score:
                    score = child_score
                    alpha = max(alpha, score)
                if score > beta:
                    node.score = score
                    return score
            node.score = score
            return score
        else: 
            score = float('inf')
            opponent_moves = node.generate_opponent_moves()
            if len(opponent_moves) > 0:
                for move in opponent_moves: 
                    child_score = self.minimax(move, depth + 1, True, alpha, beta)
                    # score = min(score, child_score)
                    if child_score < score:
                        score = child_score
                        beta = min(beta, score)
                    if score < alpha:
                        node.score = score
                        return score

            else: 
                score = float('-inf')
            node.score = score
            return score



    def pick_best_switch(self, node, depth):
        switches = node.add_bot_switches()
        score = float('-inf')
        for switch in switches:
            alpha = float("-inf")
            beta = float("inf")
            child_score = self.minimax(switch, depth, False, alpha, beta)
            score = max(score, child_score)
        node.score = score
        return score



    # This function determines if this is an end state and we should stop
    def is_terminal(self, node):
        all_fainted = True
        for pokemon in node.current_HP.keys():
            if node.current_HP[pokemon] > 0:
                all_fainted = False
        if all_fainted:
            return True
        all_fainted = True
        for pokemon in node.opponent_HP.keys():
            if node.opponent_HP[pokemon]:
                all_fainted = False
        if all_fainted:
            return True
        return False



    def score(self, node):
        score = 0
        # Get positive points for dealing damage and knocking out opponent
        for pokemon in node.opponent_HP.keys():
            if pokemon.current_hp is not None:
                if node.opponent_HP[pokemon] <= 0 and pokemon.current_hp > 0:
                    score += 300
                else:
                    damage = pokemon.current_hp - node.opponent_HP[pokemon]
                    score += 3 * damage
            #else:
                #print(f"Pokemon is {pokemon}, HP is None")
        # Lose points for taking damage or getting knocked out
        for pokemon in node.current_HP.keys():
            if node.current_HP[pokemon] <= 0 and pokemon.current_hp > 0:
                # Only lose points if pokemon had significant amount of hp --> enable "sacking"
                if (pokemon.current_hp / pokemon.max_hp) > .2:
                    score -= 300
                # score -= 100
            else:
                damage = (pokemon.current_hp / pokemon.max_hp) - (node.current_HP[pokemon] / pokemon.max_hp)
                score -= 3 * damage
        # Lose points for getting outsped by opponent
        if opponent_can_outspeed(node.current_pokemon, node.opponent_pokemon):
           score -= 25
        # Add / Subtract points for type match-up
        type_multiplier = get_defensive_type_multiplier(node.current_pokemon, node.opponent_pokemon)
        if type_multiplier == 4:
           score -= 50
        if type_multiplier == 2:
           score -= 25
        if type_multiplier == 0.5:
           score += 25
        if type_multiplier == 0.25:
           score += 50
        node.score = score
        return score
		
class MaxDamagePlayer(Player):
    def choose_move(self, battle):
        # If the player can attack, it will
        if battle.available_moves:
            # Finds the best move among available ones
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)

        # If no attack is available, a random switch will be made
        else:
            return self.choose_random_move(battle)
		
async def main():
	start = time.time()

	# create two players
	random_player = MaxDamagePlayer(battle_format="gen8randombattle",)
	minimax_player = MinimaxPlayer(battle_format="gen8randombattle",)

	# evaluate player
	await minimax_player.battle_against(random_player, n_battles=1000)

	print("Minimax player won %d / 100 battles [this took %f seconds]"% (minimax_player.n_won_battles, time.time() - start))

if __name__ == "__main__":
	asyncio.get_event_loop().run_until_complete(main())