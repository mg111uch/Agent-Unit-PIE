"""
metadata:
   summary: "This Python script executes the population dynamics simulation with fertility-based movement for farmers using default parameters, collects model data, generates plots, prints final statistics, and includes detailed insights on population trends, wealth dynamics, births/deaths, and specialist agent roles."
   dependencies: ["simulation.py", "constants.py"]
   tags: ["simulation", "runner", "analysis", "population", "dynamics", "fertility_movement"]
   hierarchy_mapping:
     classes: {}
     functions: []
   graph_methods:
     dependency_graph: {"nodes": [{"id": "run_simulation", "type": "function"}, {"id": "plot_results", "type": "function"}], "edges": [{"from": "PopuDyn", "to": "run_simulation", "type": "calls"}, {"from": "PopuDyn", "to": "plot_results", "type": "calls"}]}
     cfg_outline: "Set fertility_movement; run simulation; collect data; plot results; print summary and insights."
"""
# === Imports ===
from simulation import run_simulation, plot_results
from constants import PARAMS

# Run simulation with updated model and parameters
PARAMS["fertility_movement"] = True
model = run_simulation(PARAMS)

# Collect data
model_vars = model.datacollector.get_model_vars_dataframe()

# Plot time series (Matplotlib for Colab)
plot_results(model_vars)

# Print summary
# print(model_vars.tail())
# print(f"Final Population: {model_vars['Population'].iloc[-1]}")