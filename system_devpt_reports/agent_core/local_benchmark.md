## Bonsai-1.7B-1-bit on llama.cpp 

## Start Server first:
```bash
cd ~/Hello/llama.cpp
./build/bin/llama-server -m /home/manigupt/.ollama/models/blobs/sha256-3d7c6c90dd98717a203adb22d5eacd2581850e40aa5327e144b97766cae5f7e3 -t 2 -tb 4 -c 512 -b 64 --port 8080
```

## Test server from another terminal client:
```bash
curl http://127.0.0.1:8080/health
```

## Inference speeds
### -t 1 [ Prompt: 17.1 t/s | Generation: 10.6 t/s ]
### -t 2 [ Prompt: 27.5 t/s | Generation: 18.4 t/s ]
### -t 2 -tb 4 [ Prompt: 30.5 t/s | Generation: 17.2 t/s ]
### -t 3 [ Prompt: 30.1 t/s | Generation: 15.6 t/s ]
### -t 4 [ Prompt: 27.2 t/s | Generation: 14.2 t/s ]

- That's a useful result. 2 threads are clearly optimal for generation on your i3-1115G4. The important observation is that adding threads beyond 2 hurts decode speed. This is typical when you're hitting memory/cache or CPU resource constraints rather than pure compute limits.

- Your i3-1115G4 has **2 physical cores / 4 threads**. Hyperthreading isn't necessarily beneficial for LLM decode.This means: 2 threads for generation 4 threads for prompt processing. Prompt processing can potentially become faster without sacrificing your decode rate.

## TEST 1
- You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: Create a directory called src. Tool:
- User: Show me the contents of README.md. Model Result: READ_FILE
- User: Put "hello world" into test.txt. Model Result: WRITE_FILE
- User: Remove the old temporary directory. Model Result: DELETE_FILE
- User: What files are inside the tests directory?. Model Result: LIST_FILES
- User: Run pytest. Model Result: EXECUTE_COMMAND

## TEST 2
- You are a tool router.Available tools:CREATE_DIRECTORY(path),READ_FILE(path),WRITE_FILE(path,content),EXECUTE_COMMAND(command).Return ONLY JSON.User: Write "hello world" to /tmp/test.txt
- Result:{"tool":"WRITE_FILE","path":"/tmp/test.txt","content":"hello world"}
- User: Create a directory called "src/tools" Result:{"tool":"CREATE_DIRECTORY","path":"src/tools"}

## Model outputs:
> You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: Create a directory called tests.Tool:
CREATE_DIRECTORY
[ Prompt: 27.5 t/s | Generation: 15.1 t/s ]

> Create a directory called src
CREATE_DIRECTORY src
[ Prompt: 25.6 t/s | Generation: 13.8 t/s ]

> Show me the contents of README.md
I don't have the ability to show the contents of README.md. I cannot access or retrieve files from the system. If you need to view the contents of README.md, you would have to run the command `readme.md` on your system or use a tool to display the file.
[ Prompt: 25.7 t/s | Generation: 10.9 t/s ]

> You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: Show me the contents of README.md.Tool:
READ_FILE
[ Prompt: 28.6 t/s | Generation: 13.7 t/s ]

> You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: Put "hello world" into test.txt.Tool:
CREATE_DIRECTORY test.txt
[ Prompt: 24.7 t/s | Generation: 13.4 t/s ]

> You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: Remove the old temporary directory.Tool:
DELETE_FILE
[ Prompt: 24.3 t/s | Generation: 13.1 t/s ]

> You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: What files are inside the tests directory? Tool:
READ_FILE
[ Prompt: 23.0 t/s | Generation: 12.4 t/s ]

> You are a tool classifier. Output ONLY one tool name.Tools:CREATE_DIRECTORY,READ_FILE,WRITE_FILE,DELETE_FILE,LIST_FILES,EXECUTE_COMMAND.User: Run pytest. Tool:
RUN_PYTEST
[ Prompt: 25.4 t/s | Generation: 13.7 t/s ]

> You are a tool router.Available tools:CREATE_DIRECTORY(path),READ_FILE(path),WRITE_FILE(path,content),EXECUTE_COMMAND(command).Return ONLY JSON.User: Create a directory called "src/tools"
{
  "tool": "CREATE_DIRECTORY",
  "path": "src/tools"
}
[ Prompt: 22.4 t/s | Generation: 9.5 t/s ]

