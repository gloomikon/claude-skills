# Layout System

## Table of Contents
1. The Layout Algorithm
2. Leaf Views (Text, Shape, Color, Image, Spacer)
3. Padding & Frames
4. Aspect Ratio, Overlay, Background
5. fixedSize
6. HStack/VStack Algorithm
7. ZStack vs overlay/background
8. ScrollView, GeometryReader, List
9. LazyStacks & Grids
10. ViewThatFits
11. Alignment
12. Custom Alignment Identifiers

---

## 1. The Layout Algorithm (3 Steps)

1. **Parent proposes** a size to subview
2. **Subview determines** its own size (recursively proposing to children)
3. **Subview reports** size back — **definitive, parent cannot override**
4. Parent places the subview

```swift
// ProposedViewSize has optional width/height — nil means "become ideal size"
func sizeThatFits(in: ProposedViewSize) -> CGSize
```

## 2. Leaf Views

### Text
- Fits into any proposed size via word-wrapping, truncation, clipping
- Reports exact size needed (never wider than proposed)
- Key modifiers: `.lineLimit()`, `.truncationMode()`, `.minimumScaleFactor()`
- `.fixedSize()` → always renders at ideal size (no wrapping)

### Shapes
- Most shapes (Rectangle, RoundedRectangle, Capsule, Ellipse) accept any proposed size
- Circle fits itself and reports actual circle size
- Ideal size for shapes = 10x10 by default

### Colors
- Behave like `Rectangle().fill(...)` for layout
- Special: colors in `.background` bleed into non-safe areas
- To prevent: use `Rectangle().fill()` instead or use `ignoresSafeAreaEdges` parameter

### Image
- Default: reports static size of underlying image
- `.resizable()`: accepts any proposed size
- Almost always combine with `.aspectRatio(contentMode:)` or `.scaledToFit()`

### Spacer
- In stacks: flexible on major axis (min to infinity), zero on minor axis
- Default minimum length = default padding
- **Prefer `.frame(maxWidth: .infinity, alignment:)` over `HStack { Spacer(); Text }`**

## 3. Padding & Frames

### Padding
Subtracts from proposed, adds to reported size.

### Fixed Frame `.frame(width:height:alignment:)`
- Proposes exactly the specified size; reports exactly that size
- Use sparingly — hardcoded sizes break with Dynamic Type

### Flexible Frame `.frame(minWidth:maxWidth:...)`
Two-pass clamping:
1. **Inbound:** clamp proposed size by min/max, propose clamped to child
2. **Outbound:** substitute missing bounds with child's reported size, clamp again, report

**Essential patterns:**
```swift
// "At least as wide as proposed" (spans available width)
Text("Hello").frame(maxWidth: .infinity)

// "Exactly as wide as proposed" (ignores subview size)
Text("Hello").frame(minWidth: 0, maxWidth: .infinity)
```

## 4. Aspect Ratio, Overlay, Background

### Aspect Ratio
- `.fit`: largest rectangle with ratio that fits inside proposed size
- `.fill`: smallest rectangle with ratio that covers proposed size
- `.scaledToFit()` / `.scaledToFill()` are shorthands

### Overlay and Background
- Primary subview sized first, then its size proposed to secondary
- **Reported size = primary subview's size always**
- Secondary view never affects layout

```swift
// Highlight that doesn't affect layout
extension View {
    func highlight(_ enabled: Bool = true) -> some View {
        background { if enabled { Color.orange.padding(-3) } }
    }
}
```

## 5. fixedSize

Proposes `nil` (ideal size) to subview regardless of parent's proposal.

Use in overlays/backgrounds when secondary content must render at natural size (e.g., badges).

## 6. HStack/VStack Algorithm

1. Determine flexibility of subviews (probe with 0 and infinity)
2. Group by layout priority
3. Sort by flexibility within groups (least flexible first)
4. Distribute: remaining / count for each view
5. `.layoutPriority()` changes distribution order

```swift
HStack(spacing: 0) {
    Color.cyan
    Text("Hello, World!").layoutPriority(1) // gets space first
    Color.teal
}
```

## 7. ZStack vs overlay/background

| | ZStack | overlay/background |
|---|---|---|
| Size | Union of ALL subviews | Primary subview only |
| Use when | All views should influence size | Secondary views decorative |

## 8. ScrollView, GeometryReader, List

### ScrollView
- Proposes `nil` along scroll axis (unlimited space)
- Multiple subviews → implicit VStack
- Shapes get ideal size (10x10) on scroll axis — use `.frame(height:)`

### GeometryReader
- Always accepts proposed size, exposes via `GeometryProxy`
- Places subviews **top-leading** (unlike most containers)
- **Safe: wrap flexible views, or place inside overlay/background**

### List
- Row heights computed lazily; total estimated from visible items

## 9. LazyStacks & Grids

### LazyVStack/LazyHStack
- Do NOT distribute space (unlike regular stacks)
- Propose `nil` on major axis — subviews become ideal size
- Size = union of all subviews' frames

### LazyVGrid Column Types
- **Fixed**: unconditionally the specified width
- **Flexible**: min/max bounds, clamped from remaining/count
- **Adaptive**: fits as many subcolumns as possible (width/minimum)

**Gotcha:** Grids run column layout **twice** (sizing + rendering), which can produce surprising results.

## 10. ViewThatFits

Proposes `nil` to each subview to get ideal sizes. Displays first subview whose ideal size fits. If none fit, picks the last as fallback.

## 11. Alignment

Alignment is a **negotiation** between parent and subview via alignment guides.

Built-in: `.leading`, `.center`, `.trailing`, `.top`, `.bottom`, `.firstTextBaseline`, `.lastTextBaseline`.

```swift
Image(systemName: "pencil.circle.fill")
    .alignmentGuide(.firstTextBaseline) { $0.height / 2 }
```

**Badge pattern:**
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

## 12. Custom Alignment Identifiers

```swift
struct MenuAlignment: AlignmentID {
    static func defaultValue(in context: ViewDimensions) -> CGFloat {
        context.width / 2
    }
}
extension HorizontalAlignment {
    static let menu = HorizontalAlignment(MenuAlignment.self)
}
```

Custom alignments **propagate up** through container views — unlike built-in alignments which are overridden by each container.

## Layout Debugging

**The best technique:** put `.border()` on views. Optionally overlay a GeometryReader to display sizes.

**Rendering modifiers** (`offset`, `rotationEffect`, `scaleEffect`) do NOT affect layout — only drawing.
