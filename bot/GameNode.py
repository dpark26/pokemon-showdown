import BattleUtilities

from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon

class GameNode: 
    battle = None
    current_pokemon = None
    current_HP = {}
    opponent_pokemon = None
    opponent_HP = {}
    action = None
    children = []
    score = float('-inf')
    parent_node = None
    previous_action = None

    def __init__(self, battle, current_pokemon, current_HP, opponent_pokemon, opponent_HP, action, score, parent_node, previous_action):
        self.battle = battle
        self.current_pokemon = current_pokemon
        self.current_HP = current_HP
        self.opponent_pokemon = opponent_pokemon
        self.opponent_HP = opponent_HP
        self.action = action
        self.score = score
        self.parent_node = parent_node
        self.children = []
        self.previous_action = previous_action


    # This function should add child nodes for every legal move and switch you can perform
    def generate_bot_moves(self):
        self.add_bot_moves()
        if not self.battle.trapped and (not isinstance(self.previous_action, Pokemon) or self.battle.active_pokemon.current_hp <= 0):
            self.add_bot_switches()
        return self.children
		
    def add_bot_moves(self):
		# Add children for every legal move
        i = 0
        if self.battle.active_pokemon is self.current_pokemon: 
            for move in self.battle.available_moves:
                if move.current_pp > 0:
                    # Generate a child node with the move as the action
                    i = i + 1
                    self.children.append(GameNode(self.battle, self.current_pokemon, self.current_HP.copy(), self.opponent_pokemon, self.opponent_HP.copy(), move, self.score, self, self.previous_action))
        else: 
            for move in self.current_pokemon.moves.values():
                if move.current_pp > 0: 
                    # Generate a child node with the move as the action
                    i = i + 1
                    self.children.append(GameNode(self.battle, self.current_pokemon, self.current_HP.copy(), self.opponent_pokemon, self.opponent_HP.copy(), move, self.score, self, self.previous_action)) 
		
		

    def add_bot_switches(self): 
        # Add children for every legal switch
        i = 0
        for switch in self.battle.team.values():
            if switch.current_hp > 0 and switch is not self.current_pokemon:
                i = i + 1
                self.children.append(GameNode(self.battle, switch, self.current_HP.copy(), self.opponent_pokemon, self.opponent_HP.copy(), switch, self.score, self, self.previous_action))
        return self.children

    # This function should add child nodes based on every move and switch the opponent can perform (that we can know about)
    # This function should take into account the actions that the player made, and calculate new estimated HP values
    def generate_opponent_moves(self): 
        self.add_opponent_moves()
        self.add_opponent_switches()
         # If there are no moves for the opponent, add a "None" action and estimate damage from the bot's attack
        if len(self.children) == 0:
            self.add_opponent_default()
        return self.children
		
    def add_opponent_moves(self):
		# Add children for every move the opponent has that we know about
        for move in self.opponent_pokemon.moves.values():
            updated_current_HP = self.current_HP.copy()
            updated_opponent_HP = self.opponent_HP.copy()
            # If opponent outspeeds (or I switched this turn), start by calculating how much damage opponent does
            if BattleUtilities.opponent_can_outspeed(self.current_pokemon, self.opponent_pokemon) or isinstance(self.action, Pokemon):
                damage = BattleUtilities.calculate_damage(move, self.opponent_pokemon, self.current_pokemon, False, False)
                damage_percentage = (damage / BattleUtilities.calculate_total_HP(self.current_pokemon)) * 100
                updated_current_HP.update({self.current_pokemon : self.current_HP[self.current_pokemon] - damage })
                # If my pokemon survives (and attacked this turn), calculcate damage
                if isinstance(self.action, Move) and updated_current_HP[self.current_pokemon] > 0:
                    damage = BattleUtilities.calculate_damage(self.action, self.current_pokemon, self.opponent_pokemon, True, True)
                    damage_percentage = (damage / BattleUtilities.calculate_total_HP(self.opponent_pokemon)) * 100
                    updated_opponent_HP.update({self.opponent_pokemon : self.opponent_HP[self.opponent_pokemon] - damage_percentage })
            else: 
                # I attack first, calculate damage
                damage = BattleUtilities.calculate_damage(self.action, self.current_pokemon, self.opponent_pokemon, True, True)
                damage_percentage = (damage / BattleUtilities.calculate_total_HP(self.opponent_pokemon)) * 100
                updated_opponent_HP.update({self.opponent_pokemon : self.opponent_HP[self.opponent_pokemon] - damage_percentage})
                # If opponent survices, calculate their damage as well
                if updated_opponent_HP[self.opponent_pokemon] > 0: 
                    damage = BattleUtilities.calculate_damage(move, self.opponent_pokemon, self.current_pokemon, False, False)
                    damage_percentage = (damage / BattleUtilities.calculate_total_HP(self.current_pokemon)) * 100
                    updated_current_HP.update({self.current_pokemon : self.current_HP[self.current_pokemon] - damage_percentage})
            self.children.append(GameNode(self.battle, self.current_pokemon, updated_current_HP, self.opponent_pokemon, updated_opponent_HP, move, self.score, self, self.previous_action))
	
    def add_opponent_switches(self):
		# Calculate all switches opponent can make
        for switch in self.battle.opponent_team.values():
            if switch is not None and switch is not self.opponent_pokemon and switch.current_hp:
                if isinstance(self.action, Move):
                    damage = BattleUtilities.calculate_damage(self.action, self.current_pokemon, switch, True, True)
                    damage_percentage = (damage / BattleUtilities.calculate_total_HP(self.opponent_pokemon)) * 100
                    updated_opponent_HP = switch.current_hp - damage_percentage
                self.children.append(GameNode(self.battle, self.current_pokemon, self.current_HP.copy(), switch, self.opponent_HP.copy(), switch, self.score, self, self.previous_action))
    
    # If there are no moves for the opponent, add a "None" action and estimate damage from the bot's attack
    def add_opponent_default(self):        
        updated_opponent_HP = self.opponent_HP.copy()
        if isinstance(self.action, Move):
            damage = BattleUtilities.calculate_damage(self.action, self.current_pokemon, self.opponent_pokemon, True, True)
            damage_percentage = (damage / BattleUtilities.calculate_total_HP(self.opponent_pokemon)) * 100
            updated_opponent_HP.update({self.opponent_pokemon : self.opponent_HP[self.opponent_pokemon] - damage_percentage})
            self.children.append(GameNode(self.battle, self.current_pokemon, self.current_HP.copy(), self.opponent_pokemon, updated_opponent_HP, None, self.score, self, self.previous_action))