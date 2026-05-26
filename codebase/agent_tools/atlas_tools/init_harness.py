#!/usr/bin/env python3
"""
Usage Instructions:
-------------------
This script initializes a project harness with the required directory structure and files.

Usage:
    python init_harness.py --atlas_path <path/to/atlas> --conda_env <environment_name> --project_path <path/to/project>

Arguments:
    --atlas_path   : Path to the atlas directory
    --conda_env    : Conda environment name to use for running commands
    --project_path : Path where the project structure should be created

Example:
    python init_harness.py --atlas_path /home/user/atlas --conda_env myenv --project_path /home/user/my_project
"""

import argparse
import os
import subprocess
import shutil


def check_conflicts(project_path):
    """Check for existing files/directories with conflicting names."""
    # Items to check for conflicts
    items_to_check = [
        "codebase",
        "agent_harness.md",
        "code_atlas.md",
        "project_tools.md"
    ]
    
    conflicts = {}
    
    for item in items_to_check:
        item_path = os.path.join(project_path, item)
        if os.path.exists(item_path):
            conflicts[item] = item_path
    
    if not conflicts:
        return {}
    
    print("\n" + "=" * 50)
    print("CONFLICT DETECTED: The following items already exist:")
    print("=" * 50)
    
    for item, path in conflicts.items():
        item_type = "Directory" if os.path.isdir(path) else "File"
        print(f"  - {item} ({item_type})")
    
    print("\nDo you want to (k)eep original or (r)eplace with new? ")
    print("  - Press 'k' or 'K' to keep original files/directories")
    print("  - Press 'r' or 'R' to replace with new files/directories")
    
    while True:
        choice = input("\nEnter your choice (k/r): ").strip().lower()
        if choice in ['k', 'r']:
            break
        print("Invalid choice. Please enter 'k' or 'r'.")
    
    if choice == 'k':
        print("\nKeeping original files/directories.")
        return {item: "keep" for item in conflicts.keys()}
    else:
        print("\nReplacing existing files/directories.")
        return {item: "replace" for item in conflicts.keys()}


def should_create_item(item_name, conflict_decisions):
    """Check if we should create the item based on user's decision."""
    if item_name in conflict_decisions:
        return conflict_decisions[item_name] == "replace"
    return True


def create_directory_structure(project_path, conflict_decisions):
    """Create the required directory structure."""
    # Create codebase/tests directory only if we should replace
    if should_create_item("codebase", conflict_decisions):
        tests_dir = os.path.join(project_path, "codebase", "tests")
        os.makedirs(tests_dir, exist_ok=True)
        print(f"Created directory: {tests_dir}")
        
        # Create codebase directory (main.py will be created separately)
        codebase_dir = os.path.join(project_path, "codebase")
        os.makedirs(codebase_dir, exist_ok=True)
        print(f"Created directory: {codebase_dir}")
    else:
        print(f"Skipped creating directory: codebase (keeping original)")
        # Still ensure the tests directory exists if codebase exists
        tests_dir = os.path.join(project_path, "codebase", "tests")
        if not os.path.exists(tests_dir):
            os.makedirs(tests_dir, exist_ok=True)
            print(f"Created directory: {tests_dir}")


def create_main_py(project_path, conflict_decisions):
    """Create main.py with the specified content."""
    main_py_path = os.path.join(project_path, "codebase", "main.py")
    
    if should_create_item("codebase", conflict_decisions):
        content = "print('Hello')"
        with open(main_py_path, 'w') as f:
            f.write(content)
        print(f"Created file: {main_py_path}")
    else:
        print(f"Skipped creating file: main.py (keeping original)")


