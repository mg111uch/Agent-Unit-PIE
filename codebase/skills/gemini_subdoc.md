# Multi-turn conversations

The Interactions API supports multi-turn conversations by chaining interactions
together using `previous_interaction_id`. Each turn is a separate interaction,
and the API automatically manages conversation history.

> [!NOTE]
> **Note:** Unlike other APIs where you might manage conversation history manually, the Interactions API handles conversation state server-side. You pass the `id` from the previous interaction to continue the conversation.

### Python

    from google import genai

    client = genai.Client()

    interaction1 = client.interactions.create(
        model="gemini-3.5-flash",
        input="I have 2 dogs in my house.",
    )
    print(interaction1.output_text)

    interaction2 = client.interactions.create(
        model="gemini-3.5-flash",
        input="How many paws are in my house?",
        previous_interaction_id=interaction1.id,
    )
    print(interaction2.output_text)


    const ai = new GoogleGenAI({});

    async function main() {
      const interaction1 = await ai.interactions.create({
        model: "gemini-3.5-flash",
        input: "I have 2 dogs in my house.",
      });
      console.log("Response 1:", interaction1.output_text);

      const interaction2 = await ai.interactions.create({
        model: "gemini-3.5-flash",
        input: "How many paws are in my house?",
        previous_interaction_id: interaction1.id,
      });
      console.log("Response 2:", interaction2.output_text);
    }

    await main();


    INTERACTION_ID=$(echo "$RESPONSE1" | jq -r '.id')

    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -H 'Content-Type: application/json' \
      -H "Api-Revision: 2026-05-20" \
      -d '{
        "model": "gemini-3.5-flash",
        "input": "I have two dogs in my house. How many paws are in my house?",
        "previous_interaction_id": "'$INTERACTION_ID'"
      }'

Streaming can also be used for multi-turn conversations by combining
`previous_interaction_id` with the streaming methods.

### Python

    from google import genai

    client = genai.Client()

    interaction1 = client.interactions.create(
        model="gemini-3.5-flash",
        input="I have 2 dogs in my house.",
    )
    print(interaction1.output_text)

    stream = client.interactions.create(
        model="gemini-3.5-flash",
        input="How many paws are in my house?",
        previous_interaction_id=interaction1.id,
        stream=True
    )
    for event in stream:
        if event.event_type == "step.delta":
            if event.delta.type == "text":
                print(event.delta.text, end="")


    const ai = new GoogleGenAI({});

    async function main() {
      const interaction1 = await ai.interactions.create({
        model: "gemini-3.5-flash",
        input: "I have 2 dogs in my house.",
      });
      console.log("Response 1:", interaction1.output_text);

      const stream = await ai.interactions.create({
        model: "gemini-3.5-flash",
        input: "How many paws are in my house?",
        previous_interaction_id: interaction1.id,
        stream: true,
      });
      for await (const event of stream) {
        if (event.event_type === "step.delta") {
          if (event.delta.type === "text") {
            process.stdout.write(event.delta.text);
          }
        }
      }
    }

    await main();


    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -H 'Content-Type: application/json' \
      -H "Api-Revision: 2026-05-20" \
      --no-buffer \
      -d '{
        "model": "gemini-3.5-flash",
        "input": "How many paws are in my house?",
        "previous_interaction_id": "'$INTERACTION_ID'",
        "stream": true
      }'

# Stateless conversations

By default, the Interactions API manages conversation state server-side when you use `previous_interaction_id`. However, you can also operate in stateless mode by managing the conversation history yourself on the client side.

To use stateless mode:
1. Set `store=false` in your request to opt out of server-side storage.
2. Maintain the conversation history as an array of **steps** on the client side.
3. In subsequent requests, pass the accumulated steps in the `input` field, and append your new turn as a `user_input` step.

> [!NOTE]
> **Note:** If the model uses "thinking" or tools, you **must** preserve and resend all model-generated steps (such as `thought` and `function_call` steps) exactly as received, as they contain signatures required to continue the conversation.

