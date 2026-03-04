# Claude Skills

Custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Structure

Each skill is a standalone plugin:

```
skills/
├── my-skill/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   └── skills/
│       └── my-skill/
│           ├── SKILL.md
│           ├── references/   (optional)
│           ├── scripts/      (optional)
│           └── assets/       (optional)
```

## Installation

To install a skill, symlink the plugin directory into your Claude plugins folder:

```bash
ln -s /path/to/skills/my-skill ~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/my-skill
```

## Creating a New Skill

1. Create a new directory under `skills/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add `skills/<skill-name>/SKILL.md` with the skill prompt
4. Symlink to install locally

See the [Claude Code docs](https://docs.anthropic.com/en/docs/claude-code) for more details on skill authoring.