> You are a tool router.Available tools:CREATE_DIRECTORY(path),READ_FILE(path),WRITE_FILE(path,content),EXECUTE_COMMAND(command).Return ONLY JSON.User: Write "hello world" to /tmp/test.txt
{
  "tool": "WRITE_FILE",
  "path": "/tmp/test.txt",
  "content": "hello world"
}
[ Prompt: 24.8 t/s | Generation: 8.8 t/s ]

----------

This is actually a **very useful result** for your harness design. Bonsai is showing a clear distinction between **instruction-following/classification** and **free-form conversational behavior**.

### Results

| Task                                   | Result           |
| -------------------------------------- | ---------------- |
| Explicit classifier + create directory | ✅                |
| Bare "Create directory"                | ⚠️ Adds argument |
| Bare file read                         | ❌                |
| Explicit classifier + file read        | ✅                |
| Explicit classifier + write            | ❌ Wrong tool     |
| Explicit classifier + delete           | ✅                |
| Explicit classifier + list             | ❌ Wrong tool     |
| Explicit classifier + pytest           | ⚠️ Invents tool  |
| JSON create                            | ✅ Excellent      |
| JSON write                             | ✅ Excellent      |

So the important finding is:

> **Bonsai can perform structured tool routing, but you should not expose it to arbitrary conversational turns and expect reliable classification.**

### Your architecture should therefore be constrained

Don't do:

```text
User → Bonsai → "What do I do?"
```

Instead:

```text
                 Cloud LLM
                     │
             normalized command
                     │
                     ▼
                ┌─────────┐
                │  Bonsai │
                │ Router  │
                └────┬────┘
                     │
              strict JSON
                     │
                     ▼
              Deterministic
                harness
```

And give Bonsai **very few choices**.

Your worst result:

```text
Put "hello world" into test.txt
→ CREATE_DIRECTORY
```

is particularly important. But when explicitly instructed to produce JSON:

```json
{"tool":"WRITE_FILE","path":"/tmp/test.txt","content":"hello world"}
```

it got it exactly right.

That suggests **structured constrained output is much more suitable than plain classification**.

### I would change your local model's job

Don't ask it to understand the user's intent from scratch.

Have the cloud model produce something like:

```json
{"action":"write_file","path":"test.txt","content":"hello world"}
```

Then Bonsai's job becomes:

> Validate/normalize this into the exact internal tool schema.

Or, if you want Bonsai to classify:

```text
ACTION: WRITE
PATH: test.txt
CONTENT: hello world
```

→ deterministic parser → tool.

This dramatically reduces the intelligence required from Bonsai.

### Speed is actually quite good

Your JSON tests:

```text
CREATE: ~9.5 tok/s
WRITE:  ~8.8 tok/s
```

The generation speed is lower because the JSON output requires more generated tokens.

But you're only generating roughly **10–20 tokens**. That's still potentially a sub-second local operation.

And this is where your idea becomes interesting:

**Don't optimize Bonsai for 50 tok/s. Optimize it for <500 ms reliable tool routing.**

If we can get **95%+ accuracy with <500 ms median latency**, it could be a very useful local component of your harness.

The next experiment I'd recommend is much more rigorous: **50 tool-routing cases with exactly 8 tools**, including ambiguous/negative cases, and measure accuracy + latency. That will tell us whether Bonsai is genuinely useful or merely looks good on a few examples.

-------

### Results so far

| Test                | Accuracy | Median latency |      Prompt |
| ------------------- | -------: | -------------: | ----------: |
| Full JSON routing   |  **40%** |         ~1.82s | ~102 tokens |
| Minimal classifier  |  **60%** |         ~0.79s |  ~66 tokens |
| Few-shot classifier |  **80%** |         ~0.80s | ~125 tokens |

### What we've learned

* **Few-shot examples clearly improve accuracy:** 60% → **80%**.
* Latency is essentially unchanged at ~**0.8s**, despite nearly doubling prompt tokens. This suggests the cached prefix is helping significantly.
* Generation is extremely cheap: only **~3 tokens/request**.
* Errors are now concentrated:

  * `"Put ... into scripts/test.py"` → `EXECUTE_COMMAND`
  * `"Show everything in /home/..."` → `READ_FILE`
* The model is therefore **quite usable as a constrained classifier**, but 80% is not yet reliable enough for an autonomous tool router.
* Your original architecture looks promising: **cloud model generates intent → tiny local model classifies → deterministic harness executes**.

The next useful test isn't another larger prompt. We should test **30–50 semantically varied requests** with the current few-shot prompt to determine whether the 80% result generalizes or was simply favorable test wording.

