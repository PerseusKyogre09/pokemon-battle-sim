---
title: Pokemon Battle Sim
emoji: ⚡
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# ⚡ Pokémon Battle Simulator

A professional-grade, feature-rich Pokémon battle simulator built with **FastAPI**, **Next.js**, and **Supabase**. This application implements authentic turn-based battle mechanics inspired by the core series games and Pokémon Showdown.

## 🚀 Quick Start (Local)

To run both the backend and frontend simultaneously, use the Python start script:

```bash
python start.py
```

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend**: [http://localhost:7860](http://localhost:7860)

If you only want to run the backend:
```bash
cd backend
python run_backend.py
```

## 🎮 Features
- **Authentic Battle Engine**: Turn-based logic with priority systems, status effects, and weather.
- **Strategic Movesets**: Competitive sets fetched from a curated database.
- **Dynamic Sprites**: Gen 5 animated pixel art and 3D models support.
- **Modern UI**: Sleek, responsive interface built with Next.js and Tailwind CSS.
- **Audio Integration**: Authentic cries and background music served via Supabase.

## 🛠️ Deployment
- **Frontend**: Hosted on **Vercel** for high-performance edge delivery.
- **Backend**: Hosted on **Hugging Face Spaces** using Docker for scalable API hosting.

## 🙏 Credits
- [PokeAPI](https://pokeapi.co/) - Comprehensive Pokémon data.
- [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) - Battle logic and moveset inspiration.
- Pokémon and all related content © Nintendo, Game Freak, and The Pokémon Company.
