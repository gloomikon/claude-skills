---
name: core-data
description: >
  Core Data development expert grounded in objc.io's "Core Data" book and production patterns.
  Use this skill whenever working with Core Data, NSManagedObject, NSManagedObjectContext,
  NSPersistentContainer, NSPersistentCloudKitContainer, NSFetchRequest, NSFetchedResultsController,
  @FetchRequest, Core Data migrations, predicates, or any iOS/macOS data persistence using Core Data.
  Also trigger when the user mentions Core Data stack, managed objects, fetch requests, relationships,
  faulting, batch operations, merge policies, or CloudKit sync with Core Data.
---

# Core Data Development Guide

Based on "Core Data" by Florian Kugler & Daniel Eggert (objc.io) and production patterns from
real iOS projects.

Core Data is an **object graph manager**, not a database. Treat it as such for best performance.

For detailed reference on specific topics, read the corresponding file in `references/`:
- `references/stack-and-model.md` — Stack setup, managed objects, Managed protocol, relationships
- `references/fetching-and-performance.md` — Fetch requests, faulting, batching, indexes, profiling
- `references/saving-and-concurrency.md` — Change tracking, saving, conflicts, merge policies, multiple contexts
- `references/predicates-and-text.md` — NSPredicate patterns, string normalization, text search
- `references/migrations.md` — Model versions, lightweight/custom migrations, progressive migration
- `references/production-patterns.md` — Patterns extracted from real production projects (Boop & Invoice apps)

---

## Critical Rules (Always Apply)

### 1. Write Managed Object Subclasses by Hand

Never use Xcode codegen. Manual subclasses give full control over access levels, custom types,
and factory methods.

```swift
@objc(CD_Item)
final class CD_Item: NSManagedObject {
    @NSManaged private(set) var id: UUID
    @NSManaged private(set) var name: String
    @NSManaged private(set) var createdAt: Date
}
```

Use `@NSManaged` for Core Data-backed properties. Use `private(set)` for controlled mutation.
Mark classes `final` for performance.

### 2. Use the Managed Protocol Pattern

This protocol eliminates boilerplate across all entities:

```swift
protocol Managed: AnyObject, NSFetchRequestResult {
    static var entityName: String { get }
    static var defaultSortDescriptors: [NSSortDescriptor] { get }
    static var defaultPredicate: NSPredicate { get }
}

extension Managed where Self: NSManagedObject {
    static var entityName: String { entity().name! }
    static var defaultSortDescriptors: [NSSortDescriptor] { [] }
    static var defaultPredicate: NSPredicate { NSPredicate(value: true) }

    static var sortedFetchRequest: NSFetchRequest<Self> {
        let request = NSFetchRequest<Self>(entityName: entityName)
        request.sortDescriptors = defaultSortDescriptors
        request.predicate = defaultPredicate
        return request
    }

    static func fetch(
        in context: NSManagedObjectContext,
        configurationBlock: (NSFetchRequest<Self>) -> Void = { _ in }
    ) -> [Self] {
        let request = NSFetchRequest<Self>(entityName: entityName)
        configurationBlock(request)
        return (try? context.fetch(request)) ?? []
    }
}
```

### 3. Always Use saveOrRollback + performChanges

```swift
extension NSManagedObjectContext {
    @discardableResult
    func saveOrRollback() -> Bool {
        do {
            try save()
            return true
        } catch {
            rollback()
            return false
        }
    }

    func performChanges(block: @escaping () -> Void) {
        perform {
            block()
            _ = self.saveOrRollback()
        }
    }
}
```

Every mutation should be wrapped in `performChanges` — correct queue + auto-save.

### 4. Use findOrCreate, Not Fetch-Then-Insert

Check in-memory objects first (fast), then fetch from SQLite (slow), then create:

```swift
static func findOrCreate(
    in context: NSManagedObjectContext,
    matching predicate: NSPredicate,
    configure: (Self) -> Void
) -> Self {
    if let existing = findOrFetch(in: context, matching: predicate) {
        return existing
    }
    let newObject: Self = context.insertObject()
    configure(newObject)
    return newObject
}

static func materializedObject(
    in context: NSManagedObjectContext,
    matching predicate: NSPredicate
) -> Self? {
    for object in context.registeredObjects where !object.isFault {
        guard let result = object as? Self, predicate.evaluate(with: result)
        else { continue }
        return result
    }
    return nil
}
```

### 5. Every Fetch Request Is Expensive

