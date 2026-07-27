# 📂 simulators
Generated: 2026-07-27 19:23:22
Files: 1

---

F107│simulation_connector.py│301
S: simulation_connector.py
D: ●datetime,json,kernel,pathlib,yaml,+3
C: SimulationConnector│[__init__,run_and_extract,_emit_signals_to_kernel,_extract_signals,_store_run,_generate_summary,get_signals,get_params,compare_runs,inject_policy,+1]
   S: Bridge between popula_dyn and kernel cognition.
F: _codebase_root()
   ↳Called by: F107:__init__
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F107:__init__]
C: SimulationConnector│[__init__,run_and_extract,_emit_signals_to_kernel,_extract_signals,_store_run,_generate_summary,get_signals,get_params,compare_runs,inject_policy,+1]
   S: Bridge between popula_dyn and kernel cognition.
   F: __init__(self,base_path,emit_to_kernel)
   ↳Calls: F107:_codebase_root
   F: run_and_extract(self,params,run_id,emit_signals)→str
      S: Run simulation, extract signals, store in KB.
      S: Args:
      S: params: Simulation parameters
      S: run_id: Unique identifier for this run
      S: emit_signals: Whether to emit to kernel (default: True)
   F: _emit_signals_to_kernel(self,run_id,signals)→None
      S: Emit simulation signals to kernel.
   F: _extract_signals(self,model,params)→Any
      S: Extract signals from simulation results.
   F: _store_run(self,run_id,params,model,signals)→None
      S: Store run data in units/simulations/{run_id}/
   F: _generate_summary(self,run_id,model,signals)→str
      S: Generate readable summary.
   F: get_signals(self,run_id)→Any
      S: Read signals for a simulation run.
   F: get_params(self,run_id)→Any
      S: Read params for a simulation run.
   F: compare_runs(self,run_ids)→str
      S: Compare multiple simulation runs.
      S: Args:
      S: run_ids: List of run IDs to compare
      S: Returns:
      S: Comparison string
   F: inject_policy(self,base_run_id,policy,new_run_id)→str
      S: Inject policy into base run and re-run.
      S: Args:
      S: base_run_id: Base run to modify
      S: policy: Policy params to inject ({param: value})
      S: new_run_id: New run ID
   F: list_runs(self)→List[str]
      S: List all simulation runs.
---
