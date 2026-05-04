# Usage:
# python gen_tools_file.py --project_path /path/to/project --atlas_path /path/to/atlas --conda_env myenv

'''
<project_path>path/to/project</project_path>
<atlas_path>path/to/atlas</atlas_path>
<conda_env>myenv</conda_env>

<project_tools.md>
## Project specific tool usage commands

- **Make Codebase_atlas:** `cd <atlas_path> && conda run -n <conda_env> python -m codebase_atlas.main --project-dir <project_path>/codebase --output-dir <project_path>`

- **Add markers:** `cd <atlas_path>/tools && python add_markers.py --md_file <project_path>/code_atlas.md --project_path "<project_path>"`

- **Codebase size:** `cd <atlas_path>/tools && conda run -n <conda_env> python codebase_size.py --directory <project_path>/codebase --extensions .py .yaml --output-file <project_path>/code_atlas.md --start-marker "## Codebase size" --end-marker "## End Codebase size"`

- **Make directory:** 
`cd <atlas_path>/tools && conda run -n <conda_env> python make_directree.py --reverse --base_path <project_path> --md_file <project_path>/code_atlas.md --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Copy Content:** `cd <atlas_path>/tools && conda run -n <conda_env> python copyContent.py --mode dump --md_file <project_path>/code_atlas.md --base_path <project_path> --output_file <project_path>/code_dump.txt --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Count Tokens in file:** `cd <atlas_path>/tools && conda run -n <conda_env> python token_count.py <project_path>/agent_harness.md`

- **Check if file exists:** `cd <atlas_path>/tools && conda run -n <conda_env> python path_file_exists.py <project_path>/code_atlas.md`

- **Execute in order:** `cd <atlas_path>/tools && python run_cmds.py <project_path>/project_tools.md "Make Codebase_atlas" "Add markers" "Codebase size" "Make directory" "Count Tokens in file"`

</project_tools.md>
'''

import argparse
import re

def extract_tag_content(docstring, tag):
    """Extract content from XML-like tag in docstring."""
    pattern = rf'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, docstring, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_md_content(docstring):
    """Extract content between <project_tools.md> and </project_tools.md>."""
    pattern = r'<project_tools.md>(.*?)</project_tools.md>'
    match = re.search(pattern, docstring, re.DOTALL)
    return match.group(1).strip() if match else None


def main():
    # Read this file's docstring
    current_file = __file__
    with open(current_file, 'r') as f:
        content = f.read()
    
    # Extract docstring
    docstring_pattern = r"'''\n(.*?)\n'''"
    docstring_match = re.search(docstring_pattern, content, re.DOTALL)
    if not docstring_match:
        print("Error: Could not find docstring in the file")
        return
    
    docstring = docstring_match.group(1)
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate project_tools.md file with replaced placeholders.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n'
              '  python gen_tools_file.py --project_path /home/user/project --atlas_path /home/user/atlas --conda_env myenv'
    )
    parser.add_argument('--project_path', required=True, help='Path to project directory')
    parser.add_argument('--atlas_path', required=True, help='Path to atlas directory')
    parser.add_argument('--conda_env', required=True, help='Conda environment name')
    
    args = parser.parse_args()
    
    # Extract MD content from docstring
    md_content = extract_md_content(docstring)
    if not md_content:
        print("Error: Could not find <project_tools.md> content in docstring")
        return
    
    # Replace placeholders
    md_content = md_content.replace('<project_path>', args.project_path)
    md_content = md_content.replace('<atlas_path>', args.atlas_path)
    md_content = md_content.replace('<conda_env>', args.conda_env)
    
    # Generate output file path
    output_file = f"{args.project_path}/project_tools.md"
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(md_content)
    
    print(f"Successfully generated: {output_file}")


if __name__ == '__main__':
    main()
