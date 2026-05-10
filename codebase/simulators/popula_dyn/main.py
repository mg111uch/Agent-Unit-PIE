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