### Python

    from google import genai

    client = genai.Client()

    history = [
        {
            "type": "user_input",
            "content": [{"type": "text", "text": "I have 2 dogs in my house."}]
        }
    ]

    interaction1 = client.interactions.create(
        model="gemini-3.5-flash",
        store=False,
        input=history
    )
    print("Response 1:", interaction1.steps[-1].content[0].text)

    for step in interaction1.steps:
        history.append(step.model_dump())

    history.append({
        "type": "user_input",
        "content": [{"type": "text", "text": "How many paws are in my house?"}]
    })

    interaction2 = client.interactions.create(
        model="gemini-3.5-flash",
        store=False,
        input=history
    )
    print("Response 2:", interaction2.steps[-1].content[0].text)


    const ai = new GoogleGenAI({});

    async function main() {
      const history = [
        {
          type: "user_input",
          content: [{ type: "text", text: "I have 2 dogs in my house." }]
        }
      ];

      const interaction1 = await ai.interactions.create({
        model: "gemini-3.5-flash",
        store: false,
        input: history
      });
      console.log("Response 1:", interaction1.steps.at(-1).content[0].text);

      history.push(...interaction1.steps);

      history.push({
        type: "user_input",
        content: [{ type: "text", text: "How many paws are in my house?" }]
      });

      const interaction2 = await ai.interactions.create({
        model: "gemini-3.5-flash",
        store: false,
        input: history
      });
      console.log("Response 2:", interaction2.steps.at(-1).content[0].text);
    }

    await main();


    # Extract the steps from response
    MODEL_STEPS=$(echo "$RESPONSE1" | jq '.steps')

    # Reconstruct the full history for Turn 2 by combining:
    # 1. First user input
    # 2. Model response steps
    # 3. Second user input
    HISTORY=$(jq -n \
      --argjson first_input '[{"type": "user_input", "content": "I have 2 dogs in my house."}]' \
      --argjson model_steps "$MODEL_STEPS" \
      --argjson second_input '[{"type": "user_input", "content": "How many paws are in my house?"}]' \
      "'"'"'$first_input + $model_steps + $second_input'"'"'")

    # Turn 2: Send the full history
    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -H 'Content-Type: application/json' \
      -H "Api-Revision: 2026-05-20" \
      -d "{
        \"model\": \"gemini-3.5-flash\",
        \"store\": false,
        \"input\": $HISTORY
      }"

# Function calling with Structured output

> [!NOTE]
> **Note:** This version of the page covers the **Interactions API** . You can use the toggle on this page to switch to the [generateContent API version of this page](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).

You can configure Gemini models to generate responses that adhere to a provided
JSON Schema. This ensures predictable, type-safe results and simplifies
extracting structured data from unstructured text.

Using structured outputs is ideal for:

- **Data extraction:** Pull specific information like names and dates from text.
- **Structured classification:** Classify text into predefined categories.
- **Agentic workflows:** Generate structured inputs for tools or APIs.

In addition to supporting JSON Schema in the REST API, the Google GenAI SDKs
allow defining schemas using
[Pydantic](https://docs.pydantic.dev/latest/) (Python) and
[Zod](https://zod.dev/) (JavaScript).

## Structured output examples

### Recipe Extractor

This example demonstrates how to extract structured data from text using basic
JSON Schema types like `object`, `array`, `string`, and `integer`.

### Python

    from google import genai
    from pydantic import BaseModel, Field
    from typing import List, Optional

    class Ingredient(BaseModel):
        name: str = Field(description="Name of the ingredient.")
        quantity: str = Field(description="Quantity of the ingredient, including units.")

    class Recipe(BaseModel):
        recipe_name: str = Field(description="The name of the recipe.")
        prep_time_minutes: Optional[int] = Field(description="Optional time in minutes to prepare the recipe.")
        ingredients: List[Ingredient]
        instructions: List[str]

    client = genai.Client()

    prompt = """
    Please extract the recipe from the following text.
    The user wants to make delicious chocolate chip cookies.
    They need 2 and 1/4 cups of all-purpose flour, 1 teaspoon of baking soda,
    1 teaspoon of salt, 1 cup of unsalted butter (softened), 3/4 cup of granulated sugar,
    3/4 cup of packed brown sugar, 1 teaspoon of vanilla extract, and 2 large eggs.
    For the best part, they'll need 2 cups of semisweet chocolate chips.
    First, preheat the oven to 375°F (190°C). Then, in a small bowl, whisk together the flour,
    baking soda, and salt. In a large bowl, cream together the butter, granulated sugar, and brown sugar
    until light and fluffy. Beat in the vanilla and eggs, one at a time. Gradually beat in the dry
    ingredients until just combined. Finally, stir in the chocolate chips. Drop by rounded tablespoons
    onto ungreased baking sheets and bake for 9 to 11 minutes.
    """

    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": Recipe.model_json_schema()
        },
    )

    recipe = Recipe.model_validate_json(interaction.output_text)
    print(recipe)

### Content Moderation

This example showcases `anyOf` for conditional schemas and `enum` for
classification, allowing the output structure to vary based on the content.

