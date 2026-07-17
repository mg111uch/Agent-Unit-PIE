def build_question(argument, counter_argument=None):
    name = argument.get("name", "")
    premise = argument.get("premise", "")
    opt1 = f"Agree: {premise[:120]}..."
    if counter_argument:
        opt2 = f"Counter: {counter_argument.get('premise', '')[:120]}..."
    else:
        opt2 = "Counter: I disagree with this argument."
    opt3 = "Explore related idea (similar argument)"
    return f"""
Argument: {name}

{premise}

What do you think?

1. {opt1}
2. {opt2}
3. {opt3}
4. Write my own response
"""


def build_structured_question(argument, counter_argument=None):
    """Return a structured question dict for the ask_user_question tool format."""
    name = argument.get("name", "")
    premise = argument.get("premise", "")
    side_label = {"pro": "For", "con": "Against", "neutral": "Neutral"}.get(
        argument.get("side", ""), ""
    )
    question_text = f"Argument: {name} ({side_label})\n\n{premise}"
    if counter_argument:
        question_text += f"\n\nOpposing view: {counter_argument.get('premise', '')[:200]}..."
    return {
        "question": question_text,
        "options": [
            "Agree: I accept this argument",
            "Counter: I disagree",
            "Explore / unsure",
        ],
    }
