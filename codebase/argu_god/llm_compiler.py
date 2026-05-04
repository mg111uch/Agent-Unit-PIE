import os, json
import subprocess
from datetime import datetime

QUESTION_FILE = '/home/manigupt/Hello/python/ai_agent/utils/gemini_question.md'

ANSWER_FILE = '/home/manigupt/Hello/python/ai_agent/utils/gemini_answer.md'

def write_question_to_file(question):
    try:
        with open(QUESTION_FILE, "w") as f:
            f.write(question)
    except IOError as e:
        print(f"Error writing question file: {e}")
        return

def run_gemini_agent():
    cmd = "cd /home/manigupt/Hello/python/ai_agent/agent_tools && conda run -n myenv python ask_gemini.py"
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    return result.returncode == 0

def read_answer_from_file():
    try:
        with open(ANSWER_FILE, "r") as f:
            content = f.read().strip()
            return json.loads(content)
    except Exception as e:
        print(f"Error reading answer file: {e}")
        return None

def compile_topic_llm(topic: str):
    topic_dir = os.path.join("topics", topic)
    wiki_dir = os.path.join(topic_dir, "wiki")
    graph_path = os.path.join(topic_dir, "graph.json")
    os.makedirs(wiki_dir, exist_ok=True)

    # Load Karpathy-style instructions
    with open("AGENTS.md") as f: agents = f.read()
    with open(os.path.join(topic_dir, "schema.md")) as f: schema = f.read()

    prompt = f"""{agents}

{schema}

Topic to compile: {topic}
Raw sources are in: {topic_dir}/raw/
Read raw files, extract arguments following the schema exactly.
Return ONLY valid JSON.
Do NOT include explanations, markdown, or text.
Do NOT wrap JSON in backticks.
Output ONLY this JSON structure:
{{
  "graph": {{
    "nodes": [array of argument nodes],
    "edges": [array of edges]
  }},
  "wiki_summary": "short markdown summary"
}}"""
    
    # write_question_to_file(prompt)

    # if not run_gemini_agent():
    #     print("Failed to run gemini agent")
    
    llm_output = read_answer_from_file()
    
    if not llm_output:
        raise ValueError("Empty Gemini output")

    if isinstance(llm_output, str):
        llm_output = json.loads(llm_output)

    # Save graph for Three.js
    with open(graph_path, "w") as f:
        json.dump(llm_output["graph"], f, indent=2)

    # Save wiki
    with open(os.path.join(wiki_dir, "index.md"), "w") as f:
        f.write(f"# LLM-compiled Wiki - {topic}\n\n{llm_output.get('wiki_summary', '')}")

    # Auto-update personal mindmap (LLM-controlled, no human edits)
    mindmap_path = os.path.join("mindmaps", "local_user", "mindmap.json")
    with open(mindmap_path) as f:
        mm = json.load(f)
    if topic not in mm["topics"]:
        mm["topics"][topic] = {
            "depth_score": 0.75,
            "confidence": 0.8,
            "last_interaction": datetime.now().strftime("%Y-%m-%d"),
            "connections": []
        }
        mm["total_topics_explored"] = mm.get("total_topics_explored", 0) + 1
    with open(mindmap_path, "w") as f:
        json.dump(mm, f, indent=2)

    return {"status": "ok", "mindmap_updated": True}