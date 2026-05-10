import random
from data_loader import data_loader

class BattleAI:
    def __init__(self):
        pass

    def select_move(self, ai_pokemon, player_pokemon, weather='none'):
        if not ai_pokemon or not player_pokemon:
            return None, None

        moves = ai_pokemon.moves
        if not moves:
            return None, None

        scored_moves = []
        for move_name, move in moves.items():
            if move.pp <= 0:
                continue
            
            score = self.score_move(move, ai_pokemon, player_pokemon, weather)
            scored_moves.append((move_name, move, score))

        if not scored_moves:
            return None, None

        scored_moves.sort(key=lambda x: x[2], reverse=True)
        top_score = scored_moves[0][2]
        
        if top_score <= 1:
            selected_move_name, selected_move, _ = scored_moves[0]
            return selected_move_name, selected_move

        threshold = 0.9 * top_score
        best_moves = [m for m in scored_moves if m[2] >= threshold]
        
        selected_move_name, selected_move, _ = random.choice(best_moves)
        return selected_move_name, selected_move

    def select_switch(self, team, player_pokemon):
        """Select a pokemon to switch in from the team."""
        available = [p for p in team if not p.is_fainted()]
        if not available:
            return None
        
        # Simple heuristic: pick the one with the best type advantage or just random
        # For now, let's just pick the one with the best effectiveness against player_pokemon
        best_score = -1
        best_mon = None
        
        for p in available:
            score = 0
            # Check type advantage
            for p_type in p.types:
                for player_type in player_pokemon.types:
                    score += data_loader.get_type_effectiveness(p_type, player_type)
            
            if score > best_score:
                best_score = score
                best_mon = p
                
        return team.index(best_mon) if best_mon else None

    def score_move(self, move, attacker, defender, weather):
        score = 0
        
        if move.category in ['physical', 'special']:
            base_power = move.power
            if base_power == 0:
                base_power = 40
            
            effectiveness = 1.0
            attacker_types = [t.lower() for t in attacker.types]
            defender_types = [t.lower() for t in defender.types]
            
            for d_type in defender_types:
                effectiveness *= data_loader.get_type_effectiveness(move.type, d_type)
            
            stab = 1.5 if move.type.lower() in attacker_types else 1.0
            
            if move.category == 'physical':
                atk = attacker.attack
                dfn = defender.defense
            else:
                atk = attacker.special_attack
                dfn = defender.special_defense
                
            weather_mult = 1.0
            if weather == 'raindance':
                if move.type == 'water': weather_mult = 1.5
                elif move.type == 'fire': weather_mult = 0.5
            elif weather == 'sunnyday':
                if move.type == 'fire': weather_mult = 1.5
                elif move.type == 'water': weather_mult = 0.5
            elif weather == 'hail' and move.type == 'ice':
                weather_mult = 1.5
                
            damage_score = (base_power * effectiveness * stab * weather_mult * (atk / max(1, dfn)))
            
            acc = move.accuracy if isinstance(move.accuracy, int) else 100
            damage_score *= (acc / 100.0)
            
            score += damage_score

            if damage_score >= defender.current_hp:
                score += 1000

        elif move.category == 'status':
            if move.is_healing_move:
                hp_percent = attacker.current_hp / attacker.max_hp
                if hp_percent < 0.3:
                    score += 400
                elif hp_percent < 0.5:
                    score += 200
                elif hp_percent > 0.8:
                    score -= 100
            
            if move.stat_modifications and move.targets_self:
                hp_percent = attacker.current_hp / attacker.max_hp
                if hp_percent > 0.6:
                    score += 150
                else:
                    score += 50
            
            if hasattr(move, 'data') and move.data.get('status'):
                status_type = move.data.get('status')
                
                if defender.major_status:
                    score -= 1000
                
                defender_types = [t.lower() for t in defender.types]
                if status_type == 'brn' and 'fire' in defender_types:
                    score -= 1000
                elif status_type == 'par' and 'electric' in defender_types:
                    score -= 1000
                elif status_type == 'psn' and ('poison' in defender_types or 'steel' in defender_types):
                    score -= 1000
                elif status_type == 'tox' and ('poison' in defender_types or 'steel' in defender_types):
                    score -= 1000
                elif status_type == 'slp' and ('grass' in defender_types and move.flags.get('powder')):
                    score -= 1000
                
                if score >= 0:
                    if status_type == 'slp': score += 400
                    elif status_type == 'brn' and defender.attack > defender.special_attack: score += 300
                    elif status_type == 'par': score += 250
                    else: score += 200
            
            if move.id in ['protect', 'spikyshield', 'banefulbunker', 'kingsshield', 'obstruct', 'burningbulwark', 'silktrap']:
                if attacker.consecutive_stalling_moves == 0:
                    score += 100
                else:
                    score -= 1000

        if hasattr(move, 'data') and move.data.get('secondary'):
            secondary = move.data.get('secondary')
            chance = secondary.get('chance', 0)
            if chance > 0:
                score += (chance / 100.0) * 50

        if move.priority > 0:
            if defender.current_hp < defender.max_hp * 0.2:
                score += 200
            if attacker.current_hp < attacker.max_hp * 0.2:
                score += 100

        return max(1, score)
