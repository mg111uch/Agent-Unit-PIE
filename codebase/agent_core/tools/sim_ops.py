import json
import os
import signal
import subprocess
import sys


try:
    from modules.simulators.simulation_connector import SimulationConnector
    simulation_connector = SimulationConnector()
    SIMULATION_AVAILABLE = True
except ImportError:
    simulation_connector = None
    SIMULATION_AVAILABLE = False


def _get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def simulation_run(input_data) -> str:
    if not SIMULATION_AVAILABLE:
        return "Error: Simulation module not available."

    try:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        run_id = input_data.get("run_id")
        params = input_data.get("params", {})
        timeout = input_data.get("timeout", None)

        if not run_id:
            return "Error: 'run_id' is required"

        if timeout:
            proc = subprocess.Popen(
                [sys.executable, __file__, json.dumps(params), run_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
                cwd=_get_project_root(),
            )
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                proc.wait()
                return json.dumps({
                    "status": "timeout",
                    "run_id": run_id,
                    "message": f"Simulation timed out after {timeout}s",
                })
            if proc.returncode != 0 and not stdout:
                return json.dumps({
                    "status": "error",
                    "run_id": run_id,
                    "message": stderr.strip() or "Simulation process failed",
                })
            return stdout.strip()
        else:
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


if __name__ == "__main__":
    params = json.loads(sys.argv[1])
    run_id = sys.argv[2]
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from modules.simulators.simulation_connector import SimulationConnector
        conn = SimulationConnector()
        result = conn.run_and_extract(params, run_id)
        signals = conn.get_signals(run_id)
        print(json.dumps({
            "status": "completed",
            "run_id": run_id,
            "summary": result,
            "signals_emitted": len(signals),
            "signals": signals,
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)
