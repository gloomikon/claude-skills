---
name: swiftui
description: >
  SwiftUI development expert grounded in deep understanding of view trees, state management,
  layout algorithm, animations, environment, and the render tree. Use this skill whenever working
  with SwiftUI views, layouts, state, bindings, animations, transitions, custom layouts, or
  any iOS/macOS UI code using SwiftUI. Also trigger when the user mentions SwiftUI, @State,
  @Observable, @Binding, VStack, HStack, ZStack, .animation, .transition, GeometryReader,
  or any SwiftUI modifier.
---

# SwiftUI Development Guide

Based on "Thinking in SwiftUI" by Chris Eidhof & Florian Kugler. The core thesis: understanding
how your code translates into **view trees** is essential for working correctly with SwiftUI.

For detailed reference on specific topics, read the corresponding file in `references/`:
- `references/view-trees.md` — View trees, render trees, identity, conditionals
- `references/state.md` — @State, @Observable, @Binding, property wrappers, debugging
- `references/layout.md` — Layout algorithm, leaf views, modifiers, stacks, scroll views
- `references/animations.md` — Property animations, transitions, keyframes, Animatable protocol
- `references/advanced.md` — Environment, Layout protocol, preferences, matched geometry

---

## Critical Rules (Always Apply)

### 1. Never Use `applyIf` — Use Ternary Operators

Conditional modifier helpers introduce `ConditionalContent` branches, breaking view identity.

```swift
// BAD — creates two separate view identities
Text("Hello").applyIf(highlighted) { $0.background(.yellow) }

// GOOD — single stable identity
Text("Hello").background(highlighted ? .yellow : .clear)
```

Most modifiers accept optionals, booleans, or zero values: `bold(isBold)`, `padding(0)`, `foregroundColor(nil)`.

### 2. Always Make @State Private, Initialize Inline

```swift
// CORRECT
@State private var count = 0

// WRONG — initializer only sets initial value, ignored after node exists
@State private var count: Int
init(count: Int) { _count = State(initialValue: count) }
```

Views have no identity at init time. The initial value is only used when the render tree node is first created.

### 3. @Observable (iOS 17+) — Prefer Over ObservableObject

```swift
@Observable final class Model {
    var value = 0  // Property-level tracking, automatic
}

// View owns the object → @State
@State private var model = Model()

// Object passed from outside → plain property
var model: Model
```

No `@ObservedObject` or `@StateObject` needed with `@Observable`. Observation is automatic when properties are accessed in `body`.

### 4. Layout: The Child Decides Its Own Size

The parent proposes, the child reports back. The parent **cannot** override the child's reported size.

```swift
// Proposal chain: parent → modifier → child → reports back
Text("Hello").padding(10).background(Color.teal)
// 1. background proposes to padding
// 2. padding subtracts 10pt, proposes to Text
// 3. Text reports exact needed size
// 4. padding adds 10pt, reports back
// 5. background proposes Text's padded size to Color
```

### 5. Prefer overlay/background Over ZStack

ZStack: all subviews influence its size (union of frames).
overlay/background: only primary subview determines size.

```swift
// Use when secondary view should NOT affect layout
Text("Hello")
    .padding()
    .background(Color.teal)        // teal doesn't affect layout
    .overlay(alignment: .topTrailing) {
        Badge().fixedSize()         // badge doesn't affect layout
    }
```

### 6. Use .frame(maxWidth: .infinity) Instead of Spacer Hacks

```swift
// PREFERRED — no minimum-length edge case
Text("Right-aligned").frame(maxWidth: .infinity, alignment: .trailing)

// AVOID — Spacer has a minimum length that steals space
HStack { Spacer(); Text("Right-aligned") }
```

Two essential frame patterns:
- `.frame(maxWidth: .infinity)` — at least as wide as proposed
- `.frame(minWidth: 0, maxWidth: .infinity)` — exactly as wide as proposed

### 7. Animations Require Stable View Identity

```swift
// BAD — if/else creates ConditionalContent, triggers transition instead of animation
if flag {
    rect.frame(width: 200, height: 100)
} else {
    rect.frame(width: 100, height: 100)
}

// GOOD — ternary keeps identity stable, enables property animation
rect.frame(width: flag ? 200 : 100, height: 100)
```

### 8. Transitions Need External Animation

```swift
// WRONG — animation inside the conditional subtree
if flag { Rectangle().transition(.slide).animation(.default, value: flag) }

// CORRECT — animation wraps from outside
VStack {
    if flag { Rectangle().transition(.slide) }
}.animation(.default, value: flag)
```

### 9. GeometryReader Belongs in overlay/background

GeometryReader unconditionally accepts proposed size, disrupting layout if wrapping content.

```swift
// SAFE — doesn't affect primary view's layout
myView.background {
    GeometryReader { proxy in
        Color.clear.preference(key: SizeKey.self, value: [proxy.size])
    }
}
```

### 10. Debug Layout with .border(), Debug State with _printChanges()

```swift
// Layout debugging
Text("Hello").padding().border(.red)

// State debugging — logs WHY body re-executed
var body: some View {
    let _ = Self._printChanges()  // prints: _value, @self, or @identity
    // ...
}
```

---

## Property Wrapper Decision Guide

| Need | Pre-iOS 17 | iOS 17+ |
|---|---|---|
| Private value state | `@State private var x = ...` | `@State private var x = ...` |
| External value (read/write) | `@Binding var x` | `@Binding var x` |
| Private object state | `@StateObject private var m = M()` | `@State private var m = M()` (with `@Observable`) |
| External object | `@ObservedObject var m` | `var m: M` (plain property, `@Observable`) |
| Create binding to @Observable | N/A | `@Bindable var m` or `Bindable(m).prop` |
| Read environment value | `@Environment(\.key)` | `@Environment(\.key)` |
| Read environment object | `@EnvironmentObject var m` | `@Environment var m: M?` (with `@Observable`) |

---

## Quick Reference: Common Patterns

### Badge with Alignment Guides
```swift
extension View {
    func badge<B: View>(@ViewBuilder _ badge: () -> B) -> some View {
        overlay(alignment: .topTrailing) {
            badge()
                .alignmentGuide(.top) { $0.height / 2 }
                .alignmentGuide(.trailing) { $0.width / 2 }
        }
    }
}
```

### Custom Environment Key (3-Step Pattern)
```swift
// 1. Define key
enum AccentKey: EnvironmentKey { static var defaultValue: Color = .blue }
// 2. Extend EnvironmentValues
extension EnvironmentValues {
    var accent: Color {
        get { self[AccentKey.self] }
        set { self[AccentKey.self] = newValue }
    }
}
// 3. Convenience modifier
extension View {
    func accent(_ color: Color) -> some View { environment(\.accent, color) }
}
```

### Shake Animation (Custom Animatable)
```swift
struct Shake: ViewModifier, Animatable {
    var numberOfShakes: Double
    var animatableData: Double {
        get { numberOfShakes }
        set { numberOfShakes = newValue }
    }
    func body(content: Content) -> some View {
        content.offset(x: -sin(numberOfShakes * 2 * .pi) * 30)
    }
}
```

### Measure View Size via Preferences
```swift
struct SizeKey: PreferenceKey {
    static var defaultValue: [CGSize] = []
    static func reduce(value: inout [CGSize], nextValue: () -> [CGSize]) {
        value.append(contentsOf: nextValue())
    }
}
extension View {
    func measureSize() -> some View {
        overlay { GeometryReader { proxy in
            Color.clear.preference(key: SizeKey.self, value: [proxy.size])
        }}
    }
}
```
