# Advanced: Environment, Layout Protocol, Preferences, Matched Geometry

## Table of Contents
1. Environment
2. Custom Environment Keys
3. Custom Component Styles
4. Environment Objects
5. Layout Protocol (iOS 16+)
6. Preferences
7. Coordinate Spaces & Anchors
8. Matched Geometry Effect

---

## 1. Environment

SwiftUI's built-in **dependency injection** — propagates values **down** the view tree.

```swift
VStack { ... }.font(.title)
// equivalent to:
VStack { ... }.environment(\.font, .title)
```

All views **downstream** see the value. Upstream/sibling branches do not.

```swift
@Environment(\.dynamicTypeSize) private var dynamicTypeSize
```

**Performance:** Use specific key paths to minimize re-renders:
```swift
// Only re-renders when isAccessibilitySize changes, not every dynamicTypeSize change
@Environment(\.dynamicTypeSize.isAccessibilitySize) private var isAccessibilitySize
```

**Rules:**
- Always mark `@Environment` as `private`
- Cannot be read in view's initializer — only in `body`

## 2. Custom Environment Keys

### Modern: @Entry Macro (Xcode 16+ / iOS 18+)

The `@Entry` macro replaces the old 3-step pattern with a single declaration:

```swift
extension EnvironmentValues {
    @Entry var badgeColor: Color = .blue
}

// Optional convenience modifier:
extension View {
    func badgeColor(_ color: Color) -> some View {
        environment(\.badgeColor, color)
    }
}

// Reading:
@Environment(\.badgeColor) private var badgeColor
```

### Legacy: 3-Step Pattern (pre-Xcode 16 / iOS 17 and earlier)

```swift
// Step 1: Define key
enum BadgeColorKey: EnvironmentKey {
    static var defaultValue: Color = .blue
}

// Step 2: Extend EnvironmentValues
extension EnvironmentValues {
    var badgeColor: Color {
        get { self[BadgeColorKey.self] }
        set { self[BadgeColorKey.self] = newValue }
    }
}

// Step 3: Convenience modifier
extension View {
    func badgeColor(_ color: Color) -> some View {
        environment(\.badgeColor, color)
    }
}
```

## 3. Custom Component Styles

Mirrors SwiftUI's `.buttonStyle()` pattern:

```swift
// 1. Protocol
protocol BadgeStyle {
    associatedtype Body: View
    @ViewBuilder func makeBody(_ label: AnyView) -> Body
}

// 2. Default implementation
struct DefaultBadgeStyle: BadgeStyle { ... }

// 3. Environment key (modern — @Entry macro, Xcode 16+)
extension EnvironmentValues {
    @Entry var badgeStyle: any BadgeStyle = DefaultBadgeStyle()
}
// Or legacy: enum BadgeStyleKey: EnvironmentKey { ... }

// 4. Static member for dot syntax
extension BadgeStyle where Self == FancyBadgeStyle {
    static var fancy: FancyBadgeStyle { FancyBadgeStyle() }
}

// Usage: .badgeStyle(.fancy)
```

Use `any BadgeStyle` (existential) as the environment value type so different style types can be swapped in.

## 4. Environment Objects

### iOS 17+ (@Observable)
```swift
@Observable final class UserModel { ... }

struct Nested: View {
    @Environment var userModel: UserModel?  // Optional — safe if not set
}

// Set:
Nested().environment(UserModel())
```

### Pre-iOS 17
```swift
@EnvironmentObject var userModel: UserModel  // Crashes if not set
// Set:
.environmentObject(UserModel())
```

### Dependency Injection Helper
```swift
extension View {
    func injectDependencies() -> some View {
        environmentObject(UserModel())
            .environmentObject(Database())
    }
}
```

## 5. Layout Protocol (iOS 16+)

Two-step process:
1. `sizeThatFits` — determine container size by measuring subviews
2. `placeSubviews` — place subviews within the container

### Flow Layout Example
```swift
struct FlowLayout: Layout {
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let containerWidth = proposal.replacingUnspecifiedDimensions().width
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        return flowLayout(sizes: sizes, containerWidth: containerWidth).union().size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize,
                       subviews: Subviews, cache: inout ()) {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        let frames = flowLayout(sizes: sizes, containerWidth: bounds.width)
        for (frame, subview) in zip(frames, subviews) {
            subview.place(at: CGPoint(x: frame.minX + bounds.minX,
                                       y: frame.minY + bounds.minY),
                          proposal: .unspecified)
        }
    }
}
```

**Best practice:** Keep the layout algorithm as a pure function, testable independently.

**AnyLayout** — type-erased layout for dynamic switching with animated transitions.

## 6. Preferences

Propagate values **up** the view tree (opposite of environment).

```swift
struct SizeKey: PreferenceKey {
    static var defaultValue: [CGSize] = []
    static func reduce(value: inout [CGSize], nextValue: () -> [CGSize]) {
        value.append(contentsOf: nextValue())
    }
}

// Measure:
myView.overlay {
    GeometryReader { proxy in
        Color.clear.preference(key: SizeKey.self, value: [proxy.size])
    }
}

// Read:
.onPreferenceChange(SizeKey.self) { sizes in ... }
```

**Critical:** Use `.fixedSize()` in preference-based layouts to prevent infinite layout loops.

`onPreferenceChange` fires during the layout phase and invalidates `@State`, causing `body` re-execution **before the current frame renders** (no flicker).

## 7. Coordinate Spaces & Anchors

Three types: `.global` (screen), `.local` (view), named (`.coordinateSpace(name:)`).

### Anchors
Wrap geometry values measured in global space. Resolve via `GeometryProxy`:

```swift
// Set anchor:
Button("Log In") {}
    .anchorPreference(key: HighlightKey.self, value: .bounds) { $0 }

// Resolve in overlay:
.overlayPreferenceValue(HighlightKey.self) { anchor in
    if let anchor {
        GeometryReader { proxy in
            let rect = proxy[anchor]
            Ellipse().strokeBorder(.red)
                .frame(width: rect.width, height: rect.height)
                .offset(x: rect.origin.x, y: rect.origin.y)
        }
    }
}
```

## 8. Matched Geometry Effect

Gives target views the same position/size as a source view. Uses `@Namespace` and shared ID.

```swift
@Namespace var namespace

// Source (default isSource: true):
Button("Log In") {}
    .matchedGeometryEffect(id: "highlight", in: namespace)

// Target:
Ellipse().strokeBorder(.red)
    .matchedGeometryEffect(id: "highlight", in: namespace, isSource: false)
```

### Hero Animation
```swift
@Namespace var ns
if hero {
    circle.matchedGeometryEffect(id: "img", in: ns)
} else {
    circle.matchedGeometryEffect(id: "img", in: ns).frame(width: 30, height: 30)
}
```

**Modifier order matters:**
```swift
// WRONG — frame locks size, matched geometry can't change it
circle.frame(width: 30).matchedGeometryEffect(id: "img", in: ns)

// CORRECT — matched geometry can influence size
circle.matchedGeometryEffect(id: "img", in: ns).frame(width: 30)
```

Conceptually, matched geometry inserts a `.frame` + `.offset` on the target.
