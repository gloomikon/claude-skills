# Saving, Concurrency & Multiple Contexts

## Table of Contents
1. Change Tracking
2. Saving Process
3. Validation
4. Save Conflicts & Merge Policies
5. Batch Operations
6. Concurrency Rules
7. Two-Context Setup (Recommended)
8. Merging Changes Between Contexts
9. Nested Contexts
10. Query Generations
11. Deleting Across Contexts (Two-Step Deletion)
12. Uniqueness Constraints

---

## 1. Change Tracking

**Object-level:**
- `hasChanges` — dirty flag
- `isInserted`, `isDeleted`, `isUpdated` — specific change types
- `hasPersistentChangedValues` — compares to last persisted state (more accurate)
- `changedValues()` — dictionary of changed keys → new values since last save
- `changedValuesForCurrentEvent()` — changed keys → old values since last `processPendingChanges`

**Context-level:**
- `hasChanges`, `insertedObjects`, `updatedObjects`, `deletedObjects`

## 2. Saving Process

1. `processPendingChanges` is called
2. `.NSManagedObjectContextWillSave` notification
3. Validation runs on all changed objects
4. `willSave()` called on all unsaved objects (cycles until stable)
5. `NSSaveChangesRequest` created
6. Permanent object IDs obtained for new inserts
7. Request forwarded to persistent store
8. Conflict detection via snapshot comparison
9. SQL executed
10. Row cache updated
11. `didSave()` called on saved objects
12. `.NSManagedObjectContextDidSave` notification

## 3. Validation

**Property-level:**
```swift
func validateLongitude(_ value: AutoreleasingUnsafeMutablePointer<AnyObject?>) throws {
    guard let l = (value.pointee as? NSNumber)?.doubleValue else { return }
    if l < -180 || l > 180 {
        throw propertyValidationError(forKey: "longitude",
            localizedDescription: "longitude must be in range -180...180")
    }
}
```

**Object-level:** Override `validateForInsert`, `validateForUpdate`, `validateForDelete`. Always call `super`.

## 4. Save Conflicts & Merge Policies

Core Data uses **optimistic locking**. Snapshots compared at save time.

| Policy | Behavior |
|--------|----------|
| `NSErrorMergePolicy` (default) | Throws error |
| `NSRollbackMergePolicy` | Discards in-memory changes |
| `NSOverwriteMergePolicy` | Persists in-memory changes |
| `NSMergeByPropertyStoreTrumpMergePolicy` | Per-property, store wins |
| `NSMergeByPropertyObjectTrumpMergePolicy` | Per-property, in-memory wins |

### Custom Merge Policy
```swift
class MyMergePolicy: NSMergePolicy {
    override func resolve(optimisticLockingConflicts list: [NSMergeConflict]) throws {
        // Custom logic before calling super
        try super.resolve(optimisticLockingConflicts: list)
        // Post-processing after super
    }
}
```

Always build on top of an existing policy. Call `super` first.

## 5. Batch Operations

Batch operations bypass the context — operate directly on SQLite. FRC will NOT update automatically.

**Required pattern for change merging:**
```swift
let batchRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
batchRequest.resultType = .resultTypeObjectIDs
guard let result = try context.execute(batchRequest) as? NSBatchDeleteResult,
      let objectIDs = result.result as? [NSManagedObjectID]
else { return }
let changes = [NSDeletedObjectsKey: objectIDs]
NSManagedObjectContext.mergeChanges(fromRemoteContextSave: changes, into: [context])
```

Same pattern for `NSBatchUpdateRequest` using `NSUpdatedObjectsKey`.

## 6. Concurrency Rules

1. **Always dispatch onto the context's queue** via `perform`/`performAndWait`
2. **Never share managed objects between contexts** — pass `objectID` only
3. Concurrency types: `.mainQueueConcurrencyType` (viewContext), `.privateQueueConcurrencyType` (background)

```swift
// Safe: pass IDs between contexts
let ids = backgroundObjects.map { $0.objectID }
mainContext.perform {
    let objects = ids.map { mainContext.object(with: $0) }
}
```

**Across different coordinators:** Use `objectID.uriRepresentation()` and
`psc.managedObjectID(forURIRepresentation:)`.

## 7. Two-Context Setup (Recommended)

```
viewContext (main queue) ──┐
                           ├── NSPersistentStoreCoordinator ── SQLite
syncContext (private queue)─┘
```

This is what `NSPersistentContainer` provides. Simple, shared row cache, fine-grained conflicts.

## 8. Merging Changes Between Contexts

```swift
NotificationCenter.default.addObserver(
    forName: .NSManagedObjectContextDidSave,
    object: backgroundContext, queue: nil
) { note in
    mainContext.perform {
        mainContext.mergeChanges(fromContextDidSave: note)
    }
}
```

During merge:
- **Inserted** objects faulted in (deallocated if unreferenced)
- **Updated** objects refreshed (in-memory changes win per-property)
- **Deleted** objects removed (even with pending changes)

## 9. Nested Contexts

**Good use case 1:** Deferred background saves. Main context as child of private context.
Saving main = in-memory push to parent. Expensive I/O only when parent saves.

**Good use case 2:** Scratchpads for editing dialogs. Discard = throw away child context.

**Do NOT use nested contexts for background work:**
- Fetch requests in child block the UI (must traverse parent on main queue)
- Every save pushes ALL changes into parent (main) context
- No fine-grained conflict control

## 10. Query Generations (iOS 10+)

Pin a context to a consistent database state:
```swift
try context.setQueryGenerationFrom(.current)
```

Prevents inconsistent reads between consecutive fetches. Generation advances on merge or save.

## 11. Deleting Across Contexts (Two-Step Deletion)

If context A holds a fault and context B deletes the object, accessing the fault crashes.

**Solution: Soft delete pattern**
```swift
protocol DelayedDeletable: AnyObject {
    var markedForDeletionDate: Date? { get set }
}
extension DelayedDeletable where Self: NSManagedObject {
    func markForLocalDeletion() {
        guard isFault || markedForDeletionDate == nil else { return }
        markedForDeletionDate = Date()
    }
    static var notMarkedForDeletionPredicate: NSPredicate {
        NSPredicate(format: "%K == NULL", "markedForDeletionDate")
    }
}
```

Include `notMarkedForDeletionPredicate` in default fetch predicates. Periodically batch-delete
objects older than a threshold.

## 12. Uniqueness Constraints (iOS 9+)

Per-entity uniqueness in the data model. Violations resolved via merge policies.

For constraint conflicts:
- `NSRollbackMergePolicy` — store wins
- `NSOverwriteMergePolicy` — in-memory wins, displaced object deleted
- `NSMergeByPropertyObjectTrumpMergePolicy` — persisted object stays, changed properties merged in

Custom: override `resolve(constraintConflicts:)` in your merge policy subclass.
