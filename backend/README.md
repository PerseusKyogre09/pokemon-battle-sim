# Backend Structure

The backend has been reorganized into a clean, modular structure for easier maintenance and deployment.

## Directory Structure

```
backend/
├── src/                      # Main source code
│   ├── __init__.py
│   ├── systems/             # Game systems (abilities, items, priority, status effects)
│   │   ├── __init__.py
│   │   ├── ability_system.py
│   │   ├── item_system.py
│   │   ├── priority_system.py
│   │   └── status_effects.py
│   │
│   ├── models/              # Core data models
│   │   ├── __init__.py
│   │   ├── pokemon.py
│   │   ├── move.py
│   │   └── moveset.py
│   │
│   ├── utils/               # Utility functions and data loading
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   ├── pokemon_utils.py
│   │   └── fetcher.py
│   │
│   └── core/                # Core game logic and API server
│       ├── __init__.py
│       ├── game.py
│       ├── ai.py
│       └── fastapi_server.py
│
├── data/                    # Data files
│   ├── datasets/           # Moves, abilities, items, etc.
│   ├── pokemon_ids.json
│   ├── gen8_stats_sets.json
│   └── all_pokemon_names.json
│
├── moves/                   # Legacy moves module
│   └── moves.py
│
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── Procfile                # Deployment configuration
├── runtime.txt             # Runtime specification
└── README.md               # This file
```

## Module Organization

### Systems (`src/systems/`)
Game mechanics and rule enforcement:
- **ability_system.py**: Pokémon ability implementations
- **item_system.py**: Item effects and mechanics
- **priority_system.py**: Move priority calculations
- **status_effects.py**: Status condition handling

### Models (`src/models/`)
Core data structures:
- **pokemon.py**: Pokémon class definition and stat calculations
- **move.py**: Move mechanics and effects
- **moveset.py**: Moveset management and strategies

### Utils (`src/utils/`)
Utilities and helpers:
- **data_loader.py**: Loads JSON data files (moves, abilities, items, etc.)
- **pokemon_utils.py**: Pokémon-related utility functions
- **fetcher.py**: External data fetching utilities

### Core (`src/core/`)
Game engine and API:
- **game.py**: Battle engine and game logic
- **ai.py**: AI opponent logic
- **fastapi_server.py**: REST API server

## Running the Backend

### Development
```bash
cd backend
pip install -r requirements.txt
python src/core/fastapi_server.py
```

### Docker
```bash
docker build -f backend/Dockerfile -t pokemon-backend .
docker run -p 8000:8000 pokemon-backend
```

## Data Files

Data files are located in `backend/data/`:
- `datasets/`: TypeScript/JSON data files for moves, abilities, items, learnsets, and type effectiveness
- `pokemon_ids.json`: Pokémon name to ID mappings
- `gen8_stats_sets.json`: Generation 8 stat distributions
- `all_pokemon_names.json`: Complete Pokémon name list

## Deployment

This modular structure makes it easy to deploy to platforms like HuggingFace:
- All backend code is contained in `backend/src/`
- All data is in `backend/data/`
- Configuration files are in `backend/`
- Simply push the entire `backend/` directory for clean deployments