### Python

    from google import genai
    from pydantic import BaseModel, Field
    from typing import Union, Literal

    class SpamDetails(BaseModel):
        reason: str = Field(description="The reason why the content is considered spam.")
        spam_type: Literal["phishing", "scam", "unsolicited promotion", "other"] = Field(description="The type of spam.")

    class NotSpamDetails(BaseModel):
        summary: str = Field(description="A brief summary of the content.")
        is_safe: bool = Field(description="Whether the content is safe for all audiences.")

    class ModerationResult(BaseModel):
        decision: Union[SpamDetails, NotSpamDetails]

    client = genai.Client()

    prompt = """
    Please moderate the following content and provide a decision.
    Content: 'Congratulations! You''ve won a free cruise to the Bahamas. Click here to claim your prize: www.definitely-not-a-scam.com'
    """

    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ModerationResult.model_json_schema()
        },
    )

    result = ModerationResult.model_validate_json(interaction.output_text)
    print(result)

### Recursive Structures

This example illustrates how to define a recursive schema such as an
organization chart.

### Python

    from google import genai
    from pydantic import BaseModel, Field
    from typing import List

    class Employee(BaseModel):
        """Represents an employee in an organization."""
        name: str
        employee_id: int
        reports: List["Employee"] = Field(
            default_factory=list,
            description="A list of employees reporting to this employee."
        )

    client = genai.Client()

    prompt = """
    Generate an organization chart for a small team.
    The manager is Alice, who manages Bob and Charlie. Bob manages David.
    """

    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": Employee.model_json_schema()
        },
    )

    employee = Employee.model_validate_json(interaction.output_text)
    print(employee)

## Streaming results

You can stream structured outputs, allowing you to start processing the
response as it's being generated. The streamed chunks are valid partial JSON
strings that can be concatenated to form the final JSON object.

### Python

    from google import genai
    from pydantic import BaseModel
    from typing import Literal

    class Feedback(BaseModel):
        sentiment: Literal["positive", "neutral", "negative"]
        summary: str

    client = genai.Client()
    prompt = "The new UI is incredibly intuitive. Add a very long summary to test streaming!"

    stream = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": Feedback.model_json_schema()
        },
        stream=True
    )
    for event in stream:
        if event.event_type == "step.delta":
            if event.delta.type == "text" and getattr(event.delta, "text", None):
                print(event.delta.text, end="", flush=True)

## Structured outputs with tools

> [!WARNING]
> **Preview:** This feature is available only to Gemini 3 series models.

