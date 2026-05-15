import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
from typing import Dict, List, Tuple, Optional, Any, Set
from model import AgriculturalModel
from constants import PARAMS

# === Simulation and Visualization ===

def run_simulation(params: Dict[str, Any] = PARAMS) -> AgriculturalModel:
    """Run the agricultural simulation for the specified number of years."""
    model = AgriculturalModel(params)
    for i in range(params["years"]):
        print(f'Year: {i}')
        model.step()
        pop = model.datacollector.data['Population'][-1]
        wealth = model.datacollector.data['Total_Wealth'][-1]
        births = model.datacollector.data['Births'][-1]
        deaths = model.datacollector.data['Deaths'][-1]
        print(f'  Population: {pop}, Total Wealth: {wealth:.2f}, Births: {births}, Deaths: {deaths}')
    return model

def plot_results(model_vars: pd.DataFrame) -> None:
    """Plot the simulation results using matplotlib."""
    fig, axs = plt.subplots(4, 2, figsize=(14, 16))  # Increased rows for new agents
    axs = axs.ravel()

    # Plotting key metrics
    axs[0].plot(model_vars['Population'], label='Population', color='blue')
    axs[0].set_title('Population Over Time')
    axs[0].set_ylabel('Population')
    axs[0].legend()

    axs[1].plot(model_vars['Total_Wealth'], label='Total Wealth', color='green')
    axs[1].set_title('Total Wealth (Productivity) Over Time')
    axs[1].set_ylabel('Wealth')
    axs[1].legend()

    axs[2].plot(model_vars['Avg_Skill'], label='Average Farmer Skill', color='orange')
    axs[2].set_title('Average Farmer Skill Over Time')
    axs[2].set_ylabel('Skill')
    axs[2].legend()

    # Cumulative births and deaths
    axs[3].bar(['Births', 'Deaths'], [model_vars['Births'].sum(), model_vars['Deaths'].sum()], color=['green', 'red'])
    axs[3].set_title('Total Births vs Deaths')
    axs[3].set_ylabel('Count')

    # Plotting new agent counts
    axs[4].plot(model_vars['Healer_Count'], label='Healers', color='purple')
    axs[4].set_title('Healer Population Over Time')
    axs[4].set_ylabel('Count')
    axs[4].legend()

    axs[5].plot(model_vars['Toolmaker_Count'], label='Toolmakers', color='brown')
    axs[5].set_title('Toolmaker Population Over Time')
    axs[5].set_ylabel('Count')
    axs[5].legend()

    axs[6].plot(model_vars['Trader_Count'], label='Traders', color='cyan')
    axs[6].set_title('Trader Population Over Time')
    axs[6].set_ylabel('Count')
    axs[6].legend()

    # Plotting impact metrics (Cumulative over time)
    axs[7].plot(model_vars['Successful_Healings'].cumsum(), label='Cumulative Successful Healings', color='pink')
    axs[7].plot(model_vars['Tools_Produced'].cumsum(), label='Cumulative Tools Produced', color='gray')
    axs[7].plot(model_vars['Trades_Executed'].cumsum(), label='Cumulative Trades Executed', color='olive')
    axs[7].plot(model_vars['Wealth_Traded'].cumsum(), label='Cumulative Wealth Traded', color='teal')  # Optional
    axs[7].set_title('Cumulative Specialist Impacts')
    axs[7].set_ylabel('Count/Amount')
    axs[7].legend()

    plt.tight_layout()
    plt.savefig('simulation_plot.png')
    plt.close(fig)