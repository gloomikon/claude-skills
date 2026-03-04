# Stack Setup, Managed Objects & Relationships

## Table of Contents
1. Core Data Stack Architecture
2. NSPersistentContainer Setup
3. CloudKit Container Setup
4. Managed Object Subclasses
5. The Managed Protocol
6. Relationships
7. Delete Rules
8. Subentities (Warning)
9. Data Types & Custom Types

---

## 1. Core Data Stack Architecture

```
NSManagedObject (model objects)
        |
NSManagedObjectContext (scratchpad for changes)
        |
NSPersistentStoreCoordinator (coordinator between context and store)
        |
NSPersistentStore (SQLite by default)
```

- **NSManagedObject**: Lives within a context. Never access from wrong queue.
- **NSManagedObjectContext**: Tracks inserts, deletes, updates. Changes not persisted until `save()`.
- **NSPersistentStoreCoordinator**: Thread-safe bridge. Shared row cache for performance.
- **NSPersistentStore**: Usually SQLite. Also: XML, binary, in-memory.

## 2. NSPersistentContainer Setup

```swift
class CoreDataStack {
    private lazy var container: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "MyApp")
        return container
    }()

    lazy var managedContext: NSManagedObjectContext = {
        container.viewContext
    }()

    @MainActor func load() async throws {
        try await withCheckedThrowingContinuation { continuation in
            container.loadPersistentStores { _, error in
                if let error {
                    continuation.resume(throwing: error)
                } else {
                    continuation.resume(returning: ())
                }
            }
        }
    }
}
```

Container name must match `.xcdatamodeld` filename. Pass `container.viewContext` via dependency injection.

## 3. CloudKit Container Setup

```swift
private lazy var container: NSPersistentCloudKitContainer = {
    let container = NSPersistentCloudKitContainer(name: "MyApp")
    if let description = container.persistentStoreDescriptions.first {
        description.cloudKitContainerOptions = NSPersistentCloudKitContainerOptions(
            containerIdentifier: "iCloud.com.example.myapp"
        )
    }
    container.viewContext.automaticallyMergesChangesFromParent = true
    container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
    return container
}()
```

- `automaticallyMergesChangesFromParent = true` — essential for CloudKit sync
- `NSMergeByPropertyObjectTrumpMergePolicy` — in-memory wins per-property on conflicts
- All entities must have `syncable="YES"` in the model

### CloudKit Attribute Constraints

CloudKit requires all attributes to be **either optional or have a default value**. This creates
a problem for types like UUID that have no meaningful default.

**Workaround:** Mark the attribute optional in the `.xcdatamodeld`, but declare it as non-optional
`@NSManaged` in code. Assign the value in `awakeFromInsert()`:

```swift
@objc(CD_Item)
final class CD_Item: NSManagedObject {
    // Non-optional in code, optional in the model
    @NSManaged private(set) var identifier: UUID

    override func awakeFromInsert() {
        super.awakeFromInsert()
        identifier = UUID()  // Always set before any access
    }
}
```

`awakeFromInsert()` runs before the object is ever accessed, so the property is never nil
in practice. This avoids polluting the API with unnecessary optionals.

## 4. Managed Object Subclasses

Always write by hand. Never use Xcode codegen.

```swift
@objc(CD_Item)
final class CD_Item: NSManagedObject, Managed {
    @NSManaged private(set) var id: UUID
    @NSManaged private(set) var name: String
    @NSManaged private(set) var dateCreated: Date
    @NSManaged private(set) var dateModified: Date

    // Relationships
    @NSManaged private(set) var owner: CD_User
    @NSManaged private var itemsSet: NSSet?

    var items: [CD_SubItem] {
        (itemsSet?.allObjects as? [CD_SubItem])?.sorted { $0.dateCreated < $1.dateCreated } ?? []
    }

    // Factory method
    @discardableResult
    static func create(
        in context: NSManagedObjectContext,
        name: String,
        owner: CD_User
    ) -> Self {
        Self.create(in: context) { item in
            item.id = UUID()
            item.name = name
            item.owner = owner
            item.dateCreated = Date()
            item.dateModified = Date()
        }
    }

    func update(name: String) {
        self.name = name
        self.dateModified = Date()
    }
}
```