Gemini 3 lets you combine Structured Outputs with built-in tools, including
[Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search),
[URL Context](https://ai.google.dev/gemini-api/docs/url-context),
[Code Execution](https://ai.google.dev/gemini-api/docs/code-execution),
[File Search](https://ai.google.dev/gemini-api/docs/file-search#structured-output), and
[Function Calling](https://ai.google.dev/gemini-api/docs/function-calling).

### Python

    from google import genai
    from pydantic import BaseModel, Field
    from typing import List

    class MatchResult(BaseModel):
        winner: str = Field(description="The name of the winner.")
        final_match_score: str = Field(description="The final match score.")
        scorers: List[str] = Field(description="The name of the scorer.")

    client = genai.Client()

    interaction = client.interactions.create(
        model="gemini-3.1-pro-preview",
        input="Search for all details for the latest Euro.",
        tools=[{"type": "google_search"}, {"type": "url_context"}],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": MatchResult.model_json_schema()
        },
    )

    result = MatchResult.model_validate_json(interaction.output_text)
    print(result)

## JSON schema support

To generate a JSON object, configure `response_format` with an object (or an array containing an object) of type `text` and set its `mime_type` to `application/json`. The schema should be provided in the `schema` field.

Gemini's structured output mode supports a subset of the
[JSON Schema](https://json-schema.org/) specification.

The following values of `type` are supported:

- **`string`**: For text.
- **`number`**: For floating-point numbers.
- **`integer`**: For whole numbers.
- **`boolean`**: For true or false values.
- **`object`**: For structured data with key-value pairs.
- **`array`**: For lists of items.
- **`null`** : To allow a property to be null, include `"null"` in the type array (e.g., `{"type": ["string", "null"]}`).

These descriptive properties help guide the model:

- **`title`**: A short description of a property.
- **`description`**: A longer and more detailed description of a property.

### Type-specific properties

**For `object` values:**

- **`properties`**: An object where each key is a property name and each value is a schema for that property.
- **`required`**: An array of strings, listing which properties are mandatory.
- **`additionalProperties`** : Controls whether properties not listed in `properties` are allowed. Can be a boolean or a schema.

**For `string` values:**

- **`enum`**: Lists a specific set of possible strings for classification tasks.
- **`format`** : Specifies a syntax for the string, such as `date-time`, `date`, `time`.

**For `number` and `integer` values:**

- **`enum`**: Lists a specific set of possible numeric values.
- **`minimum`**: The minimum inclusive value.
- **`maximum`**: The maximum inclusive value.

**For `array` values:**

- **`items`**: Defines the schema for all items in the array.
- **`prefixItems`**: Defines a list of schemas for the first N items, allowing for tuple-like structures.
- **`minItems`**: The minimum number of items in the array.
- **`maxItems`**: The maximum number of items in the array.

## Structured outputs versus function calling

| Feature | Primary Use Case |
|---|---|
| **Structured Outputs** | **Formatting the final response.** Use when you want the model's *answer* in a specific format. |
| **Function Calling** | **Taking action during conversation.** Use when the model needs to *ask you* to perform a task before providing a final answer. |

## Best practices

- **Clear descriptions:** Use the `description` field to guide the model.
- **Strong typing:** Use specific types (`integer`, `string`, `enum`).
- **Prompt engineering:** Clearly state what you want the model to do.
- **Validation:** While output is syntactically correct JSON, always validate values in your application.
- **Error handling:** Implement robust error handling for schema-compliant but semantically incorrect outputs.

## Limitations

- **Schema subset:** Not all JSON Schema features are supported.
- **Schema complexity:** Very large or deeply nested schemas may be rejected.

# Stream tool calls

When using tools with streaming, the model generates function calls as a
sequence of `step.delta` events on the stream. Tool arguments can be streamed
as partial arguments using `arguments`. You must aggregate these deltas to
reconstruct the complete tool calls before executing them.

### Python

    import json
    from google import genai

    client = genai.Client()

    weather_tool = {
        "type": "function",
        "name": "get_weather",
        "description": "Gets the weather for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city and state"}
            },
            "required": ["location"]
        }
    }

    stream = client.interactions.create(
        model="gemini-3-flash-preview",
        input="What is the weather in Paris?",
        tools=[weather_tool],
        stream=True
    )

    current_calls = {}
    tool_calls = []

    for event in stream:
        if event.event_type == "step.start":
            if event.step.type == "function_call":
                current_calls[event.index] = {
                    "id": event.step.id,
                    "name": event.step.name,
                    "arguments": ""
                }
                if hasattr(event.step, "arguments") and event.step.arguments:
                    if isinstance(event.step.arguments, dict):
                        current_calls[event.index]["arguments"] = json.dumps(event.step.arguments)
                    else:
                        current_calls[event.index]["arguments"] = event.step.arguments
        elif event.event_type == "step.delta":
            if event.delta.type == "arguments":
                if event.index in current_calls:
                    current_calls[event.index]["arguments"] += event.delta.partial_arguments
            elif event.delta.type == "text":
                print(event.delta.text, end="", flush=True)

        elif event.event_type == "interaction.completed":
            for index, call in current_calls.items():
                args = call["arguments"]
                if args:
                    args = json.loads(args)
                else:
                    args = {}

                tool_calls.append({
                    "type": "function_call",
                    "id": call["id"],
                    "name": call["name"],
                    "arguments": args
                })

            print(f"\nFinal tool calls ready to execute:")
            print(json.dumps(tool_calls, indent=2))


    const client = new GoogleGenAI({});

    const weatherTool = {
        type: 'function',
        name: 'get_weather',
        description: 'Gets the weather for a given location.',
        parameters: {
            type: 'object',
            properties: {
                location: { type: 'string', description: 'The city and state' }
            },
            required: ['location']
        }
    };

    const stream = await client.interactions.create({
        model: 'gemini-3-flash-preview',
        input: 'What is the weather in Paris?',
        tools: [weatherTool],
        stream: true,
    });

    const currentCalls = new Map();
    let toolCalls = [];

    for await (const event of stream) {
        const evType = event.event_type;
        if (evType === 'step.start') {
            if (event.step.type === 'function_call') {
                currentCalls.set(event.index, {
                    id: event.step.id,
                    name: event.step.name,
                    arguments: ''
                });
                if (event.step.arguments) {
                    if (typeof event.step.arguments === 'object') {
                        currentCalls.get(event.index).arguments = JSON.stringify(event.step.arguments);
                    } else {
                        currentCalls.get(event.index).arguments = event.step.arguments;
                    }
                }
            }
        } else if (evType === 'step.delta') {
            if (event.delta.type === 'arguments') {
                if (currentCalls.has(event.index)) {
                    currentCalls.get(event.index).arguments += event.delta.partial_arguments;
                }
            } else if (event.delta.type === 'text') {
                process.stdout.write(event.delta.text);
            }
        } else if (evType === 'interaction.completed' || evType === 'interaction.complete') {
            toolCalls = Array.from(currentCalls.values()).map(call => ({
                type: 'function_call',
                id: call.id,
                name: call.name,
                arguments: call.arguments ? JSON.parse(call.arguments) : {}
            }));
            console.log('\nFinal tool calls ready to execute:');
            console.log(JSON.stringify(toolCalls, null, 2));
        }
    }
