# Pokémon Battle Game
A simple Pokémon battle game built using Flask for the back-end and HTML, CSS, and JavaScript for the front-end. The game uses PokeAPI to fetch Pokémon data and simulate a turn-based battle system with real-time animations, sound effects, and health bars.
[**PLAY HERE**](https://perseus.pythonanywhere.com/)

## Features
1. **Pokémon Data from PokeAPI**
   - The game pulls Pokémon data (e.g., sprites, stats, and moves) directly from PokeAPI.
   - Pokémon have accurate stats based on their base stats and are scaled to level 100.
2. **Turn-Based Battle System**
   - The battle system is turn-based, with each Pokémon taking turns attacking.
   - The faster Pokémon (based on their speed stat) moves first in each turn.
   - The player can select from four moves, and the opponent will randomly choose a move to attack.
3. **Real-Time HP Updates**
   - Both the player and opponent have visible health bars that update dynamically as damage is dealt.
   - Health bars change color based on the percentage of HP remaining (green, yellow, red).
   - HP values are properly scaled based on level 100 using standard Pokémon stat formulas.
4. **Animations and Sound Effects**
   - The opponent shakes when hit by an attack, giving the game a visual response to damage.
   - A hit sound effect plays whenever a Pokémon takes damage.
   - Background music plays during the battle and loops continuously.
   - **NOTICE**: You are to include a file named music in the root directory to store the music folders. And rename accordingly in `templates/battle.html`.
5. **Game Over Conditions**
   - The game ends when either the player’s or the opponent’s HP reaches 0.
   - The game declares whether the player has won or lost based on the final HP status of the Pokémon.
6. **Battle Log**
   - A battle log shows the most recent actions, such as which moves were used during each turn.

## How to Run the Game
**Prerequisites**
1. Python 3.x
2. Flask (`pip install flask`)
3. Requests (`pip install requests`)

**Running the Game**
1. Clone or download the repository.
2. Run the Flask app:
   ```bash
   python web_server.py
   ```
3. Navigate to `http://127.0.0.1:5000/` in your browser to start the game.

**Game Controls**
1. Start the game by visiting `/start`.
2. Select a move by clicking one of the available buttons.
3. Watch as the battle unfolds, with real-time health bar updates, animations, and sound effects.
4. When the battle ends, an alert will display the result (win or lose).

## Screenshots
![IMG1](https://imgur.com/YZu6hfR.png)
![IMG2](https://imgur.com/Jaa1stT.png)

## Features To Be Added
- Pokémon type advantages (e.g., water beats fire).
- Smarter AI for opponent actions.
- More complex move animations and status effects (e.g., burn, paralysis).

## Credits
- PokeAPI for providing Pokémon data.
- Flask for powering the back-end.
HTML, CSS, and JavaScript for the front-end logic and styling.
