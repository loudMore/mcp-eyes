# Skills for mcp-eyes

A single comprehensive [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) covering the full mcp-eyes lifecycle.

## `mcp-eyes`

Triggers on any mcp-eyes-related interaction:

- **Install / setup**: user asks to install mcp-eyes, give the agent vision capability, or pastes the GitHub URL
- **Daily use**: user sends an image path/URL while `eyes` is configured, or you're about to call any `mcp__eyes__*` tool

Two parts inside the skill:

- **Part A — Install & Configure**: 7-step automated install using the CLI (`presets` → `config` → `init` → `doctor` → restart). User only provides the vision API key.
- **Part B — Daily Use**: collaboration patterns between the reasoning model and the eyes-only vision model. Decision tree, scene picking, question writing patterns + anti-patterns, multi-step workflows (debugging / UI regression / game balancing / code-from-screenshot), multi-image batching, cost/cache awareness, error recovery, and **when NOT to call mcp-eyes**.

## Install the skill

Skills live in `~/.claude/skills/` (user-scope) or `<project>/.claude/skills/` (project-scope).

```bash
# User-scope (recommended): install once, all your projects benefit
cp -r skills/mcp-eyes ~/.claude/skills/

# Or project-scope: only this project picks it up
mkdir -p .claude/skills && cp -r skills/mcp-eyes .claude/skills/
```

Discoverable to Claude Code automatically — no restart needed. Type `/skills` in Claude Code to verify it appears.

## Why one skill instead of two

Earlier drafts split this into `install-mcp-eyes` and `use-mcp-eyes`. Splitting added friction (two cp commands, two trigger descriptions to maintain) without buying clarity — once a user has installed the skill, they want it to handle everything mcp-eyes related, not pick one of two cousins. So it's one skill with two clearly labeled sections inside.

## Authoring notes

A skill is a single `SKILL.md` with YAML frontmatter (`name`, `description`). The `description` is what Claude reads to decide whether to invoke — keep it specific, trigger-rich, and broad enough to cover all relevant intents. The body is loaded into context only when the skill fires.

PRs welcome for additional skills (e.g. `tune-mcp-eyes-cache`, `add-vision-provider`, `migrate-to-mcp-eyes`).
