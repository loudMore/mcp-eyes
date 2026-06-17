# skills-vision-extension

The Claude Code skill bundled with [vision-extension](https://github.com/loudMore/vision-extension).

## Contents

```
skills-vision-extension/
└── vision-extension/
    └── SKILL.md         # the skill itself
```

## Install (one command)

```bash
cp -r vision-extension ~/.claude/skills/
```

After copying, type `/skills` in Claude Code to verify it appears.

For project-scope (only this project picks it up):

```bash
mkdir -p .claude/skills && cp -r vision-extension .claude/skills/
```

## What the skill does

The single `vision-extension` skill covers the full vision-extension lifecycle:

- **Install & configure** — triggered by *"install vision-extension"* / *"install vision-extension"* / pasting the GitHub URL → walks the agent through the deterministic 7-step CLI install. The user only provides the vision API key.
- **Daily use** — triggered any time the agent is about to call `mcp__vision-extension__*` tools or the user sends an image path → teaches the reasoning model how to talk to the describe-only vision model effectively, including persona-specific patterns for game devs, frontend devs, designers, data analysts, DevOps, QA, educators, hardware/makers, localization, researchers, PM/business.

Without this skill, an agent installing vision-extension for the first time tends to hand-write JSON (typos), miss steps, or use vague `question` strings the describe-only vision model will refuse. With the skill, the entire flow is deterministic.

## Authoring notes

A skill is a single `SKILL.md` with YAML frontmatter (`name`, `description`). The `description` is what Claude reads to decide whether to invoke — keep it specific, trigger-rich, and broad enough to cover all relevant intents. The body is loaded into context only when the skill fires.

PRs welcome for additional skills.