A fetch request is a **full round trip** through the entire stack down to SQLite. Minimize them:
- Traverse **relationships** instead of fetching
- Check `registeredObjects` / `materializedObject` first
- Use `fetchBatchSize` (e.g., 20) for large result sets
- Use `returnsObjectsAsFaults = false` when you know you need the data

### 6. Use Primitive Properties for Custom Types

```swift
@NSManaged private var primitiveWeightUnit: String
private static let weightUnitKey = "weightUnit"

var weightUnit: WeightUnit {
    get {
        willAccessValue(forKey: Self.weightUnitKey)
        let value = WeightUnit(rawValue: primitiveWeightUnit) ?? .lbs
        didAccessValue(forKey: Self.weightUnitKey)
        return value
    }
    set {
        willChangeValue(forKey: Self.weightUnitKey)
        primitiveWeightUnit = newValue.rawValue
        didChangeValue(forKey: Self.weightUnitKey)
    }
}
```

Always wrap primitive access in `willAccessValue/didAccessValue` (getter) or
`willChangeValue/didChangeValue` (setter). For complex types, use JSONEncoder/JSONDecoder
to store as Binary Data.

### 7. CloudKit Integration — NSPersistentCloudKitContainer

```swift
let container = NSPersistentCloudKitContainer(name: "MyApp")
if let description = container.persistentStoreDescriptions.first {
    description.cloudKitContainerOptions = NSPersistentCloudKitContainerOptions(
        containerIdentifier: "iCloud.com.example.myapp"
    )
}
container.viewContext.automaticallyMergesChangesFromParent = true
container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
```

- `automaticallyMergesChangesFromParent = true` for CloudKit sync changes
- `NSMergeByPropertyObjectTrumpMergePolicy` — per-property merge, in-memory wins

### 8. Concurrency: Two Golden Rules

1. **Always use `perform`/`performAndWait`** before accessing a context or its objects
2. **Never pass managed objects between contexts** — pass `objectID` instead

```swift
// Safe pattern:
let ids = backgroundObjects.map { $0.objectID }
mainContext.perform {
    let objects = ids.map { mainContext.object(with: $0) }
}
```

### 9. Debug with Launch Arguments

| Argument | Purpose |
|----------|---------|
| `-com.apple.CoreData.SQLDebug 1` | SQL statements + timing |
| `-com.apple.CoreData.MigrationDebug 1` | Migration diagnostics |
| `-com.apple.CoreData.ConcurrencyDebug 1` | Threading violations |

---

## Property Wrapper / Observation Decision Guide

| Need | Approach |
|------|----------|
| FRC → UIKit table/collection view | `NSFetchedResultsController` + delegate |
| FRC → SwiftUI | `@FetchRequest` or FRC + AsyncStream wrapper |
| FRC → ObservableObject | FRC delegate → `@Published` properties |
| Observe single object changes | `NSManagedObjectContextObjectsDidChange` notification |
| Merge remote/background changes | `.NSManagedObjectContextDidSave` notification + `mergeChanges` |

---

## Quick Reference: Common Patterns

### Type-Safe Insert
```swift
extension NSManagedObjectContext {
    func insertObject<A: NSManagedObject>() -> A where A: Managed {
        guard let obj = NSEntityDescription.insertNewObject(
            forEntityName: A.entityName, into: self) as? A
        else { fatalError("Wrong object type") }
        return obj
    }
}
```

### Static Factory Method
```swift
@discardableResult
static func create(
    in context: NSManagedObjectContext,
    configure: (Self) -> Void
) -> Self {
    let newObject: Self = context.insertObject()
    configure(newObject)
    return newObject
}
```

### Batch Delete with Change Merging
```swift
let fetchRequest = NSFetchRequest<NSFetchRequestResult>(entityName: Self.entityName)
let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
deleteRequest.resultType = .resultTypeObjectIDs
if let result = try? context.execute(deleteRequest) as? NSBatchDeleteResult,
   let objectIDs = result.result as? [NSManagedObjectID] {
    let changes = [NSDeletedObjectsKey: objectIDs]
    NSManagedObjectContext.mergeChanges(fromRemoteContextSave: changes, into: [context])
}
```

### FRC with AsyncStream (Modern Pattern)
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

### Soft Delete for Sync Architectures
```swift
protocol DelayedDeletable: AnyObject {
    var markedForDeletionDate: Date? { get set }
}
extension DelayedDeletable where Self: NSManagedObject {
    func markForLocalDeletion() {
        markedForDeletionDate = Date()
    }
    static var notMarkedForDeletionPredicate: NSPredicate {
        NSPredicate(format: "%K == NULL", "markedForDeletionDate")
    }
}
```