### NSOrderedSet for Ordered To-Many
```swift
@NSManaged private var records: NSOrderedSet

var recordsArray: [CD_Record] {
    records.array as? [CD_Record] ?? []
}

// Mutating:
fileprivate var mutableRecords: NSMutableOrderedSet {
    mutableOrderedSetValue(forKey: #keyPath(records))
}
```

## 5. The Managed Protocol

Full implementation with all helpers:

```swift
protocol Managed: AnyObject, NSFetchRequestResult {
    static var entity: NSEntityDescription { get }
    static var entityName: String { get }
    static var defaultSortDescriptors: [NSSortDescriptor] { get }
    static var defaultPredicate: NSPredicate { get }
    var managedObjectContext: NSManagedObjectContext? { get }
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

    static func sortedFetchRequest(with predicate: NSPredicate) -> NSFetchRequest<Self> {
        let request = sortedFetchRequest
        guard let existing = request.predicate else { fatalError("must have predicate") }
        request.predicate = NSCompoundPredicate(andPredicateWithSubpredicates: [existing, predicate])
        return request
    }

    static func create(in context: NSManagedObjectContext, configure: (Self) -> Void) -> Self {
        let newObject: Self = context.insertObject()
        configure(newObject)
        return newObject
    }

    static func findOrCreate(
        in context: NSManagedObjectContext,
        matching predicate: NSPredicate,
        configure: (Self) -> Void
    ) -> Self {
        guard let object = findOrFetch(in: context, matching: predicate) else {
            let newObject: Self = context.insertObject()
            configure(newObject)
            return newObject
        }
        return object
    }

    static func findOrFetch(in context: NSManagedObjectContext, matching predicate: NSPredicate) -> Self? {
        guard let object = materializedObject(in: context, matching: predicate) else {
            return fetch(in: context) { request in
                request.predicate = predicate
                request.returnsObjectsAsFaults = false
                request.fetchLimit = 1
            }.first
        }
        return object
    }

    static func materializedObject(in context: NSManagedObjectContext, matching predicate: NSPredicate) -> Self? {
        for object in context.registeredObjects where !object.isFault {
            guard let result = object as? Self, predicate.evaluate(with: result) else { continue }
            return result
        }
        return nil
    }

    static func fetch(
        in context: NSManagedObjectContext,
        configurationBlock: (NSFetchRequest<Self>) -> Void = { _ in }
    ) -> [Self] {
        let request = NSFetchRequest<Self>(entityName: entityName)
        configurationBlock(request)
        return (try? context.fetch(request)) ?? []
    }

    static func count(in context: NSManagedObjectContext, configure: (NSFetchRequest<Self>) -> Void = { _ in }) -> Int {
        let request = NSFetchRequest<Self>(entityName: entityName)
        configure(request)
        return (try? context.count(for: request)) ?? 0
    }

    func delete(in context: NSManagedObjectContext) {
        context.delete(self)
    }

    static func deleteAll(in context: NSManagedObjectContext) {
        let fetchRequest = Self.fetchRequest() as NSFetchRequest<NSFetchRequestResult>
        let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
        _ = try? context.execute(deleteRequest)
    }

    static func deleteAll(currentContext: NSManagedObjectContext, backgroundContext: NSManagedObjectContext) {
        backgroundContext.perform {
            let fetchRequest = Self.fetchRequest() as NSFetchRequest<NSFetchRequestResult>
            let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
            deleteRequest.resultType = .resultTypeObjectIDs
            if let result = try? backgroundContext.execute(deleteRequest) as? NSBatchDeleteResult,
               let objectIDs = result.result as? [NSManagedObjectID] {
                let changes = [NSDeletedObjectsKey: objectIDs]
                NSManagedObjectContext.mergeChanges(fromRemoteContextSave: changes, into: [currentContext])
            }
        }
    }
}
```

