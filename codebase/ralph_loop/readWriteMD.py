import re
import os
import yaml

def read_and_update_md(file_path: str, status: str = "read_next", feature_name: str = None, log_message: str = None) -> str:
    """Reads the next undone feature or updates a feature's status."""
    if not os.path.exists(file_path):
        return f"ERROR: Development plan file not found at {file_path}"
        
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    # Logic to find the next UNDONE feature
    if status == "read_next":
        for i, line in enumerate(lines):
            if re.match(r'^- \[ \]', line):
                # Returns the index and the feature line
                return f"INDEX:{i}\nFEATURE:{line.strip()}"

    # Logic to update the feature status
    elif feature_name and status in ["done", "failed"]:
        new_lines = []
        for i, line in enumerate(lines):
            # Check for the specific feature to update
            if feature_name in line:
                if status == "done":
                    # Mark as DONE
                    new_line = line.replace('- [ ]', '- [X] DONE') 
                elif status == "failed":
                    # Log the failed attempt
                    new_line = line.strip() + f"\n    - Attempt Failed. Log: {log_message}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
                
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
            
        return f"Plan successfully updated for feature: {feature_name} to status: {status}"

if __name__ == "__main__":
    # Load config.yaml
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    project_root = config['project_root']
    filepath = project_root+'/development_plan.md'
    next_feature = read_and_update_md(filepath,'read_next')
    print(next_feature)