def create_agent_harness_md(project_path, project_path_value, conda_env, conflict_decisions):
    """Create agent_harness.md with placeholders replaced."""
    if not should_create_item("agent_harness.md", conflict_decisions):
        print(f"Skipped creating file: agent_harness.md (keeping original)")
        return
        
    agent_harness_path = os.path.join(project_path, "agent_harness.md")
    content = """# AI Agent Development Guidelines 

## TASK

## Project Paths

- **Project_root:**  `{project_path}`
- **Source_code:** (Working directory) `{project_path}/codebase`

## Code Execution & Validation Environment

- **Command to run project:** `cd {project_path}/codebase && conda run -n {conda_env} python main.py`.
- **Command to run Tests :** `cd {project_path}/codebase && conda run -n {conda_env} python -m pytest tests/ -v`

## Core principles

- **Small scope always** — Never ask the agent to change >3 files at once or understand the full codebase.
- **Strict modularity** — Single responsibility, clear interfaces, minimal coupling.
- **Test-first mindset** — Tests are the safety net for AI-generated code.
- **Human-in-the-loop** — Agent proposes → you review → apply → test → commit.
- Optimize for handling large codebases while maintaining output quality.

## File & Module Size Rules

- Max **400–500 lines** per file (including tests & comments).
- **One public class/struct/interface** per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.

## Testing Mandates (Non-Negotiable)

Every feature/change **must** include:

- **Unit tests** for new/altered systems & controllers (mock event bus, components).
- **Integration smoke tests** for core loops (input → ECS tick → render).
- **View tests** — at minimum property assertions (position, visibility) + visual smoke checklist.
- Controller examples: input → command/event mapping, mode switching, buffering.
- **Red → Green → Refactor**: Agent first writes failing test → implements → passes.
- Aim for **>80% coverage** on logic-heavy files (systems/controllers).

Use your language's test framework (e.g., pytest/unittest).
""".format(project_path=project_path_value, conda_env=conda_env)
    
    with open(agent_harness_path, 'w') as f:
        f.write(content)
    print(f"Created file: {agent_harness_path}")


def create_code_atlas_md(project_path, conflict_decisions):
    """Create code_atlas.md with the specified content."""
    if not should_create_item("code_atlas.md", conflict_decisions):
        print(f"Skipped creating file: code_atlas.md (keeping original)")
        return
        
    code_atlas_path = os.path.join(project_path, "code_atlas.md")
    content = """## Codebase size
## End Codebase size

### FILE_MAP Tree
### End Tree
"""
    with open(code_atlas_path, 'w') as f:
        f.write(content)
    print(f"Created file: {code_atlas_path}")


def run_project_tool_command(atlas_path, conda_env, project_path, conflict_decisions):
    """Run the command to generate project_tools.md."""
    # Check if we should replace project_tools.md
    if not should_create_item("project_tools.md", conflict_decisions):
        print(f"Skipped creating file: project_tools.md (keeping original)")
        return
    
    project_tools_path = os.path.join(project_path, "project_tools.md")
    command = [
        "cd", f"{atlas_path}/tools", "&&",
        "conda", "run", "-n", conda_env,
        "python", "gen_tools_file.py",
        "--atlas_path", atlas_path,
        "--conda_env", conda_env,
        "--project_path", project_path
    ]
    
    # Join command for shell execution
    cmd_str = " ".join(command)
    print(f"Running command: {cmd_str}")
    
    try:
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            print(f"Successfully generated project_tools.md")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"Error running command: {result.stderr}")
            # Create an empty project_tools.md if command fails
            project_tools_path = os.path.join(project_path, "project_tools.md")
            with open(project_tools_path, 'w') as f:
                f.write("# Project Tools\n\n")
            print(f"Created empty project_tools.md at: {project_tools_path}")
    except Exception as e:
        print(f"Exception running command: {e}")
        # Create an empty project_tools.md if command fails
        project_tools_path = os.path.join(project_path, "project_tools.md")
        with open(project_tools_path, 'w') as f:
            f.write("# Project Tools\n\n")
        print(f"Created empty project_tools.md at: {project_tools_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Initialize project harness with directory structure and files.'
    )
    parser.add_argument(
        '--atlas_path',
        required=True,
        help='Path to the atlas directory'
    )
    parser.add_argument(
        '--conda_env',
        required=True,
        help='Conda environment name to use for running commands'
    )
    parser.add_argument(
        '--project_path',
        required=True,
        help='Path where the project structure should be created'
    )
    
    args = parser.parse_args()
    
    # Get absolute paths
    atlas_path = os.path.abspath(args.atlas_path)
    project_path = os.path.abspath(args.project_path)
    conda_env = args.conda_env
    
    print(f"Atlas Path: {atlas_path}")
    print(f"Conda Env: {conda_env}")
    print(f"Project Path: {project_path}")
    print("-" * 50)
    
    # Check for conflicts and get user decision
    conflict_decisions = check_conflicts(project_path)
    
    print("-" * 50)
    
    # Create directory structure
    create_directory_structure(project_path, conflict_decisions)
    
    # Create main.py
    create_main_py(project_path, conflict_decisions)
    
    # Create agent_harness.md
    create_agent_harness_md(project_path, project_path, conda_env, conflict_decisions)
    
    # Create code_atlas.md
    create_code_atlas_md(project_path, conflict_decisions)
    
    # Run project_tool_command to generate project_tools.md
    run_project_tool_command(atlas_path, conda_env, project_path, conflict_decisions)
    
    print("-" * 50)
    print("Project harness initialization complete!")


if __name__ == "__main__":
    main()
