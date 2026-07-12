import json

try:
    from modules.simulators.simulation_connector import SimulationConnector
    simulation_connector = SimulationConnector()
    SIMULATION_AVAILABLE = True
except ImportError:
    simulation_connector = None
    SIMULATION_AVAILABLE = False


def simulation_run(input_data) -> str:
    if not SIMULATION_AVAILABLE:
        return "Error: Simulation module not available."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        run_id = input_data.get("run_id")
        params = input_data.get("params", {})

        if not run_id:
            return "Error: 'run_id' is required"

        result = simulation_connector.run_and_extract(params, run_id)

        signals = simulation_connector.get_signals(run_id)
        output = {
            "status": "completed",
            "run_id": run_id,
            "summary": result,
            "signals_emitted": len(signals),
            "signals": signals,
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in simulation_run: {str(e)}"


def simulation_compare(input_data) -> str:
    if not SIMULATION_AVAILABLE:
        return "Error: Simulation module not available."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        run_ids = input_data.get("run_ids", [])

        if not run_ids:
            return "Error: 'run_ids' is required"

        result = simulation_connector.compare_runs(run_ids)
        return result

    except Exception as e:
        return f"Error in simulation_compare: {str(e)}"


def simulation_list(input_data) -> str:
    if not SIMULATION_AVAILABLE:
        return "Error: Simulation module not available."

    try:
        runs = simulation_connector.list_runs()
        return json.dumps({"runs": runs})

    except Exception as e:
        return f"Error in simulation_list: {str(e)}"


def simulation_get_signals(input_data) -> str:
    if not SIMULATION_AVAILABLE:
        return "Error: Simulation module not available."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        run_id = input_data.get("run_id")

        if not run_id:
            return "Error: 'run_id' is required"

        signals = simulation_connector.get_signals(run_id)
        return json.dumps({"run_id": run_id, "signals": signals}, indent=2)

    except Exception as e:
        return f"Error in simulation_get_signals: {str(e)}"
