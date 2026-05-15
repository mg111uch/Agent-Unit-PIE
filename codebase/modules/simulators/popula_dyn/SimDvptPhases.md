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

---

### Detailed Plan for Building a Realistic Population Dynamics Model in Python

#### Phase 2: Controllable Vital Rates and Individual Variation
**Objectives**: Make the model tunable via script parameters. Introduce variability for realism (e.g., not all agents reproduce equally).

**Key Components**:
- Parameter controls: Script args for birth/death rates, fertility window, litter size (1–2 children max).
- Individual traits: Add `fertility` (0–1 float, normally distributed) and `lifespan` (random from distribution, e.g., Weibull for human-like aging).
- Death causes: Categorize (e.g., age-related vs. random accidents) with adjustable probabilities.
- Gender balance: Track ratios; auto-adjust if skewed (e.g., via higher fertility in underrepresented gender).

#### Phase 3: Environmental Conditions
**Objectives**: Integrate external factors affecting survival/reproduction, making the world dynamic.

**Key Components**:
- Grid world: Spatialize population on a 2D grid (e.g., 100x100 cells) for resource distribution.
- Environment layers: Temperature, food scarcity (random yearly fluctuations, e.g., droughts reduce birth by 20%). Agents migrate to better cells if local conditions worsen.
- Adaptation: Agents gain `adaptability` trait; harsher environments select for higher adaptability over generations.
- Carrying capacity: Logistic growth limit based on grid resources (e.g., max pop per cell).

**Data Structures**:
- `Environment` class: 2D NumPy array for conditions (e.g., food_level[ x ][ y ]).
- Extend `Agent`: Add `location` (x,y tuple), `migration_threshold` (e.g., if local death_rate > 0.05, move).

**Simulation Loop**:
- Yearly: Update environment (e.g., random weather) → Adjust local rates → Simulate aging/deaths/births per cell → Migration (random walk to adjacent cells).

**Validation/Testing**:
- Scenarios: Famine year → pop drop; mild climate → steady growth. Visualize heatmaps of pop density.

#### Phase 4: Economic Parameters
**Objectives**: Add resource gathering and trade to influence productivity and population.

**Key Components**:
- Resources: Food, tools (gathered via `labor_skill` trait). Base productivity per agent (e.g., 1 unit food/year).
- Economy model: Simple supply-demand; scarcity raises death rates, abundance boosts births.
- Trade: Agents in same cell exchange resources (random bartering).
- Productivity metric: Total resources produced/year, tied to pop size and skills (skills improve with age/experience).

**Data Structures**:
- `Resource` class: Types like food (perishable) vs. tools (durable).
- Extend `Environment`: Resource grids updated by agent actions.
- Extend `Agent`: Add `resources_inventory` (dict), `labor_skill` (0–1, inherited + learned).

**Simulation Loop**:
- Per year: Agents gather (success ~ skill * local resources) → Consume (unmet needs → death) → Trade/mate → Log total productivity.

**Validation/Testing**:
- Growth curves: High resources → pop boom; depletion → collapse. Track GDP-like metric (resources * pop efficiency).

#### Phase 5: Social Structures (Communities and Cities)
**Objectives**: Enable grouping, leading to emergent societies.

**Key Components**:
- Grouping: Agents form `Community` if >50 in a cell (threshold param). Communities have shared resources/pools.
- City formation: Communities >500 merge into `City` with bonuses (e.g., +10% productivity from specialization).
- Leadership: Random `leader` per group; influences decisions (e.g., migration votes).
- Cultural traits: Groups develop `culture_score` (e.g., cooperation vs. isolationism), affecting trade/fusion rates.

**Data Structures**:
- `Group` class (inherits Community/City): Members list, shared_resources, culture.
- Extend `Agent`: `group_id`, `loyalty` (0–1).

**Simulation Loop**:
- After individual actions: Check for group formation/merges → Group-level decisions (e.g., resource allocation) → Update logs.

**Validation/Testing**:
- Emergent behavior: Isolated pops → small villages; dense → megacities. Simulate 200 years for city counts.

#### Phase 6: Conflict, Expansion, and Civilization
**Objectives**: Add competition for full realism, evolving to civilizations.

