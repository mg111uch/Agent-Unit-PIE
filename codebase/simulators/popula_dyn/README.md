# Population Dynamics Simulation

A comprehensive simulation system modeling human societies with multiple agent types, featuring a real-time playable browser game. Target of this project is to make simulation as realistic as possible by taking population growth data from real human history starting from the primitive agricultutal societies to the complexities and technologies of modern world.

## 🎯 Overview

This project simulates the dynamics of agricultural populations using agent-based modeling. It includes farmers, healers, toolmakers, and traders interacting in a spatial environment, demonstrating concepts like Malthusian traps, economic specialization, and population dynamics.

## 🛠️ Technology Stack

### Backend
- **Python 3.12**: Core simulation logic
- **NumPy**: Numerical computations and random number generation
- **Pandas**: Data collection and analysis
- **Matplotlib**: Static visualization and plotting
- **FastAPI**: REST API and WebSocket server
- **Uvicorn**: ASGI server for FastAPI

### Frontend
- **PixiJS**: 2D graphics rendering for game visualization
- **HTML5/CSS3**: UI styling and layout
- **JavaScript (ES6+)**: Game logic and WebSocket communication
- **WebSockets**: Real-time bidirectional communication

### Architecture
- **Agent-Based Modeling**: Mesa-inspired framework
- **Spatial Grid**: Toroidal multi-agent grid system
- **Real-time Updates**: WebSocket broadcasting for live simulation

## 🚀 Getting Started

### Prerequisites
```bash
# Activate conda environment
cd python/Popula
eval "$(conda shell.bash hook)" && conda activate myenv

# Install dependencies
pip install fastapi uvicorn pydantic
```

### Running the System

1. **Start the Server:**
```bash
python server.py
```

2. **Access Interfaces:**
   - **Simulation Game**: http://localhost:8000/game
   - **API Documentation**: http://localhost:8000/docs

## 🎮 Game Controls

### Simulation Controls
- **Start**: Begin continuous simulation with real-time updates
- **Stop**: Pause the simulation
- **Reset**: Clear all agents and reset to initial state
- **Step**: Advance simulation by one year manually

### Parameter Controls
- **Initial Population**: Set starting farmer count (100-5000)
- **Birth Rate**: Probability of successful mating (0-0.2)
- **Death Rate**: Base mortality probability (0-0.1)
- **Healers**: Number of healer agents (0-50)
- **Toolmakers**: Number of toolmaker agents (0-50)
- **Traders**: Number of trader agents (0-50)
- **Grid Size**: World dimensions (10x10 to 100x100)

### Visual Elements
- **Green squares**: Fertile land patches
- **Red circles**: Farmers
- **Purple circles**: Healers
- **Orange circles**: Toolmakers
- **Teal circles**: Traders

## 📈 Real-time Statistics

The game displays live metrics:
- **Year**: Current simulation time
- **Population**: Active farmer count
- **Total Wealth**: Aggregate economic value
- **Average Skill**: Mean farming efficiency
- **Births/Deaths**: Cumulative counts per year
- **Specialist Counts**: Current numbers of each agent type


## 🏗️ Project Structure

```
python/Popula/
├── README.md                # This documentation
├── feature_list.md                  # Todo list of features to be added
├── constants.py             # Simulation parameters
├── base_classes.py          # Core agent and grid classes
├── agents.py                # Agent implementations
├── model.py                 # Agricultural model
├── simulation.py            # Simulation runner and plotting
├── PopuDyn.py               # Main entry point for simulation
├── devpt_log.md             # Log of features addition in project
├── Insight.md               # Insight from analysing the simulation plot
├── simulation_game.py       # Game server entry point 
├── simulation_plot.png      # Plot obtained after running the main simulation
├── static/
│   └── game.html           # Simulation game script
└── DevptPhases.md               # Development phases
```

## 🎯 Agent Behaviors

### Farmers
- **Movement**: Random adjacent cell movement
- **Harvesting**: Collect crops based on skill and land fertility
- **Consumption**: Use wealth for survival
- **Mating**: Reproduce with nearby fertile partners
- **Death**: Age and starvation-based mortality

### Specialists
- **Healers**: Reduce farmer death probability for payment
- **Toolmakers**: Produce and sell tools to improve farmer skills
- **Traders**: Facilitate wealth transfer between agents

## 🔬 Simulation Mechanics

### Economic System
- Farmers earn wealth through harvesting
- Specialists provide services for payment
- Wealth affects survival and reproduction
- Tools increase farming efficiency over time

### Spatial Dynamics
- Toroidal grid prevents edge effects
- Vision radius limits agent interactions
- Random movement with fertility preferences (TODO)

### Population Control
- Age-based fertility windows
- Starvation multipliers on death rates
- Maximum age limits
- Specialist healing modifiers

## 🎨 Visualization Features


### Game Interface
- Real-time grid rendering
- Live statistics dashboard
- Parameter adjustment sliders
- WebSocket synchronization
- Responsive design

## 🚀 Advanced Features


### Real-time Collaboration
- WebSocket broadcasting
- Multi-client synchronization
- Parameter sharing
- Live result comparison

## 📝 API Endpoints

### REST API
- `GET /game`: Simulation game page

### Simulation API
- `POST /simulation/start`: Start simulation
- `POST /simulation/stop`: Stop simulation
- `POST /simulation/reset`: Reset simulation
- `POST /simulation/step`: Single step
- `POST /simulation/params`: Update parameters
- `GET /simulation/state`: Get current state

### WebSocket
- `ws://localhost:8000/ws/simulation`: Real-time updates

## 🔧 Development Notes

### Performance Considerations
- Grid rendering optimized for 100x100 maximum
- WebSocket broadcasting every 1 second

### Extensibility
- Modular agent system for easy addition
- Parameter-driven configuration
- Plugin-ready architecture

### Future Enhancements
- Advanced movement algorithms (fertility-based)
- More agent types and interactions
- Multiplayer collaboration
- Historical data persistence
- Advanced visualization modes

## 📚 Educational Value

This simulation demonstrates:
- **Economic Theory**: Supply/demand, specialization
- **Population Dynamics**: Malthusian constraints
- **Agent-Based Modeling**: Emergent behavior
- **Spatial Analysis**: Geographic influences
- **Real-time Systems**: WebSocket architecture

## 🤝 Contributing

The modular architecture makes it easy to:
- Add new agent types
- Implement different movement strategies
- Create new visualization modes
- Add multiplayer features

## 📄 License

This project is open-source and available for educational and research purposes.