## 6. Relationships

| Type | Swift Property | Model |
|------|---------------|-------|
| To-one | `@NSManaged var country: Country` | To-One relationship |
| To-many unordered | `@NSManaged var moods: Set<Mood>` | To-Many, unordered |
| To-many ordered | `@NSManaged var items: NSOrderedSet` | To-Many, ordered |

- **Always define inverse relationships** in the model
- Core Data automatically maintains inverses
- For to-many mutation: use `mutableSetValue(forKey:)` or `mutableOrderedSetValue(forKey:)`

## 7. Delete Rules

| Rule | Behavior |
|------|----------|
| **Nullify** | Related object stays; inverse nullified |
| **Cascade** | Deleting also deletes related objects |
| **Deny** | Deletion fails if relationship not empty |
| **No Action** | Nothing happens; you handle manually. Dangerous. |

Custom logic via `prepareForDeletion()`:
```swift
override func prepareForDeletion() {
    guard let parent = parent else { return }
    if parent.children.filter({ !$0.isDeleted }).isEmpty {
        managedObjectContext?.delete(parent)
    }
}
```

## 8. Subentities — Warning

Subentities share a **single SQLite table**. All attributes from all subentities are combined.
This causes performance and memory problems at scale.

**Rule:** Only use subentities if you could collapse them into one entity with a "type" enum.
Prefer protocols over subclassing for shared behavior.

## 9. Data Types & Custom Types

### Standard Types
| Type | Notes |
|------|-------|
| Integer 16/32/64 | Choose smallest that fits |
| Double | Prefer over Float |
| Decimal | Use `NSDecimalNumber` for currency |
| Boolean | Stored as 0 or 1 |
| Date | Seconds since Jan 1, 2001 UTC. No timezone. |
| String | Full Unicode |
| Binary Data | Enable "Allows External Storage" for >100KB |
| Transformable | Conforms to NSCoding |

### Enum Storage
```swift
@NSManaged private var primitiveType: NSNumber
var type: MessageType {
    get {
        willAccessValue(forKey: "type")
        let val = MessageType(rawValue: primitiveType.int16Value) ?? .text
        didAccessValue(forKey: "type")
        return val
    }
    set {
        willChangeValue(forKey: "type")
        primitiveType = NSNumber(value: newValue.rawValue)
        didChangeValue(forKey: "type")
    }
}
```

### JSON-Encoded Complex Types (Production Pattern)
```swift
private static let encoder = JSONEncoder()
private static let decoder = JSONDecoder()

@NSManaged private var primitiveDiscount: Data?

var discount: DiscountType? {
    get {
        willAccessValue(forKey: Self.discountKey)
        let value: DiscountType? = if let data = primitiveDiscount {
            try? Self.decoder.decode(DiscountType.self, from: data)
        } else { nil }
        didAccessValue(forKey: Self.discountKey)
        return value
    }
    set {
        willChangeValue(forKey: Self.discountKey)
        primitiveDiscount = if let newValue { try? Self.encoder.encode(newValue) } else { nil }
        didChangeValue(forKey: Self.discountKey)
    }
}
```

### Optional Doubles — Use NSNumber
```swift
@NSManaged fileprivate var latitude: NSNumber?
@NSManaged fileprivate var longitude: NSNumber?

var location: CLLocation? {
    guard let lat = latitude, let lon = longitude else { return nil }
    return CLLocation(latitude: lat.doubleValue, longitude: lon.doubleValue)
}
```

### Custom types must be immutable
Mutating a stored object in-place bypasses change tracking, causing data loss.
