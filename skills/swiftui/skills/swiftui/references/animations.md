# Animations

## Table of Contents
1. Core Principle
2. Property Animations vs Transitions
3. Implicit vs Explicit Animations
4. Timing Curves & Transactions
5. Animatable Protocol
6. Transitions
7. Phase Animators (iOS 17+)
8. Keyframe Animations (iOS 17+)
9. Completion Handlers (iOS 17+)

---

## 1. Core Principle

> The only way to trigger a view update is by changing state. Animations always start from the
> current render tree state and move toward the new state. This makes them additive and cancelable.

## 2. Property Animations vs Transitions

**Property animations** interpolate changed properties of views that **exist in both** old and new tree. View identity must be stable.

**Transitions** animate **insertions and removals** of views.

```swift
// WRONG — if/else = two identities = transition, not property animation
if flag { rect.frame(width: 200) } else { rect.frame(width: 100) }

// CORRECT — single identity = smooth property animation
rect.frame(width: flag ? 200 : 100)
```

## 3. Implicit vs Explicit Animations

### Implicit `.animation(_:value:)`
Animates everything in the modifier's **subtree** when the value changes:
```swift
Rectangle()
    .frame(width: flag ? 100 : 50)
    .animation(.default, value: flag)
```

Place as locally as possible. The old `.animation(_:)` without value is **deprecated**.

### iOS 17 Scoped `.animation(_:body:)`
Scope to specific modifiers:
```swift
Text("Hello")
    .opacity(flag ? 1 : 0)          // NOT animated
    .animation(.default) {
        $0.rotationEffect(flag ? .zero : .degrees(90))  // animated
    }
```

### Explicit `withAnimation`
Scope to a **state change** rather than a subtree:
```swift
.onTapGesture { withAnimation(.default) { flag.toggle() } }
```

### Binding Animation
```swift
Toggle(isOn: $flag.animation(.default)) { Text("Toggle") }
```

### Key Difference
| Aspect | Implicit | Explicit |
|--------|----------|----------|
| Scope | View subtree | Entire view update |
| Trigger | When value changes | When code in `withAnimation` runs |
| Precedence | **Wins** (evaluated later) | Overridden by implicit |

## 4. Timing Curves & Transactions

Built-in: `.linear`, `.easeIn`, `.easeOut`, `.spring`, `.bouncy` (iOS 17).

Modifiers: `.speed()`, `.delay()`, `.repeatCount(_:autoreverses:)`.

Progress values can go below 0 or above 1 (e.g., `.bouncy` overshoots).

**Transactions** are the underlying mechanism. Both implicit and explicit animations set properties on the current transaction.

```swift
// Remove animation without deprecated API
.transaction { $0.animation = nil }

// Equivalent to withAnimation:
var t = Transaction(animation: .default)
withTransaction(t) { flag.toggle() }
```

**`disablesAnimations`** on Transaction: when `true`, implicit animations won't override the transaction's animation.

## 5. Animatable Protocol

The heart of property animations:
- Expose `animatableData` conforming to `VectorArithmetic`
- Default is `EmptyAnimatableData` (nothing animates)
- SwiftUI interpolates and sets the value ~60 times per second

### Shake Animation (Classic Example)
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

Value goes N → N+1; `sin(N * 2π) == 0` so view ends where it started.

**`AnimatablePair`** — compose multiple animatable values when >1 property needs interpolation.

## 6. Transitions

Define how views animate on insertion/removal. Two states:
- **Active**: applied during insert (before resting) or removal (animating out)
- **Identity**: normal resting appearance

Default transition is `.opacity`.

### Custom Transition (Pre-iOS 17)
```swift
extension AnyTransition {
    static func blur(radius: CGFloat) -> Self {
        .modifier(
            active: Blur(radius: radius),
            identity: Blur(radius: 0)
        )
    }
}
```

### iOS 17 Transition Protocol
```swift
struct BlurTransition: Transition {
    var radius: CGFloat
    func body(content: Content, phase: TransitionPhase) -> some View {
        content.blur(radius: phase.isIdentity ? 0 : radius)
    }
}
```

### Critical Rules
- **Transitions require animations** — `.transition()` alone does nothing
- **Animation must NOT be inside** the subtree being inserted/removed
- **`.id()` changes trigger transitions** (identity change = removal + insertion)
- Combine: `.asymmetric(insertion:removal:).combined(with:)`

## 7. Phase Animators (iOS 17+)

Cycle through discrete values — each phase completes before next begins:

```swift
Button("Shake") { shakes += 1 }
    .phaseAnimator([0, -20, 20], trigger: shakes) { content, offset in
        content.offset(x: offset)
    }
```

- Without `trigger`: loops indefinitely
- Phase type needs only `Equatable` conformance
- Each phase change = separate animation

## 8. Keyframe Animations (iOS 17+)

Separate subsystem. Tracks run **in parallel**; keyframes within tracks run **in sequence**.

```swift
struct ShakeData {
    var offset: CGFloat = 0
    var rotation: Angle = .zero
}

Button("Shake") { trigger += 1 }
    .keyframeAnimator(initialValue: ShakeData(), trigger: trigger) { content, data in
        content.offset(x: data.offset).rotationEffect(data.rotation)
    } keyframes: { _ in
        KeyframeTrack(\.offset) {
            CubicKeyframe(-30, duration: 0.25)
            CubicKeyframe(30, duration: 0.5)
            CubicKeyframe(0, duration: 0.25)
        }
        KeyframeTrack(\.rotation) {
            LinearKeyframe(.degrees(20), duration: 0.1)
            LinearKeyframe(.degrees(-20), duration: 0.2)
            LinearKeyframe(.zero, duration: 0.1)
        }
    }
```

Types: `CubicKeyframe`, `LinearKeyframe`, `MoveKeyframe`. Cannot animate `Color` directly — use `Color.Resolved`.

## 9. Completion Handlers (iOS 17+)

```swift
withAnimation(.default) { flag.toggle() } completion: { print("Done!") }
```

**Pitfall:** In `.transaction` closures, use `.transaction(value:)` to force re-evaluation:
```swift
.transaction(value: flag) {
    $0.addAnimationCompletion { print("Done!") }
}
```

Completion fires at **logical completion** (feels done) or **actual completion** (curve fully settled).
