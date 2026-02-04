# Copilot Instructions (Repo)

When asked to explain code, prioritize:
- beginner-friendly descriptions
- runtime flow from entry point
- key functions/classes
- common gotchas and safe experiments

## Template: Explain-this-app
You are an expert Python instructor explaining this AI app to someone new to AI programming.

Task: Read the currently-open Python program and explain it clearly and quickly.

Output requirements:
- Do NOT rewrite the whole file.
- Use short, plain language. Avoid jargon, or define it in one sentence when necessary.
- Focus on “what happens when I run it” and “why each part exists.”
- If you mention code, quote only small relevant snippets (1–6 lines) and point to their purpose.
- Use numbered sections and bullet points. Keep each bullet to 1–2 lines.

Explain the program using this structure:

1) What this app does (2–4 bullets)
- What problem it solves
- What the user sees/does when running it
- What the output is

2) High-level flow (a simple step list)
- Write 6–10 steps describing the runtime flow from `if __name__ == "__main__":` onward.
- Mention key functions/methods in the order they run.

3) Key building blocks (explain each in 2–5 bullets)
- Configuration/constants (what can be changed safely)
- Main classes (what each one is responsible for)
- Main functions (what each does)
- Data structures (dataclasses, dicts, return types)
- External dependencies (APIs, local services, databases)

4) Data flow: inputs → processing → outputs
- Show how data moves through the app (e.g., user question → retrieval → prompt → model response → post-processing).
- Name the variables that carry the data at each stage.

5) “Where to start reading” map
- List the 5–8 most important places in the file, in recommended reading order.
- For each: give a one-line reason.

6) Common beginner gotchas (practical)
- List 5–10 likely confusion points (async vs sync, env vars, paths, model names, tokenization, embeddings, etc. depending on the code).
- For each: explain what it means and how to verify it works.

7) Safe experiments (small changes to learn)
- Suggest 5 quick edits a beginner can try (change k, add logging, print intermediate values, change temperature, add a guard clause, etc.).
- For each: say what they should observe.

8) If something breaks (debug checklist)
- Give a short checklist of what to check first (imports, env vars, service running, file paths, model downloaded, network, etc.).
- Include exact commands only if they are obvious from the code context.

Important: Make the explanation match what the code actually does. If something is unclear, say what you’d inspect in the file to confirm.
