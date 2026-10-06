---
name: ios-delight
description: >-
  Makes SwiftUI apps look and feel alive instead of generic: a visual direction first, then custom
  components, motion, haptics, sound and celebrations. Use when building or redesigning any SwiftUI
  screen, when the owner says the app is "boring", "primitive", "plain", "looks like a demo", "no
  animations", "make it beautiful", "add juice", or asks for custom elements, transitions, haptics,
  SF Symbol effects, Liquid Glass, typography or palette work.
---

# iOS Delight

One entry point that combines three MIT skill packs (see `SOURCES.md`). Work in this order. Do not
jump to code before step 1 is done for the screen at hand.

## 0. Know the project

- Read the project's `CLAUDE.md` and `docs/DESIGN.md` (if it exists) first. Project rules win over
  anything in these guides.
- Check the deployment target (`project.yml` / build settings). Guard every newer API with
  `if #available` / `@available` and give a good fallback, for example `PhaseAnimator` and
  `KeyframeAnimator` need iOS 17, `.glassEffect()` needs iOS 26, SF Symbols draw effects need iOS 26.
- Respect Reduce Motion, Dynamic Type, VoiceOver and both color schemes. Motion is never the only
  way information reaches the user.

## 1. Direction: what should this app feel like

Read `taste/GUIDE.md` (and `taste/references/apple-design-dna.md`).

- Do the 0.5-second test and the design-thinking phase for the screen.
- For a new app, or for a redesign of an existing one, write the direction once to
  `docs/DESIGN.md`. Include the user and the feeling, a palette, type, shape language, 3–5
  signature moments, and what to avoid. Generate and check the palette with
  `python3 -I taste/scripts/generate_palette.py` and `verify_palette.py`. Show the direction to the
  owner before building on it.
- "Boring" usually means there is no visual shape and no signature moment. A different list style
  does not fix it.

## 2. Custom components and motion

- `motion/GUIDE.md` gives complete, premium components in the legendary-Animo style: press
  feedback, springs, drag with resistance, carousels, card stacks, liquid and goo effects, loaders,
  toasts and tab bars. Use it when building a custom element.
- `apple-design/animation-patterns/` is the API reference: spring generations, Phase and Keyframe
  animators, transitions, matched geometry, SF Symbol effects, completions.
- `apple-design/liquid-glass/` covers Liquid Glass (iOS 26+). `apple-design/sf-symbols/` and
  `apple-design/typography/` cover icons and type.
- One orchestrated moment beats many scattered effects. Every animation must answer a user action
  or mark a meaningful event.

## 3. Feel: celebrations, haptics, sound

Read `apple-design/game-feel/GUIDE.md`. Design celebrations for the moments that matter (a correct
answer, a streak, a finished lesson), use a small consistent haptic vocabulary, and add sound only
with a mute path. Run `apple-design/game-feel/feedback-audit.md` over the app's events: does every
meaningful event reach the user, on the right channel?

## 4. Words

`apple-design/ux-writing/GUIDE.md` for button labels, empty states, errors and alerts.

## 5. Check it

Build. Run it in the simulator and take before and after screenshots, or a short recording for
motion. Check light and dark mode, the largest Dynamic Type size and Reduce Motion. Then follow the
project's usual review loop.
