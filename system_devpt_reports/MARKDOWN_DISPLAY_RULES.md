# Markdown Display Rules for VS Code

Purpose: Make Markdown (`.md`) files easy to read and navigate in VS Code and other Markdown editors. Apply these rules when creating or editing project documentation.

## 1. General principles
- Optimize for clear scanning, not decorative formatting.
- Use standard GitHub-Flavored Markdown (GFM); avoid editor-specific syntax unless the project requires it.
- Keep source Markdown readable in plain-text mode as well as Preview.
- Use UTF-8 encoding and LF line endings.
- Do not rewrite technical meaning merely to improve formatting.

## 2. Headings and document structure
- Use exactly one `# H1` title per document.
- Use headings in order: `#`, `##`, `###`; do not skip levels for styling.
- Keep headings concise and descriptive; use sentence case.
- Add a blank line before and after headings.
- Use headings to create a navigable outline; avoid excessively deep nesting.

## 3. Paragraphs and spacing
- Keep paragraphs focused on one idea, usually 1–4 sentences.
- Put a blank line between paragraphs and between different block types.
- Prefer lists, tables, or short subsections over very long paragraphs.
- Avoid manual alignment with spaces; Markdown rendering differs across fonts and editors.
- Do not use repeated blank lines for visual spacing.

## 4. Lists
- Use `-` for unordered lists consistently.
- Use `1.` for ordered lists; let Markdown handle numbering.
- Indent nested list items by two spaces.
- Keep list items parallel in grammar and structure.
- Use task lists for actionable work: `- [ ] Pending` and `- [x] Done`.
- Avoid deeply nested lists; split complex material into subsections when practical.

## 5. Code and commands
- Use fenced code blocks with a language identifier, such as ` ```python`, ` ```bash`, or ` ```json`.
- Use inline backticks for filenames, paths, commands, identifiers, environment variables, and short code expressions.
- Keep commands copyable; do not include shell prompts such as `$` unless they are part of the command.
- Explain non-obvious commands before or after the code block.
- Never put secrets, API keys, passwords, or tokens in documentation.

## 6. Tables
- Use tables for compact comparisons or structured fields, not for long prose.
- Always include a header row and separator row.
- Keep cells concise; use bullets or subsections instead of large multi-paragraph cells.
- Do not use tables merely to force page layout.

## 7. Links, images, and references
- Use descriptive link text rather than “click here.”
- Use relative links for files inside the same repository where practical.
- Use meaningful image alt text.
- Ensure referenced paths and anchors actually exist; do not invent links.

## 8. Callouts and emphasis
- Use **bold** sparingly for key terms or important warnings.
- Use *italics* for light emphasis, not as a substitute for headings.
- Use blockquotes for genuine quotations or short notes.
- Use standard Markdown callout syntax only if the target renderer supports it; otherwise use plain headings such as `> **Note:** ...`.
- Avoid excessive emojis, all-caps text, and decorative separators.

## 9. File-specific conventions
- Put the document's purpose and scope near the top when they are not obvious from the title.
- For technical docs, prefer sections such as `Purpose`, `Prerequisites`, `Usage`, `Configuration`, `Examples`, `Troubleshooting`, and `Status` when relevant.
- For plans, distinguish current state, proposed changes, acceptance criteria, and unresolved questions.
- Include dates in ISO format (`YYYY-MM-DD`) when dates matter.
- Define acronyms on first use unless they are already standard in the project.
- Keep one source of truth for each fact; link to authoritative docs rather than duplicating long content.

## 10. VS Code editing and preview
- Use syntax that works in VS Code's built-in Markdown Preview and common GFM renderers.
- Prefer a single blank line between blocks; avoid HTML for basic formatting.
- Use Markdown Preview (`Ctrl+Shift+V`) to check the rendered result when making substantial documentation changes.
- If available in the project, run the configured Markdown linter/formatter; do not add new dependencies without approval.
- Respect repository-specific rules and existing conventions when they conflict with these defaults.

## 11. Suggested editor settings
These are optional user-level or workspace settings. Merge them into `.vscode/settings.json` only if the project does not already define conflicting preferences.

```json
{
  "editor.wordWrap": "on",
  "editor.wrappingIndent": "same",
  "editor.renderWhitespace": "selection",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,
  "[markdown]": {
    "editor.defaultFormatter": "vscode.markdown-language-features",
    "editor.wordWrap": "on",
    "editor.quickSuggestions": {
      "comments": "off",
      "strings": "off",
      "other": "on"
    }
  }
}
```

## 12. Agent workflow
Before finishing Markdown work:
1. Check heading hierarchy and blank-line spacing.
2. Check that code fences are closed and use language labels.
3. Check links, file paths, and table structure.
4. Preserve existing content and project conventions.
5. Review the rendered preview for substantial changes.
6. Report any formatting rules that could not be followed and why.

## Priority
Follow, in order:
1. Explicit user instructions.
2. Repository-specific `AGENTS.md`, `CONTRIBUTING.md`, or documentation rules.
3. This file's defaults.
4. General Markdown conventions.
