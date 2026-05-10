---
# Model Card for Pokémon Battle Simulator
# Follow HuggingFace Model Card standard

# Model Details
## Model Description

<!-- Provide a longer summary of what this model is. -->

This is the backend API for a comprehensive Pokémon Battle Simulator that implements full Gen 8 mechanics, including:

- **Complete Battle System**: Full implementation of turn-based Pokémon battles with priority calculation
- **All Gen 8 Pokémon**: 905 Pokémon with accurate stats, types, and abilities
- **Comprehensive Move Pool**: 900+ moves with proper effects and mechanics
- **Advanced Abilities**: 267 abilities with complex interactions and edge cases
- **Item System**: 430+ items with various battle effects
- **Status Effects**: Complete status condition system (burn, poison, paralysis, sleep, freeze, toxic)
- **Strategic Depth**: Support for competitive movesets, EV distributions, natures, and held items
- **AI Opponent**: Intelligent battle AI that makes strategic decisions

## Model Type

- **Architecture**: FastAPI REST API + Python Backend
- **Framework**: FastAPI, Python 3.11
- **Task**: Game Engine / Battle Simulator

## Intended Use

This backend powers the Pokémon Battle Simulator frontend, enabling:

- Real-time battle simulations
- AI-powered opponent battles
- Training and testing competitive movesets
- Educational tool for understanding Pokémon mechanics
- Game development reference implementation

## Out-of-Scope Use Cases

- This is not a real Pokémon game
- Not affiliated with The Pokémon Company
- Cannot be used for commercial purposes
- Educational and non-commercial use only

---

# Uses

## Direct Use

The API can be accessed directly with HTTP requests:

```bash
# Start a new battle
POST /api/battles/start
{
  "player_pokemon": {
    "name": "Charizard",
    "moves": ["Flamethrower", "Dragon Claw", "Earthquake", "Swords Dance"],
    "level": 50
  }
}

# Make a move
POST /api/battles/{battle_id}/move
{
  "move_index": 0
}

# Switch Pokémon
POST /api/battles/{battle_id}/switch
{
  "pokemon_index": 1
}
```

## Downstream Use Cases

The primary downstream use is the [Pokémon Battle Simulator Frontend](https://github.com/perseuskyogre/Pokemon), a Next.js web application that provides an interactive UI for battles.

---

# How to Get Started

## Installation

### Docker (Recommended)

```bash
docker build -t pokemon-battle-simulator .
docker run -p 7860:7860 pokemon-battle-simulator
```

### Local Installation

```bash
cd backend
chmod +x run.sh
./run.sh
```

Or on Windows:
```batch
cd backend
run.bat
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:7860/docs`
- **ReDoc**: `http://localhost:7860/redoc`
- **OpenAPI Schema**: `http://localhost:7860/openapi.json`

## Example Requests

### Get All Pokémon

```bash
curl http://localhost:7860/api/pokemon
```

### Start a Battle

```bash
curl -X POST http://localhost:7860/api/battles/start \
  -H "Content-Type: application/json" \
  -d '{
    "player_pokemon": {
      "name": "Pikachu",
      "moves": ["Thunderbolt", "Thunder Wave", "Quick Attack", "Iron Tail"],
      "level": 50
    }
  }'
```

---

# Training Data

The simulator uses official Pokémon data from:

- **Pokédex**: Gen 8 official stats and movepools
- **Moves Database**: Complete move mechanics and effects
- **Abilities Database**: 267 abilities with interaction rules
- **Items Database**: 430+ items with battle effects

All data is sourced from official Pokémon games and databases.

---

# Model Performance

The model/engine is thoroughly tested with:

- ✅ 267 ability implementations tested
- ✅ 900+ move mechanics validated
- ✅ 430+ items properly implemented
- ✅ All status effects and conditions
- ✅ Complex interaction edge cases

See [ABILITY_TESTING.md](../test/ABILITY_TESTING.md) and [MOVE_TESTING.md](../test/MOVE_TESTING.md) for detailed test results.

---

# Limitations

- **Rate Limiting**: No built-in rate limiting (implement at proxy level)
- **Persistence**: Battles are not persisted between server restarts
- **Multiplayer**: Current implementation is single-player AI battles (multiplayer support coming)
- **Real-time**: Not optimized for extremely high-frequency requests
- **Statistics**: Limited game history/statistics storage

---

# Environmental Impact

- **Model Size**: ~50MB uncompressed (lightweight)
- **Inference Speed**: <100ms per battle turn on CPU
- **Memory Usage**: ~500MB running, <2GB peak
- **CPU Requirements**: Any modern CPU (ARM/x86_64 compatible)

---

# Bias, Risks, and Limitations

## Bias

The Pokémon data reflects the official games. Some Pokémon/moves may have balance disparity.

## Risks

- The API could be misused for game hacking tools
- Should not be used in commercial Pokémon games without permission

## Limitations

- Mechanics are Gen 8 based (Sword/Shield)
- Some rare mechanics may have edge cases not fully implemented
- Competitive metagame changes not reflected (static data)

---

# Recommendations

Users should:

- Use this for educational purposes only
- Respect Pokémon intellectual property
- Consider rate limiting in production
- Cache API responses where possible
- Run in a containerized environment

---

# Citation

```bibtex
@software{pokemon_battle_simulator,
  title = {Pokémon Battle Simulator},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/perseuskyogre/Pokemon},
  note = {Educational AI-powered Pokémon battle engine}
}
```

---

# How to Contribute

To contribute improvements:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with test coverage
4. Update relevant documentation

---

# License

MIT License - See LICENSE file for details

---

# Acknowledgments

- The Pokémon Company for the original games and mechanics
- FastAPI framework and community
- Contributors and testers