One particularly interesting target is whether we can get **90%+ accuracy while keeping ~0.8s latency**.

----------

Yes. **Testing the Bonsai family is actually the most logical next experiment** because your current 1.7B 1-bit model is showing a very specific failure pattern. The larger/ternary models should tell us whether the problem is primarily **capacity** or **1-bit representation**.

PrismML's published benchmarks support that hypothesis: Ternary Bonsai substantially improves over the corresponding 1-bit models, especially on BFCLv3 (tool/function-calling related). For example, Ternary 4B scores 67.8 on BFCLv3 vs 48.0 for 1-bit 4B; Ternary 1.7B scores 51.0 vs 34.9 for 1-bit 1.7B. ([Hugging Face][1])

### What I'd expect on your classifier

| Model                 |   Memory | Expected classification | Expected speed on your i3 |
| --------------------- | -------: | ----------------------: | ------------------------: |
| **Bonsai 1.7B 1-bit** |  ~240 MB |              **70–85%** |              ~15–20 tok/s |
| **Ternary 1.7B**      |  ~440 MB |              **80–90%** |              ~10–17 tok/s |
| **Bonsai 4B 1-bit**   |  ~570 MB |              **85–92%** |               ~7–12 tok/s |
| **Ternary 4B**        | ~1.02 GB |              **90–95%** |               ~5–10 tok/s |
| **Bonsai 8B 1-bit**   | ~1.15 GB |             **90–95%+** |                ~3–7 tok/s |
| **Ternary 8B**        | ~1.75 GB |             **93–97%+** |                ~2–6 tok/s |

Those speed numbers are **rough estimates**, not published measurements for your i3-1115G4. The published model sizes are documented by PrismML; their 1.7B/4B/8B ternary GGUFs are approximately 0.44/1.02/1.75 GB. ([prismml.com][2])

### And I would add one non-Bonsai baseline

When your download limit resets, test **Qwen3-1.7B**.

PrismML's own published benchmark has Qwen3-1.7B at **66.57 average / 71.8 BFCLv3**, versus Ternary Bonsai 1.7B at **58.47 / 51.0**. ([Hugging Face][1])

So it gives us a fascinating comparison:

```text
                 Accuracy       Memory
Bonsai 1.7B       your test       0.24 GB
Ternary 1.7B      your test       0.44 GB
Qwen3 1.7B        your test       ~3.44 GB
```

Qwen3 may be much better at your specific routing task, while Bonsai wins enormously on memory.

------

This is **much better**. Your 8 GB machine is handling the server comfortably with the reduced context/batch settings.

### Current result

| Metric           |       Result |
| ---------------- | -----------: |
| RAM before       | ~2.7 GB used |
| RAM after server | ~3.2 GB used |
| Increase         |  **~0.5 GB** |
| Available RAM    |   **4.3 GB** |
| Swap used        |       1.3 GB |
| Accuracy         |      **80%** |
| Median latency   |   **782 ms** |
| Average latency  |   **756 ms** |
| Output           |    ~3 tokens |

So the previous **95% RAM usage was largely caused by the server configuration**, particularly the larger context/batch allocation, rather than the 248 MB model itself.

### This changes the model-size picture

You now have about **4.3 GB available RAM while Bonsai is running**.

That means I would be comfortable testing:

```text
Ternary Bonsai 1.7B   ~440 MB
1-bit Bonsai 4B       ~570 MB
Ternary Bonsai 4B     ~1 GB
1-bit Bonsai 8B       ~1.2 GB
Ternary Bonsai 8B     ~1.7 GB
```

The **4B models should be very comfortable**.

The 8B models should also fit, although inference speed will fall and the OS may start using more swap depending on how much memory your other applications consume.

### One important observation

Your latency is now remarkably consistent:

```text
556
823
763
780
822
887
668
622
785
852 ms
```

That's exactly what we want for a harness component.

And because the model only generates **3 tokens**, the ~750 ms latency is dominated by **prompt processing**, not generation.

Your next experiment should therefore be:

**Ternary Bonsai 1.7B → same server settings → exactly the same benchmark.**

That will give us a clean apples-to-apples comparison:

```text
                 Accuracy    Median latency    RAM
1-bit 1.7B       80%         782 ms            ~+0.5 GB
Ternary 1.7B     ???         ???               ???
```

Don't change the benchmark or server parameters between models. That will make the eventual **1.7B → 4B → 8B scaling curve** genuinely useful for deciding which model belongs in your harness.