**Key Components**:
- Conflict: Groups fight over resources/cells (probability ~ size difference; winner absorbs losers, casualties via death rate spike).
- Expansion: Cities colonize empty cells (success ~ military_tech, a new trait).
- Civilization stage: >10 cities → `Civilization` entity with tech tree (e.g., unlock irrigation → +birth rate).
- Diplomacy: Alliances via trade; wars via betrayal (random events).
- Endgame: Global metrics like empire size, tech level.

**Data Structures**:
- `Civilization` class: City list, tech_tree (dict of unlocked nodes).
- Extend `Group`: `military_strength` (pop * skill), `diplomacy_status` (dict of relations).

**Simulation Loop**:
- Late in year: Resolve conflicts/diplomacy → Expansion attempts → Tech progress (e.g., R&D pool from productivity).

**Validation/Testing**:
- War scenarios: Aggressive civs dominate. Compare to historical patterns (e.g., Roman expansion).

#### Phase 7: Visualization and Output
**Objectives**: Generate graphs for analysis.

**Key Components**:
- Metrics tracking: Annual DataFrame with columns: year, total_pop, male/female, births/deaths, productivity, city_count, civ_count.
- Graphs: Line plots for pop/productivity over time; heatmaps for spatial distribution; pie charts for resource allocation.
- Export: Save sim data as CSV; interactive plots via Plotly if desired.

### Adapting to a Game: Civilization-Style Control

**Incorporating Civ-Like Features** (Scaled to Your Model):
- **Tech Tree** (from Civ): Unlock via productivity points (Phase 6). Player chooses branches (e.g., Agriculture → +birth rate; Military → better fights). Include 20–30 nodes, like Writing (boosts trade).
- **Resources & Economy** (from Civ/AoE): Hex/tile map with yields (food, production). Player allocates (e.g., build farms → env bonus). Track happiness (low → rebellions, pop loss).
- **Cities & Units** (from Civ): Your cities as hubs; spawn "units" (agents with roles: farmers, warriors). Player designs builds (e.g., walls → defense +20%).
- **Diplomacy & Events** (from Humankind): Random events (plagues, discoveries). Player negotiates alliances (set relations sliders) or declares war (boost military params).
- **Victory Paths** (from Civ): Domination (conquer all), Cultural (high culture_score), Economic (max productivity graphs).
- **Player Agency**: Mid-game interventions (e.g., "miracle" boosts birth rate). Multiplayer: Compete by controlling rival civs' params.
- **UI/Polish**: Zoomable map (Matplotlib or Pygame), scenario editor (save/load configs), achievements (e.g., "Sustainable Utopia" for stable pop 1000 years).

- ---------------------------------------------------

### Recommendations for Feature and Agent Upgrades
To enhance realism, focus on emergent behaviors like specialization, trade networks, conflict, and environmental feedback. Below are targeted upgrades, prioritized by impact on realism (high/medium/low) and ease of implementation (easy/medium/hard).

| Upgrade Category | Specific Recommendation | Rationale for Realism | Priority/Ease |
|------------------|--------------------------|-----------------------|---------------|
| **Resource Dynamics** | Introduce seasonal crop yields (e.g., multiplier based on sine wave for summer/winter) and soil degradation (fertility decreases with over-harvesting, recoverable via fallow periods or fertilizers). | Prevents constant regrowth; mirrors real agriculture's vulnerability to climate and overuse, leading to famines or migrations. | High/Easy |
| **Movement & Decision-Making** | Upgrade `move()` in FarmerAgent to prospecting: scan for fertility/wealth gradients within vision radius, move toward better patches if wealth < threshold. Add pathfinding (A* via NetworkX). | Agents act rationally (e.g., migration to fertile lands), creating settlements and trade routes organically. | High/Medium |
| **Social/Economic Layers** | Add inheritance: On death, wealth/skill transfers to children (weighted by gender/age). Implement markets: Agents barter based on supply/demand (e.g., excess crops for tools). | Builds family lineages, inequality, and economic cycles; explains wealth concentration and class emergence. | High/Medium |
| **Environmental Feedback** | Add weather events (random droughts/floods reducing fertility grid-wide) and pollution (toolmaking/healing produces waste that lowers nearby fertility). | Introduces shocks like historical plagues or industrial pollution, forcing adaptation or collapse. | Medium/Medium |
| **Specialist Evolution** | Allow specialists to reproduce (low birth rate, offspring inherit role with mutation chance to switch roles). Add death mechanics for them (e.g., overwork if too many clients). | Prevents static counts; enables guilds or dynasties, with roles emerging based on fitness. | Medium/Hard |
| **Conflict & Cooperation** | Add raiding: Low-wealth agents steal from neighbors with probability based on power imbalance (skill x population). Cooperation: Form temporary alliances for mega-harvests. | Captures tribal wars or alliances; realism from resource scarcity driving violence/cooperation. | Low/Hard |

