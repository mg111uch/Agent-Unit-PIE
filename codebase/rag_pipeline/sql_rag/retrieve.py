import yaml
import re
import subprocess

def retrieve_context(spec, db='rag.db'):
    # Craft query from spec - use deps as primary keywords
    dep_words = set()
    for dep in spec.get('deps', []):
        dep_words.update(re.findall(r'\b\w+\b', dep))
    keywords = ' '.join(dep_words)
    if not keywords:
        # Fallback to feature words if no deps
        feature_words = set(re.findall(r'\b\w+\b', spec['feature']))
        keywords = ' '.join(feature_words)
    result = subprocess.run(['python', 'sqlrag.py', 'query', f'--query={keywords}', '--top_k=5', '--db', db],
                            capture_output=True, text=True)

    # Parse output (enhance sqlrag.py later for JSON; for now, extract via regex)
    files = re.findall(r'Path: (.*?)\nContent Preview: (.*?)\n-{50}', result.stdout, re.DOTALL)

    # List paths of files needing modifications
    context = "=== RETRIEVED CONTEXT ===\n"
    for path, preview in files[:3]:  # Limit for prompt size
        context += f"{path}\n"

    with open('context.txt', 'w') as f:
        f.write(context)
    return context

if __name__ == '__main__':
    spec = yaml.safe_load(open('next_feature.yaml'))

    ctx = retrieve_context(spec)
    print(f"Retrieved: {len(ctx)} chars to context.txt")

