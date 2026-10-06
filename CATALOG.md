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
| `emil-design-eng`, `animate`, `review-animations`, `find-animation-opportunities`, `pick-ui-library` | github.com/emilkowalski/skills (MIT) | Emil Kowalski's design engineering: UI polish, when and how to animate, animation review, finding missing motion, choosing a UI library. **Web** (CSS/React) | web apps |
| `break-ui` | same | Breaks UI with worst-case data: long names, empty states, huge counts, long translations. Framework-agnostic | web and iOS apps |
| `replica-recon`, `replica-entrepreneur` | github.com/Jakeschincariol/replica-skill (MIT) | Reverse-engineer a competitor app; mine its public reviews for what users hate and miss | projects hub: new product research |
| `i-have-adhd` | github.com/ayghri/i-have-adhd (MIT) | Answers shaped for an ADHD reader: next action first, numbered steps, state restated every turn, concrete time estimates, wins made visible. Always on via a SessionStart hook; off with "stop adhd mode" | global |
| `caveman` | local | Terse answer style; a SessionStart hook loads it | global |

## Agents (per project, `.claude/agents/`)

| Agent | Source | What it does | Use for |
|---|---|---|---|
| `swift-reviewer` | github.com/affaan-m/everything-claude-code (MIT), `agents/` | Swift review: safety (force unwrap, `try!`), concurrency, memory, protocol design | iOS apps |
| `swift-build-resolver` | same | Fixes Swift/Xcode/SPM build errors with minimal changes | iOS apps |
| `kotlin-reviewer` | same | Kotlin review | Android apps |
| `typescript-reviewer` | same | TypeScript review | web apps |
| `silent-failure-hunter` | same | Finds swallowed errors, empty catches, fallbacks that hide failures | web apps, backends |

Own reviewers: the library is in the owner's private dotfiles (`~/.dotfiles/claude/agents/`). Copy them into a project's `.claude/agents/` by stack. Nothing is global.

| Agent | Put into |
|---|---|
| `verifier`, `code-critic`, `plan-challenger` | every project with code |
| `ux-critic`, `perf-auditor` | apps with a UI |
| `db-auditor` | projects with a database or local store |
| `security-auditor` | auth, payments, OAuth, webhooks, secrets, user data |
| `parity-checker` | products with several clients (iOS, Android, web, contracts) |
| `release-gatekeeper` | apps that ship to users (App Store, Play, TestFlight, production web) |
Not taken from everything-claude-code: the full install (5,700+ files, 1,000+ skills, auto-running hooks). It is too heavy for every session's context.

## Updates

`sources.json` pins every third-party skill and agent to the commit that was reviewed.
Run `python3 tools/check-updates.py` to see which ones changed upstream; it prints a compare link.
To update: read the diff, then copy the new version to every place in `installed_in` and bump `commit`. Never update blindly.

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
