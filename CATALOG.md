# Skills catalog

Skills I have reviewed. **Rule:** only `caveman` and `i-have-adhd` are global (`~/.claude/skills/`). Everything else is
copied into each project's `.claude/skills/<name>/` (or enabled per project as a plugin), so a project
gets only what fits its stack. Before installing anything new: read the whole skill (SKILL.md,
scripts, hooks, settings) and check its license. Install it only after that.

## In use

| Skill | Source | What it does | Use for |
|---|---|---|---|
| `ios-delight` | this repo, `skills/ios-delight` (built from 3 MIT packs, see its `SOURCES.md`) | Alive SwiftUI apps: visual direction first, then custom components, motion, haptics, sound, celebrations | iOS apps |
| `swiftui`, `core-data` | this repo | SwiftUI and Core Data, based on objc.io books | iOS apps (enable as plugin) |
| `ios-new-project` | this repo | New iOS project from the KOMA template | projects hub only |
| `ios-simulator-skill` | github.com/conorluddy/ios-simulator-skill | Scripts: build, simulator, UI navigation, accessibility | iOS apps |
| `wwdc` | github.com/superwall/skills, `skills/wwdc` | Search and cite WWDC sessions | iOS apps |
| `graphify` | `graphify` CLI (`graphify install`) | Knowledge graph of a codebase; PreToolUse hooks `graphify hook-guard` | large codebases only |
| `remotion-best-practices` | github.com/remotion-dev/skills, `skills/remotion-best-practices` (router; already contains all 12 sub-skills, so do not add them separately) | Official Remotion rules: markup, rendering, captions, audio, maps, Studio | video made with Remotion |
| `humanizer` | github.com/blader/humanizer (MIT) | Removes signs of AI writing from prose | scripts, copy |
| `taste-skill`, `redesign-skill` | github.com/Leonxlnx/taste-skill (MIT), `skills/taste-skill`, `skills/redesign-skill` | Anti-generic web design; redesign audits and improves existing UI without a rewrite. **Web only** (CSS/Tailwind/React) | web apps |
| `replica-recon`, `replica-entrepreneur` | github.com/Jakeschincariol/replica-skill (MIT) | Reverse-engineer a competitor app; mine its public reviews for what users hate and miss | projects hub: new product research |
| `i-have-adhd` | github.com/ayghri/i-have-adhd (MIT) | Answers shaped for an ADHD reader: next action first, numbered steps, state restated every turn, concrete time estimates, wins made visible. Always on via a SessionStart hook; off with "stop adhd mode" | global |
| `caveman` | local | Terse answer style; a SessionStart hook loads it | global |

## Worth a look later

| Skill | Source | Why not yet |
|---|---|---|
| `supabase-postgres-best-practices` | github.com/supabase/agent-skills | for Supabase backends |
| `vercel-react-best-practices`, `web-design-guidelines` | github.com/vercel-labs/agent-skills | for React / Next.js |
| `mobile-ios-design` | github.com/wshobson/agents, `plugins/ui-design/skills/mobile-ios-design` | HIG basics; `ios-delight` covers more |
| `hyperframes` | github.com/heygen-com/hyperframes (Apache-2.0) | HTML-to-video renderer; Remotion is already in use |
| `postiz` | github.com/gitroomhq/postiz-app (AGPL, self-host) | post scheduler for many networks; needs a paid server |
| VoiceStudio | github.com/debpalash/VoiceStudio (AGPL) | local voice cloning and dubbing; each model has its own license |
| `diagram-design` | github.com/cathrynlavery/diagram-design | editorial diagrams (HTML) |
| `replica-*` (other 9) | github.com/Jakeschincariol/replica-skill | rebuild a clone on Next.js, Postgres, Stripe and Resend |

## Reviewed, not taken

- **OpenMontage** (calesthio, AGPL): a large video "studio", much of it tied to paid APIs. A few ideas
  were borrowed and rewritten, not copied.
- **ui-ux-pro-max**, **impeccable**: heavy (hundreds of scripts, hooks); overlap with `frontend-design`.
- **Understand-Anything**: duplicates `graphify`.
- **skillry.dev** marketplace: browser-authorized CLI, skills can change server-side.
- Reels promising "$5000 services" with pipecat, cline, anything-llm, crewAI, browser-use, InfiniteTalk:
  either already covered by Claude Code or off-topic.
- GetLayers.ai: a paid prompt library; Claude writes such pages directly.