These upgrades would amplify the Malthusian dynamics while adding resilience pathways (e.g., tech diffusion via tools reduces death rates).

### Suggested New Agents
To expand beyond basic roles, introduce agents that foster complexity like technology, governance, and ecology. Start with 5-10 initial instances each, placed randomly or near high-density areas. Suggestions in a table for clarity:

| New Agent Type | Key Behaviors | Interactions/Impacts | Realism Tie-In |
|----------------|---------------|----------------------|---------------|
| **Warrior** | Patrols territory (radius=3), raids low-wealth neighbors for wealth/crops. Gains "strength" from tools/meat (new resource). | Steals from Farmers/Traders; protects settlements if "hired" by wealth threshold. Increases deaths during conflicts. | Military castes in agrarian societies; prevents unchecked expansion. |
| **Innovator** | Researches upgrades (e.g., 1% chance/step to boost global birth_rate or skill cap). Consumes extra wealth for "R&D". | Sells inventions to Toolmakers; failure drains wealth, risking bankruptcy/death. | Technological progress (e.g., irrigation); counters stagnation in insights. |
| **Merchant Guild** (Group Agent) | Aggregates Traders: Coordinates multi-agent caravans across grid, enabling long-distance trade with risk (e.g., bandit encounters). | Boosts wealth_traded 2x; fees fund roads (fertility bonuses on paths). Tracks via graph network. | Historical trade networks (Silk Road); fixes zero trades in insights. |
| **Ecologist** (or Druid) | Restores degraded patches (heals fertility at cost); predicts weather via simple ML (e.g., track past yields). | Charges Farmers for services; low interaction if fertility is high. | Environmental stewardship; adds sustainability to avoid endless decline. |
| **Ruler** (Elite Agent) | Taxes nearby agents (5% wealth/step), invests in public goods (e.g., +10% harvest in "domain"). Over-taxing sparks revolts (mass deaths). | Emerges from richest Farmer; reproduces elites with higher skill. | Governance/hierarchy; explains inequality and state formation. |

These agents would create feedback loops (e.g., Warriors protect Innovators, enabling tech booms that reduce poverty).

### Adapting to a Realistic World Map
The current toroidal 50x50 grid is abstract; for a world-scale sim, shift to geospatial realism:

- **Data Integration**: Use real-world GIS data (e.g., from Natural Earth or OpenStreetMap) for terrain. Replace uniform LandPatches with varied biomes: rivers (high fertility, linear), mountains (low harvest, barriers to movement), forests (wood resource for tools). Load via GeoPandas/Shapely for irregular polygons instead of square cells.
  
- **Scaling**: Start with a continent (e.g., Europe ~1000x1000 km at 1km resolution = 1M cells, feasible with sparse agents). Use hierarchical zooming: Global view for migrations, local for interactions. Toroidal edges off; add oceans as impassable barriers.

- **Agent Placement**: Bootstrap with historical densities (e.g., higher in river valleys). Movement: Realistic paths via river/road networks (Dijkstra on graph).

- **Implementation Tip**: Subclass MultiGrid to GeoGrid, using lat/long coords. Simulate climate via NOAA data (e.g., annual rainfall modulates fertility).

This evolves the sim from toy grid to Civ-like world-builder, where geography drives history (e.g., Nile fertility enables Egyptian booms).

### Visualization Libraries for a Playable Civilization Game
To transform this into an interactive, turn-based (or real-time) game like Civilization, prioritize libraries supporting maps, agents, UI (e.g., tech trees, city panels), and performance for 1000s of agents. Focus on 2D top-down views with zoom/pan.For geospatial realism, embed Leaflet.js (open-source maps) to overlay agent sim on Google Earth-like tiles. Challenges: Agent count caps (~10k for smooth play); solution: Aggregate distant agents into "city" blobs. 