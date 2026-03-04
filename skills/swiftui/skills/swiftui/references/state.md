# State & Binding

## Table of Contents
1. View Update Cycle
2. @State In Depth
3. @Observable (iOS 17+)
4. ObservableObject (Pre-iOS 17)
5. Bindings
6. @Bindable (iOS 17+)
7. Debugging View Updates
8. Performance Tips

---

## 1. View Update Cycle

1. View tree is constructed
2. Render tree nodes are created/removed/updated to match
3. Some event causes a state change
4. Repeat

Your job: describe what should be onscreen for a given state. SwiftUI handles the diffing.

## 2. @State In Depth

- For **private, value-type** view state
- `State(initialValue:)` — value is ONLY the initial value, used when the render tree node is first created
- `wrappedValue` is a pointer to memory in the render tree
- Dependencies tracked automatically: accessing state in `body` registers a dependency

**Always declare @State as private and initialize inline:**
```swift
@State private var count = 0  // CORRECT
```

**Why initializers break:**
```swift
// BROKEN — only changes initial value, ignored once node exists
init(count: Int) { _count = State(initialValue: count) }
```

Views have no identity at init time — a single view struct can appear at multiple positions.

## 3. @Observable (iOS 17+)

Two responsibilities:
1. Adds conformance to `Observable` marker protocol
2. Transforms properties for read/write tracking

```swift
@Observable final class Model {
    var value = 0  // Automatically tracked at property level
}
```

**Key advantages over ObservableObject:**
- **Property-level** tracking (not object-level) — more efficient
- **Location-agnostic** — works in singletons, optionals, arrays, nested collections
- **Branch-aware** — only observed when accessed in the current code path
- No need to manually split model objects for granular updates

**Ownership rules:**
```swift
// View owns the object → @State for lifetime management
@State private var model = Model()

// Object passed from outside → plain property, observation is automatic
var model: Model
```

**How it works internally:** Properties become computed, backed by private storage. `access()` and `withMutation()` calls go through an `ObservationRegistrar`. SwiftUI uses `withObservationTracking(_:onChange:)` to form dependencies.

### Common Mistakes

1. **Using @State for externally-owned objects** — initial value only set once
2. **Not using @State for view-private objects** — object recreated on every parent re-render

## 4. ObservableObject (Pre-iOS 17)

### @StateObject
- Manages lifetime + subscribes to `objectWillChange`
- Uses **autoclosure** (lazy init, evaluated once)
- Should be private, initialized inline

```swift
final class Model: ObservableObject {
    @Published var value = 0
}
struct Counter: View {
    @StateObject private var model = Model()
}
```

### @ObservedObject
- NO lifetime management, only subscribes to `objectWillChange`
- For objects passed from outside

```swift
struct Counter: View {
    @ObservedObject var model: Model  // Passed in
}
```

**Key difference:** `@StateObject` tracks at object level (any @Published change → re-render). `@Observable` tracks at property level.

## 5. Bindings

A binding wraps a **getter and a setter** for read/write access without owning the value:

```swift
struct Counter: View {
    @Binding var value: Int
    var body: some View {
        Button("Increment: \(value)") { value += 1 }
    }
}
// Usage: Counter(value: $parentState)
```

`$value` is syntactic sugar for `_value.projectedValue`.

**Binding to computed properties:**
```swift
final class Model: ObservableObject {
    @Published var value = 0
    var clamped: Int {
        get { min(max(0, value), 10) }
        set { value = newValue }
    }
}
// $model.clamped works as a binding
```

## 6. @Bindable (iOS 17+)

For creating bindings to `@Observable` objects:

```swift
struct Counter: View {
    @Bindable var model: Model
    var body: some View {
        Stepper("\(model.value)", value: $model.value)
    }
}
// Or inline:
Stepper("\(model.value)", value: Bindable(model).value)
```

Uses dynamic member lookup internally.

## 7. Debugging View Updates

```swift
var body: some View {
    let _ = Self._printChanges()  // Logs WHY body re-executed
    // Output: _value (state changed), @self (props changed), @identity (fresh insert)
}
```

## 8. Performance Tips

- Break large views into subviews dependent on distinct sub-states
- With `@Observable`, property-level tracking naturally helps
- Only pass data that is actually needed to subviews
- Use Instruments' SwiftUI profiling template for diagnosis
