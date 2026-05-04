import time
import subprocess
import os
import sys
from datetime import datetime

class PhoenixHelper:
    def __init__(self, log_file):
        self.log_file = log_file

    def log_event(self, message):
        """Appends a timestamped message to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def handle_success(self, feature_name, loop_iteration, duration):
        """Consolidates Git commit, logging, and status reporting."""
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"feat(phoenix): {feature_name}"], check=True)
            log_msg = f"Loop {loop_iteration} SUCCESS: {feature_name} in {duration:.2f}s."
            self.log_event(log_msg)
            print(f"PHOENIX_STATUS: SUCCESS")
        except Exception as e:
            self.log_event(f"GIT ERROR: {str(e)}")
            print(f"PHOENIX_STATUS: GIT_FAIL")

    def handle_failure(self, rca, loop_iteration, duration):
        """Consolidates Git checkout and failure logging."""
        subprocess.run(["git", "checkout", "--", "."], check=True)
        self.log_event(f"Loop {loop_iteration} FAILURE after {duration:.2f}s. RCA: {rca}")
        print(f"PHOENIX_STATUS: REVERTED")

if __name__ == "__main__":
    # Simple CLI for the Orchestrator to call
    helper = PhoenixHelper(sys.argv[2]) # log_file from sys args
    action = sys.argv[1]
    if action == "success":
        helper.handle_success(sys.argv[3], sys.argv[4], float(sys.argv[5]))
    elif action == "failure":
        helper.handle_failure(sys.argv[3], sys.argv[4], float(sys.argv[5]))