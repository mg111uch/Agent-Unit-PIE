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