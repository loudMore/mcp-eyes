# Skills for mcp-eyes

Companion [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that make using mcp-eyes more ergonomic.

## Available skills

### `install-mcp-eyes`

Triggers when a user asks to install mcp-eyes, attach a vision model to their text-only reasoning model, or pastes the mcp-eyes GitHub link. Walks through the 7-step automated install (pip → presets → config → init → doctor → restart) using the CLI subcommands. The user only provides their vision API key.

## Installing skills locally

Skills live in `~/.claude/skills/` (user-scope) or `<project>/.claude/skills/` (project-scope).

```bash
# User-scope (recommended): one-time install, all your projects can use it
cp -r skills/install-mcp-eyes ~/.claude/skills/

# Or project-scope: only this project can use it
mkdir -p .claude/skills && cp -r skills/install-mcp-eyes .claude/skills/
```

After copying, the skill is discoverable to Claude Code automatically — no restart needed. To verify, type `/skills` in Claude Code.

## How a Claude Code skill helps here

Without the skill, the user must remember to point their agent at `AGENT_SETUP.md` or paste the mcp-eyes URL. With the skill installed, **any phrasing that matches the trigger description** ("install mcp-eyes", "give you eyes", "set up vision", "I want my model to see images") routes the agent into the deterministic install flow — no improvisation, no JSON typos, no missed steps.

## Authoring notes

The skill is a single `SKILL.md` file with YAML frontmatter (`name`, `description`). The description is what Claude reads to decide whether to invoke — keep it specific and trigger-rich. The body is plain Markdown that gets loaded into the model's context only when the skill fires.

Contributions for additional skills (e.g. `tune-mcp-eyes-cache`, `add-vision-provider`) welcome via PR.
