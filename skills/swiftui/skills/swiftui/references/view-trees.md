# View Trees & Identity

## Table of Contents
1. View Trees vs Render Trees
2. Modifier Order
3. View Builders & Group
4. Conditional Content & Identity
5. Lifetime Hooks
6. The applyIf Anti-Pattern

---

## 1. View Trees vs Render Trees

- **View tree** = ephemeral blueprint, constructed and thrown away repeatedly
- **Render tree** = persistent internal structure (Apple calls it "attribute graph")
- When a render tree node is removed, all associated state disappears
- VStack renders eagerly; LazyVStack renders lazily but preserves nodes offscreen

## 2. Modifier Order Matters

Modifiers wrap views in layers, read **bottom-up** to visualize the tree:

```swift
// Background is outermost; padding wraps text
Text("Hello").padding().background(Color.blue)

// vs. — different tree, different result
Text("Hello").background(Color.blue).padding()
```

## 3. View Builders & Group

- `@ViewBuilder` produces `TupleView` types encoding static structure
- Nested tuple views are recursively unfolded by container views
- Can be applied to properties and methods

**Modifiers on view lists apply to EACH element:**
```swift
Group {
    Image(systemName: "hand.wave")
    Text("Hello")
}.border(.blue)  // border on EACH view individually
```

**Group behavior varies by context:**
- Root view or sole child of ScrollView → behaves like VStack
- Inside overlay/background → behaves like ZStack

## 4. Conditional Content & Identity

`if/else` creates `ConditionalContent` with two branches that have **different identities**:

```swift
if let greeting = greeting {
    Text(greeting)       // identity: ifBranch — one view
} else {
    Text("Hello")        // identity: elseBranch — DIFFERENT view
}
```

Switching branches = removing one render tree node and inserting another. State is lost.

## 5. Lifetime Hooks

| Hook | Behavior |
|------|----------|
| `onAppear` | Called each time view appears onscreen (can fire multiple times) |
| `onDisappear` | Counterpart to onAppear |
| `task` | Creates async task on appear, cancels on disappear |

## 6. Identity Types

**Implicit identity:** position in the view tree (path like "0", "1.ifBranch").

**Explicit identity:** via `ForEach` with `Identifiable` items or `.id()` modifier. Appended to implicit identity, not a replacement.

**Changing `.id()` = removing the old node + inserting a new one** — triggers transitions and resets state.

## 7. The applyIf Anti-Pattern

```swift
// NEVER DO THIS — introduces ConditionalContent branch
extension View {
    @ViewBuilder
    func applyIf<V: View>(_ condition: Bool, transform: (Self) -> V) -> some View {
        if condition { transform(self) } else { self }
    }
}
```

**Instead**, use ternary operators or optional values:
```swift
Text("Hello").background(highlighted ? .red : .clear)
```

Most modifiers accept optionals/booleans/zero values precisely for this reason.
