# Fetching & Performance

## Table of Contents
1. Fetch Request Lifecycle
2. Faulting
3. Batched Fetching
4. NSFetchedResultsController
5. Three-Tier Performance Model
6. Avoiding Fetch Requests
7. Indexes
8. Denormalization
9. Saving Performance
10. Profiling

---

## 1. Fetch Request Lifecycle (8 Steps)

1. Context forwards request to persistent store coordinator
2. Coordinator forwards to persistent store(s)
3. Persistent store converts to SQL, sends to SQLite
4. SQLite executes query, returns rows → stored in **row cache**
5. Persistent store instantiates managed objects as **faults** (uniquing ensures one object per ID)
6. Coordinator returns array to context
7. Context considers **pending changes** (unsaved inserts/deletes/updates) and adjusts results
8. Final array returned to caller

**All synchronous.** Every fetch request is a full round trip to SQLite.

## 2. Faulting

**Faults** are lightweight managed objects not yet populated with data — "promises" to get data.

- `returnsObjectsAsFaults = true` (default): Returns faults
- `returnsObjectsAsFaults = false`: Pre-populates with data (use when you need all data)
- `includesPropertyValues = true` (default): Loads data into row cache
- `includesPropertyValues = false`: Only loads object IDs

**Fault fulfillment:** When you access a property on a fault, Core Data checks the row cache.
Cache hit = cheap (in-memory). Cache miss = expensive (SQLite round trip).

**Relationship faults:** To-many relationships have two-level faulting. First access loads IDs only.
Accessing a property on a related object fulfills that individual fault.

### Batch-Fault Multiple Objects
```swift
extension Collection where Element: NSManagedObject {
    func fetchFaults() {
        guard let context = first?.managedObjectContext else { return }
        let faults = filter { $0.isFault }
        guard let first = faults.first else { return }
        let request = NSFetchRequest<Element>()
        request.entity = first.entity
        request.returnsObjectsAsFaults = false
        request.predicate = NSPredicate(format: "self in %@", Array(faults))
        _ = try? context.fetch(request)
    }
}
```

## 3. Batched Fetching

```swift
request.fetchBatchSize = 20  // ~1.3x visible items
request.returnsObjectsAsFaults = false
```

Core Data fetches only object IDs upfront, then loads data in pages as you access elements.
Old batches released on LRU basis — extremely memory-efficient for huge datasets.

## 4. NSFetchedResultsController

Mediates between Core Data and table/collection views. Listens to context change notifications.

### Standard Setup
```swift
let request = CD_Item.sortedFetchRequest
request.returnsObjectsAsFaults = false
let frc = NSFetchedResultsController(
    fetchRequest: request,
    managedObjectContext: context,
    sectionNameKeyPath: nil,
    cacheName: "items"  // Persistent cache for faster re-use
)
frc.delegate = self
try frc.performFetch()
```

### Modern AsyncStream Wrapper
```swift
static func make<T: NSFetchRequestResult>(
    for frc: NSFetchedResultsController<T>
) -> AsyncStream<Void> {
    AsyncStream { continuation in
        let delegate = FRCDelegateWrapper { continuation.yield() }
        frc.delegate = delegate
        try? frc.performFetch()
        continuation.yield()
        continuation.onTermination = { _ in frc.delegate = nil }
    }
}
```

### FRC → @Published (Production Pattern)
```swift
private func observeItems() {
    let request = CD_Item.sortedFetchRequest
    request.returnsObjectsAsFaults = false
    let frc = NSFetchedResultsController(
        fetchRequest: request,
        managedObjectContext: context,
        sectionNameKeyPath: nil,
        cacheName: nil
    )
    self.itemsFRC = frc
    let stream = FetchResultStream.make(for: frc)
    Task { @MainActor [weak self] in
        for await _ in stream {
            self?.items = frc.sections?.first?.objects as? [CD_Item] ?? []
        }
    }
}
```

## 5. Three-Tier Performance Model

| Tier | Cost | Description |
|------|------|-------------|
| Context | ~1x | Managed objects + context. Lock-free, extremely fast. |
| Coordinator | ~10x | PSC + row cache. Thread-safe with locking. |
| SQL | ~100x | SQLite + file system. Orders of magnitude slower. |

**Principle:** Minimize round trips to lower tiers.

## 6. Avoiding Fetch Requests

### Traverse Relationships
Accessing `item.owner` may be free if the owner is already materialized. A fetch request
always traverses all tiers.

### Check In-Memory First
```swift
static func materializedObject(in context: NSManagedObjectContext, matching predicate: NSPredicate) -> Self? {
    for object in context.registeredObjects where !object.isFault {
        guard let result = object as? Self, predicate.evaluate(with: result) else { continue }
        return result
    }
    return nil
}
```

### Cache Singleton-Like Objects
```swift
extension NSManagedObjectContext {
    func set(_ object: NSManagedObject?, forSingleObjectCacheKey key: String) {
        var cache = userInfo["SingleObjectCache"] as? [String: NSManagedObject] ?? [:]
        cache[key] = object
        userInfo["SingleObjectCache"] = cache
    }
}
```

### Small Datasets
For <100 objects, load all with a single fetch, hold strong references, filter in memory.

## 7. Indexes

Indexes improve sorting and predicate filtering at cost of larger DB and slower inserts.

**Compound indexes are critical.** SQLite uses max ONE index per table per query.
A compound index on `(markedForDeletionDate, updatedAt)` serves both WHERE and ORDER BY.

A compound index on `(A, B, C)` can serve queries on `A`, `(A, B)`, or `(A, B, C)` — NOT just `B`.

Remove redundant single-attribute indexes that overlap with compound indexes.

### Verify with EXPLAIN QUERY PLAN
```bash
sqlite3 MyApp.sqlite "EXPLAIN QUERY PLAN SELECT ..."
```

## 8. Denormalization

Store computed/derived values directly on entities to avoid relationship fault fulfillment:

```swift
override func willSave() {
    if hasChangedItems { updateItemCount() }
}

fileprivate func updateItemCount() {
    let count = Int64(items.count)
    guard count != numberOfItems else { return }  // Prevent infinite loop
    numberOfItems = count
}
```

Always check for equality before setting to avoid infinite save loops.

## 9. Saving Performance

- Inserting/changing objects in a context is cheap (context-tier only)
- `save()` is expensive (coordinator + SQL tiers)
- Minimize saves; batch changes together
- Aim for <16ms save time during animations

## 10. Profiling

### SQL Debug Output
```
-com.apple.CoreData.SQLDebug 1
```

Shows every SQL statement with timing. Column naming: `Z_PK` (primary key), `Z_ENT` (entity type),
`Z_OPT` (optimistic locking version), `Z` prefix on attributes.

### Watch for Consecutive Faults
```
annotation: fault fulfilled from database for : 0xd000000000100002
```
Many in quick succession = inefficient one-at-a-time round trips. Fix with `returnsObjectsAsFaults = false`
or relationship prefetching.

### Relationship Prefetching
```swift
request.relationshipKeyPathsForPrefetching = ["owner", "owner.settings"]
```

### Core Data Instruments
4 instruments: Fetches, Saves, Faults, Cache Misses. All include call stack info.
