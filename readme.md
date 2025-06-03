# Pokémon Battle Simulator

A feature-rich Pokémon battle simulator built with Flask, HTML, CSS, and JavaScript. This web application allows players to engage in strategic turn-based battles with authentic Pokémon mechanics, including type advantages, strategic movesets, and dynamic battle animations.

[![Twitter Follow](https://img.shields.io/twitter/follow/KyogrePerseus)](https://twitter.com/KyogrePerseus)
[![License](https://img.shields.io/badge/license-MIT-purple)](https://github.com/PersesKyogre09/pokemon-battle-sim/blob/main/LICENSE)

<p align="center">
  <a href="https://pokemon-battle-sim.onrender.com/"><img src="https://img.shields.io/badge/Live%20Demo- Pokémon%20Battle%20Simulator-blue?style=for-the-badge" alt="Live Demo"></a>
</p>


## 🎮 Features

### 🎯 Core Gameplay
- **Authentic Pokémon Battles**: Experience turn-based battles with official Pokémon mechanics
- **Strategic Movesets**: Pokémon come with optimized movesets based on their type and abilities
- **Type Advantages**: Full implementation of Pokémon type effectiveness (super effective, not very effective, no effect)
- **STAB (Same Type Attack Bonus)**: Moves matching the Pokémon's type deal 1.5x damage
- **Critical Hits**: Random critical hits add excitement to battles
- **Damage Variance**: Moves deal 85-100% of their maximum damage

### 🖼️ Visuals & Audio
- **Animated Sprites**: Gen 5 animated sprites for authentic Pokémon appearance
- **Dynamic Health Bars**: Color-changing HP bars based on remaining health
- **Battle Animations**: Visual feedback for attacks, damage, and status effects
- **Sound Effects**: Authentic Pokémon cries and battle sounds
- **Background Music**: Immersive battle music (add your own music files to the `music` directory)

### ⚙️ Technical Features
- **Responsive Design**: Works on desktop and tablet devices
- **Real-time Updates**: Dynamic UI updates without page refreshes
- **Battle Log**: Detailed log of all battle events
- **Scalable Architecture**: Clean separation of concerns between frontend and backend

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, or Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PersesKyogre09/pokemon-battle-sim.git
   cd pokemon-battle-sim
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python web_server.py
   ```

4. **Open in your browser**
   Visit `http://127.0.0.1:5000/` to start playing!

## 🎮 How to Play

1. **Start a Battle**
   - Visit the home page and click "Start Battle"
   - Choose your Pokémon from the selection screen
   - The game will automatically select an opponent for you

2. **Battle Controls**
   - Click on a move button to attack
   - Watch the battle log for turn-by-turn updates
   - Monitor HP bars to track battle progress

3. **Winning the Game**
   - Reduce your opponent's HP to zero to win
   - If your Pokémon faints, you lose the battle

## 🛠️ Project Structure

```
pokemon-battle-sim/
├── data/                  # Data files and type effectiveness charts
├── music/                 # Background music (add your own files here)
├── static/
│   ├── css/              # Stylesheets
│   ├── js/               # Frontend JavaScript
│   └── sounds/           # Sound effects
├── templates/            # HTML templates
│   ├── battle.html       # Main battle interface
│   └── index.html        # Home/selection screen
├── data_loader.py        # Handles loading Pokémon and move data
├── game.py               # Core game logic
├── move.py               # Move class and damage calculation
├── moveset.py            # Strategic moveset generation
├── pokemon.py            # Pokémon class and battle logic
└── web_server.py         # Flask web server and routes
```

## 📝 Notes

- The game uses PokeAPI to fetch Pokémon data, so an internet connection is required
- For offline play, you'll need to implement a local cache of the required data
- Add your own music files to the `music` directory and update the references in `templates/battle.html`

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Screenshots
<p align="center">
  <img src="https://github.com/user-attachments/assets/91142e9c-d96a-4640-87a7-e8b4da0d9ee6" width="49.5%">
  <img src="https://github.com/user-attachments/assets/78c61934-512c-4c5e-b0fe-47e92e3ece86" width="49.5%">
  <br>
  <img src="https://github.com/user-attachments/assets/48891598-009e-45ba-9d28-acece71032e8" width="49.5%">
  <img src="https://github.com/user-attachments/assets/ec4fec02-3e02-495c-8c31-adb181394c82" width="49.5%">
</p>

## 🙏 Credits

- [PokeAPI](https://pokeapi.co/) for the comprehensive Pokémon data
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) for the moves, typechart logic, and learnsets datasets (MIT license)
- Pokémon and all related content &copy; Nintendo, Game Freak, and The Pokémon Company

<div align="center">
  <a href="https://twitter.com/KyogrePerseus"><img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/KyogrePerseus"></a>
  <a href="https://github.com/PersesKyogre09/pokemon-battle-sim/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache2.0-purple"></a>
</div>
