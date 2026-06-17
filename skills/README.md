# Skills for mcp-eyes

Companion [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) that make using mcp-eyes more ergonomic. Two skills cover the full lifecycle: getting it installed, and using it well day-to-day.

## Available skills

### `install-mcp-eyes`

Triggers when a user asks to install mcp-eyes, attach a vision model to their text-only reasoning model, or pastes the mcp-eyes GitHub link. Walks through the 7-step automated install (pip → presets → config → init → doctor → restart) using the CLI subcommands. The user only provides their vision API key.

### `use-mcp-eyes`

Triggers whenever you're about to call any `mcp__eyes__*` tool, or whenever the user gives you an image path/URL and `eyes` is available. This is the **day-to-day collaboration playbook** between the main reasoning model and the eyes-only vision model. Covers:

- Decision tree: which tool (`describe_image` / `compare_images` / `extract_text`), which `scene`
- `question` writing patterns that work, plus a list of anti-patterns that will silently fail
- Multi-step workflows: debugging from a screenshot, UI regression, game balancing, code-from-screenshot
- Multi-image batching strategy
- Cost / cache awareness — same image + same question is free, retries with `bypass_cache: true` are not
- Error recovery — what to do when the vision model says "Not visible in image" or the API errors
- **When NOT to call mcp-eyes** (the user already described the image in words, the image was already described earlier in conversation, etc.)

Without this skill, agents tend to: ask the vision model "why is this failing" (which it can't answer by design), call `describe_image` once per question on the same image (cost), or echo the raw description back to the user instead of synthesizing.

## Installing skills locally

Skills live in `~/.claude/skills/` (user-scope) or `<project>/.claude/skills/` (project-scope).

```bash
# User-scope (recommended): one-time install, all your projects benefit
cp -r skills/install-mcp-eyes skills/use-mcp-eyes ~/.claude/skills/

# Or project-scope: only this project picks them up
mkdir -p .claude/skills && cp -r skills/install-mcp-eyes skills/use-mcp-eyes .claude/skills/
```

After copying, the skills are discoverable to Claude Code automatically — no restart needed. Type `/skills` in Claude Code to verify they appear.

## How these skills earn their keep

Without the install skill: the user has to manually point their agent at `AGENT_SETUP.md`, the agent improvises, JSON gets typo'd, the user re-runs three times.

Without the use skill: the agent calls `describe_image` with vague questions like "what's wrong here", gets a "Not visible in image" response for the diagnostic part, doesn't realize that's by design, and the user thinks the vision model is dumb. With the use skill, the agent knows to ask "what does the red box show" instead of "why is the red box red".

## Authoring notes

Each skill is a single `SKILL.md` file with YAML frontmatter (`name`, `description`). The `description` is what Claude reads to decide whether to invoke — keep it specific and trigger-rich. The body is plain Markdown loaded into context only when the skill fires.

Contributions for additional skills welcome via PR. Ideas: `tune-mcp-eyes-cache` (for power users), `add-vision-provider` (PR-style preset additions), `migrate-vision-mcp` (move from a custom MCP to mcp-eyes).

