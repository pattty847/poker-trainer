# Poker Trainer MVP

An AI-powered poker training application that provides real-time strategy guidance with instant heuristic actions and streamed reasoning. Learn optimal poker play through interactive practice against AI opponents with personalized coaching.

## Features

- **Instant Action + Streamed Reasoning**: Never wait for AI - heuristic actions execute immediately while detailed reasoning streams in real-time
- **Multiple Coaching Personas**: Choose from different teaching styles (Math Nerd, Beginner-Friendly, etc.)
- **Skill-Level Filtering**: Adjust complexity of explanations based on your experience level
- **Hand Review**: Analyze completed hands with alternate line suggestions and EV estimates
- **Range Visualization**: See estimated ranges for yourself and opponents in real-time
- **Reasoning Continuity**: AI maintains consistent strategy across all streets of a hand

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PokerKit** - Poker game engine for heads-up play
- **SSE (Server-Sent Events)** - Real-time streaming of AI reasoning
- **SQLite** - Session persistence and hand history

### Frontend
- **React** + **TypeScript** - UI framework
- **Vite** - Fast development server and build tool
- **Zustand** - Lightweight state management
- **EventSource** - SSE client with automatic retry

## Project Structure

```
poker-player/
├── backend/
│   └── app/
│       ├── routes/          # API endpoints
│       │   ├── game.py      # Game management
│       │   ├── reason.py    # SSE reasoning stream
│       │   ├── coach.py     # Interactive coaching
│       │   ├── review.py    # Hand review
│       │   └── range.py     # Range estimation
│       ├── domain/          # Core game logic
│       │   ├── game_manager.py
│       │   ├── poker_adapter.py
│       │   ├── heuristics.py
│       │   └── board_features.py
│       ├── reasoning/       # LLM integration
│       │   ├── base.py
│       │   └── prompts/
│       └── core/            # Infrastructure
│           ├── config.py
│           ├── sse.py
│           └── deps.py
└── frontend/
    └── src/
        ├── lib/
        │   ├── api.ts       # REST client
        │   ├── sse.ts       # SSE subscription
        │   └── store.ts     # State management
        └── components/      # React components
```

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- uv (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd poker-player
```

2. Set up Python backend:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Set up frontend:
```bash
cd frontend
npm install
```

### Running the Application

1. Start the backend server:
```bash
uvicorn backend.app.main:app --reload
```

Backend will run at http://localhost:8000

2. In a separate terminal, start the frontend:
```bash
cd frontend
npm run dev
```

Frontend will run at http://localhost:5173

## API Endpoints

### Game Management
- `POST /api/game/new` - Create new poker session
- `POST /api/game/action` - Apply player action
- `GET /api/game/state` - Get current game state

### AI Reasoning
- `GET /api/reason/stream` - SSE stream of AI reasoning (supports skill filtering)

### Coaching & Review
- `POST /api/coach/ask` - Ask coaching questions
- `GET /api/review/hand` - Get hand review with alternate lines
- `GET /api/range/estimate` - Get range estimation grid

### Health
- `GET /health` - Server health check

## Development Roadmap

### Phase 1: MVP (Current)
- [x] SSE streaming infrastructure
- [x] Basic game state management
- [x] Heads-up poker support
- [ ] Deterministic heuristics (preflop/postflop)
- [ ] PokerKit integration
- [ ] Skill-level tagging and filtering
- [ ] Basic coaching personas

### Phase 2: Enhanced Features
- [ ] LLM integration (Claude/OpenAI)
- [ ] Hand review with alternate lines
- [ ] Range estimation with ML model
- [ ] Session persistence
- [ ] Multi-street reasoning continuity

### Phase 3: Advanced
- [ ] Fine-tuned local LLM (QLoRA)
- [ ] Advanced range estimation (MLP)
- [ ] Multi-way pots support
- [ ] Tournament mode

## Design Principles

1. **Latency First**: Instant heuristic actions, reasoning streams asynchronously
2. **Deterministic Core**: Heuristics are reproducible and tested
3. **Reasoning Consistency**: AI maintains coherent strategy across streets
4. **Progressive Complexity**: Adapt explanations to user skill level
5. **Graceful Degradation**: System remains functional even if LLM fails

## License

MIT

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.
