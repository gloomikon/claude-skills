# Skills catalog

Skills I have reviewed. **Rule:** only `caveman`, `i-have-adhd`, `ponytail` and `teach` are global (`~/.claude/skills/`). Everything else is
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
| `ponytail` | github.com/DietrichGebert/ponytail (MIT), `skills/ponytail/SKILL.md` only, without the Node hooks | Lazy-senior coding: YAGNI, reuse, stdlib and native features first, shortest working diff, root-cause fixes | global |
| `teach` | github.com/mattpocock/skills (MIT), `skills/productivity/teach` | Multi-session teaching of any topic: mission, HTML lessons, spaced retrieval, learning records. Manual `/teach`; use it in a dedicated folder per topic | global |
| `improve-codebase-architecture` + `codebase-design` | github.com/mattpocock/skills (MIT) | Manual `/improve-codebase-architecture`: finds shallow modules and proposes deepening refactors as an HTML report with before/after diagrams | large codebases |
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
| `web-quality-skills` | github.com/addyosmani/web-quality-skills (MIT) | Lighthouse / Core Web Vitals; for a web performance pass |
| `archify` | github.com/tt-a1i/archify (MIT) | interactive HTML architecture diagrams; 300+ scripts, and `graphify` already maps code |
| `stop-slop` | github.com/hardikpandya/stop-slop | `humanizer` already covers it |
| `frontend-slides` | github.com/zarazhangrui/frontend-slides | slides as code; not needed now |
| `awesome-design-md`, `design.md` | github.com/VoltAgent/awesome-design-md, github.com/google-labs-code/design.md | DESIGN.md format; `ios-delight` writes `docs/DESIGN.md` itself |
| Magic UI, Smooth UI, Unlumen UI, Retro UI | web component libraries | for the web app, together with `taste-skill` |
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
- **mattpocock/skills** (278k★): only `teach`, `improve-codebase-architecture` and `codebase-design` were taken. `git-guardrails-claude-code` was rejected because it blocks every `git push`, and the auto-mode classifier already stops destructive git. **addyosmani/agent-skills** (102k★, has hooks): planning, TDD, debugging,
  review, specs. `superpowers` and our reviewer agents already cover this.
- **everything-claude-code** (affaan-m, 274k★): the full install is 5,700+ files, 1,000+ skills and auto hooks.
  Only 5 agents were taken (see Agents).
- **swift-ios-skills** (dpearson2699): non-standard license; overlaps with `ios-delight`.
- **ios-ui-craft** (vabole/apple-skills): the author moved it to `disabled-skills`.
- **open-design / swiftui-design** (nexu-io): `ios-delight` covers it.
- **gpt-tasteskill**, **imagegen-frontend-mobile/web**, **brandkit**, **image-to-code** (in taste-skill): need image generation (Codex).
- **Emil Kowalski** `apple-design`, `mobile-native`, `animate-expo`, `ask-sonner`, `prototype`: web or React Native only.
- **Login security reel** (5 vibe-coded login holes): turned into a login audit TODO in the web app.
- **"5 content formats for user acquisition" reel**: applies only to the YouTube channel (Shorts). The other projects are personal or monetized differently.
- GetLayers.ai: a paid prompt library; Claude writes such pages directly.
