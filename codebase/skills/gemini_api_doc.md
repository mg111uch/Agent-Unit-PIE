### Stateful conversation

To continue a conversation, pass the `id` from the previous interaction to the
`previous_interaction_id` parameter. The API remembers the conversation history,
so you only need to send the new input. For details on which fields are
inherited and which must be re-specified, see
[Server-side state management](https://ai.google.dev/gemini-api/docs/interactions#server-side-state).

### Python

    from google import genai

    client = genai.Client()

    # 1. First turn
    interaction1 = client.interactions.create(
        model="gemini-3-flash-preview",
        input="Hi, my name is Phil."
    )
    print(f"Model: {interaction1.outputs[-1].text}")

    # 2. Second turn (passing previous_interaction_id)
    interaction2 = client.interactions.create(
        model="gemini-3-flash-preview",
        input="What is my name?",
        previous_interaction_id=interaction1.id
    )
    print(f"Model: {interaction2.output_text}")

