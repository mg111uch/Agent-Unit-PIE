import json
import os, datetime
from argu_god.engine.question_builder import build_question
from argu_god.engine.storage import load_state, save_state, add_response, load_beliefs, save_beliefs
from argu_god.engine.retriever import index_arguments, get_counter_argument
from argu_god.engine.vector_store import index_graph
from argu_god.engine.retriever import get_best_counter
from argu_god.engine.analyzer import detect_contradictions

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_graph(topic: str):
    path = os.path.join(BASE_PATH, "topics", topic, "graph.json")
    
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)
    
def get_next_argument(topic, graph, state, beliefs):
    nodes = graph.get("nodes", [])

    # prioritize arguments user disagrees or unsure
    for node in nodes:
        name = node["name"]

        if name in state["seen_arguments"]:
            continue

        if name in beliefs["arguments"]:
            stance = beliefs["arguments"][name]["stance"]
            if stance in ["disagree", "neutral"]:
                return node

    # fallback
    for node in nodes:
        if node["name"] not in state["seen_arguments"]:
            return node

    return None

def get_user_choice():
    while True:
        choice = input("Select option (1-4 or 'exit'): ").strip()

        if choice.lower() == "exit":
            return {"type": "exit"}

        if choice in ["1", "2", "3"]:
            return {
                "type": "choice",
                "value": int(choice),
                "custom_text": None
            }

        if choice == "4":
            text = input("Write your response: ").strip()
            return {
                "type": "choice",
                "value": 4,
                "custom_text": text
            }

        print("Invalid input. Try again.")

def map_choice_to_stance(choice):
    if choice == 1:
        return "agree", 0.7
    elif choice == 2:
        return "disagree", 0.7
    elif choice == 3:
        return "neutral", 0.5
    elif choice == 4:
        return "custom", 0.6

def run_explore_loop(topic: str):

    print(f"Exploring topic: {topic}")
    # print(f"Already seen: {len(state['seen_arguments'])} arguments\n")

    graph = load_graph(topic)
    if not graph:
        return f"Topic not found: {topic}"

    state = load_state()    

    if state["current_topic"] != topic:
        state["current_topic"] = topic
        state["seen_arguments"] = []
        state["responses"] = []
        save_state(state)

    index = index_arguments(graph)

    index_graph(graph)

    while True:
        argument = get_next_argument(topic, graph, state)

        if not argument:
            return "No more arguments left."

        counter = get_counter_argument(argument, index)       
        print(build_question(argument, counter))

        best_counter = get_best_counter(argument)
        print(build_question(argument, best_counter))

        user_input = get_user_choice()

        if user_input["type"] == "exit":
            save_state(state)
            return "Exited."
        
        choice = user_input["value"]

        if choice == 1:
            print("You seem to agree. Let's test this with a counterpoint next.\n")
        elif choice == 2:
            print("Good—considering an opposing view.\n")
        elif choice == 3:
            print("Let's explore this further step by step.\n")
        elif choice == 4:
            print("Custom response recorded.\n")

        # store response
        add_response(
            state,
            argument["name"],
            user_input["value"],
            user_input["custom_text"]
        )

        # Update Belief State After Each Response

        beliefs = load_beliefs()

        arg_name = argument["name"]
        stance, confidence = map_choice_to_stance(user_input["value"])

        if arg_name not in beliefs["arguments"]:
            beliefs["arguments"][arg_name] = {
                "stance": stance,
                "confidence": confidence,
                "last_updated": "",
                "history": []
            }

        beliefs["arguments"][arg_name]["history"].append({
            "stance": stance,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })

        beliefs["arguments"][arg_name]["stance"] = stance
        beliefs["arguments"][arg_name]["confidence"] = confidence
        beliefs["arguments"][arg_name]["last_updated"] = datetime.now().isoformat()

        save_beliefs(beliefs)

        # Surface Contradictions in Loop

        contradictions = detect_contradictions(beliefs, graph)

        if contradictions:
            print("\n⚠️ Potential contradiction detected:")
            for c in contradictions:
                print(f"- You agreed with both: {c[0]} AND {c[1]}")
            print("")

        # mark seen
        state["seen_arguments"].append(argument["name"])

        save_state(state)

        print("\nSaved. Moving to next...\n")