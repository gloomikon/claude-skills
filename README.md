# Claude Skills

Custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Installation

Add the marketplace:
```
/plugin marketplace add gloomikon/claude-skills
```

Install skills:
```
/plugin install swiftui@gloomikon-claude-skills
/plugin install core-data@gloomikon-claude-skills
/plugin install ios-new-project@gloomikon-claude-skills
/plugin install ios-delight@gloomikon-claude-skills
```

## Skills

- **SwiftUI** — based on "Thinking in SwiftUI" by objc.io
- **Core Data** — based on "Core Data" by objc.io + production patterns
- **iOS Delight** — alive SwiftUI apps: design direction, custom components, motion, haptics (built from 3 MIT packs, licenses inside)
- **iOS New Project** — create a new iOS project from KOMA template with pre-configured skills and MCP

## Swift Concurrency (by [Antoine van der Lee](https://github.com/AvdLee))

```
/plugin marketplace add AvdLee/Swift-Concurrency-Agent-Skill
/plugin install swift-concurrency@swift-concurrency-agent-skill
```

## Apple Docs MCP

MCP server for Apple documentation ([repo](https://github.com/kimsungwhee/apple-docs-mcp)):
```bash
claude mcp add --scope project apple-docs -- npx -y @kimsungwhee/apple-docs-mcp@latest
```

## Catalog and new machine

- [`CATALOG.md`](CATALOG.md) — every skill I have reviewed: what it does, the source, where to use it, and what I rejected.
- [`NEW-MACHINE.md`](NEW-MACHINE.md) — setup on a new laptop; give it to Claude.
