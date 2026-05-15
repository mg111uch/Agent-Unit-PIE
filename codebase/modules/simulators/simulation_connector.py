class SimulationConnector:
    def run_and_extract(self, params: dict, run_id: str) -> str:
        """Run simulation, extract signals, store in KB, return summary"""
    
    def get_patterns(self, run_id: str) -> str:
        """Read patterns.md for this simulation run"""
    
    def compare_runs(self, run_ids: list[str]) -> str:
        """Graph diff between simulation runs"""
    
    def inject_policy(self, run_id: str, policy: dict) -> str:
        """Modify simulation params and re-run a scenario branch"""