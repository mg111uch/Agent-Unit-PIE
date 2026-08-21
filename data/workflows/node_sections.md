# Node Sections — Docs for Graph Editor

Reference document for associating markdown sections to graph nodes via the Docs sidepanel (`10th tuple = file#slug`). Pick a file + section in the Docs panel to link it to the selected node.

## Overview

The graph editor supports orthogonal links on each node:
- `ref` (9th tuple) → subgraph JSON in `data/workflows/`
- `mdRef` (10th tuple) → `data/workflows/<file>.md#<slug>`

Use the Docs panel to browse files in `data/workflows/` and their headings. The blue dashed ring and `📄 file#slug` caption indicate a docs link.

## Node Shapes

Describes the three built-in shapes. Associate a shape node to its definition section.

### Rectangle — Task

Rectangle (`rect`) is the default task/action node. Size `150×70`, fill from palette. Use for steps, actions, and processing blocks.

Example prompts: `R` tool, drag to place, double-click to edit label.

### Diamond — Decision

Diamond (`diamond`) is a decision/branch node. Size `120×80`. Use for `?` branches, conditions, and `Yes/No` edges.

Keep labels short; edge labels carry branch conditions.

### Ellipse — State

Ellipse (`ellipse`) marks start/end states. Size `150×70`. Use for `START`, `STOP`, or milestone states. Typically `fill #d4f0c0` (start) / `#f0c0c0` (end).

## Example Workflow

Example: `Session START (ellipse) → Read TASK (rect) → Decision (diamond) → Execute (rect) → STOP (ellipse)`. Link each node to its corresponding section above (e.g., `START` → `Ellipse — State`, decision → `Diamond — Decision`).

## Tips

- Keep `file#slug` stable: prefer `##` headings over `###` for link targets.
- Rename headings → update `slug`; old `mdRef` remains but shows as legacy option until re-linked.
- Docs files are intentionally limited to `data/workflows/*.md` (like `GET /api/graphs`); add new `.md` there to appear in the Docs dropdown.
