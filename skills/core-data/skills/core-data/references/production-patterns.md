# Production Patterns

Patterns extracted from real iOS projects (Boop & Invoice apps) that demonstrate
battle-tested Core Data architectures.

## Table of Contents
1. DatabaseManager Pattern
2. FRC → AsyncStream → @Published
3. Snapshot Cloning Pattern
4. NSManagedObjectContext Extensions
5. Network Sync Pattern
6. Dependency Injection Setup
7. SwiftUI Integration via ObservableObject Bridge
8. Soft Delete for Sync
9. Entity Inheritance for Payment Methods

---

## 1. DatabaseManager Pattern

Centralize ALL Core Data operations in a single manager class. No direct context access from views.

```swift
class DatabaseManager: ObservableObject {
    @Injected private var coreDataStack: CoreDataStack

    private var context: NSManagedObjectContext { coreDataStack.managedContext }

    // Published collections driven by FRCs
    @MainActor @Published var items: [CD_Item] = []

    // FRC storage
    private var itemsFRC: NSFetchedResultsController<CD_Item>?

    func load() async throws {
        try await coreDataStack.load()
        observeItems()
    }

    // CRUD
    func createItem(name: String) {
        context.performChanges { [self] in
            CD_Item.create(in: context, name: name)
        }
    }

    @MainActor
    func updateItem(_ item: CD_Item, name: String) {
        context.performChanges {
            item.update(name: name)
        }
    }

    @MainActor
    func deleteItem(with id: UUID) {
        guard let target = items.first(where: { $0.id == id }) else { return }
        context.performChanges { [self] in
            target.delete(in: context)
        }
    }
}
```

## 2. FRC → AsyncStream → @Published

Modern pattern bridging NSFetchedResultsController to SwiftUI/Combine:

```swift
// FRCDelegateWrapper
private class FRCDelegateWrapper: NSObject, NSFetchedResultsControllerDelegate {
    private let onChange: () -> Void
    init(onChange: @escaping () -> Void) { self.onChange = onChange }
    func controllerDidChangeContent(_ controller: NSFetchedResultsController<any NSFetchRequestResult>) {
        onChange()
    }
}

// AsyncStream factory
enum FetchResultStream {
    private static var delegates: [ObjectIdentifier: FRCDelegateWrapper] = [:]

    static func make<T: NSFetchRequestResult>(
        for frc: NSFetchedResultsController<T>
    ) -> AsyncStream<Void> {
        AsyncStream { continuation in
            let delegate = FRCDelegateWrapper { continuation.yield() }
            frc.delegate = delegate
            let key = ObjectIdentifier(frc)
            delegates[key] = delegate

            try? frc.performFetch()
            continuation.yield()

            continuation.onTermination = { _ in
                frc.delegate = nil
                delegates.removeValue(forKey: key)
            }
        }
    }
}

// Usage in DatabaseManager
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
            guard let self else { return }
            self.items = frc.sections?.first?.objects as? [CD_Item] ?? []
        }
    }
}
```

## 3. Snapshot Cloning Pattern

When creating invoices or similar records, clone related items so changes to originals
don't affect historical records:

```swift
@objc(CD_WorkItem)
class CD_WorkItem: NSManagedObject, Managed {
    @NSManaged private(set) var isSnapshotClone: Bool

    func clonedForSnapshot(in context: NSManagedObjectContext) -> Self {
        Self.create(in: context) { item in
            item.id = UUID()
            item.name = self.name
            item.price = self.price
            item.quantity = self.quantity
            item.dateCreated = Date()
            item.isSnapshotClone = true
        }
    }
}

// When creating invoice:
let snapshotItems = builder.workItems.map { $0.clonedForSnapshot(in: context) }

// When updating invoice, clean up orphaned snapshots:
let removedIds = oldItems.filter { !updatedIds.contains($0.id) }.map { $0.id }
removedIds.forEach { deleteWorkItem(with: $0) }
```

## 4. NSManagedObjectContext Extensions

```swift
extension NSManagedObjectContext {
    @discardableResult
    func saveOrRollback() -> Bool {
        do {
            try save()
            return true
        } catch {
            #if DEBUG
            print("Rollback. Error: \(error)")
            #endif
            rollback()
            return false
        }
    }

    func performSaveOrRollback() {
        perform { _ = self.saveOrRollback() }
    }

    func performChanges(block: @escaping () -> Void) {
        perform {
            block()
            _ = self.saveOrRollback()
        }
    }

    func insertObject<A: NSManagedObject>() -> A where A: Managed {
        guard let obj = NSEntityDescription.insertNewObject(
            forEntityName: A.entityName, into: self) as? A
        else { fatalError("Wrong object type") }
        return obj
    }
}
```

## 5. Network Sync Pattern

Save to Core Data first, then async network call. On failure, data persists locally.

```swift
func trackWeight(_ record: WeightRecord) {
    guard let user else { return }
    context.performChanges { [self] in
        CD_WeightRecord.insert(
            into: context, id: record.id, user: user,
            value: record.weight.value, weightUnit: record.weight.weightUnit,
            date: record.date
        )
        user.update()  // Touch lastModifiedDate
    }
    // Network call is fire-and-forget; data is already persisted
    Task {
        try await networkService.logWeight(record)
    }
}
```

## 6. Dependency Injection Setup

Register as singletons via DI container:

```swift
container.register(CoreDataStack.self) { CoreDataStack() }
    .inObjectScope(.container)

container.register(DatabaseManager.self) { DatabaseManager() }
    .inObjectScope(.container)
```

Load in startup sequence:
```swift
func start() async {
    try await databaseManager.load()
}
```

## 7. SwiftUI Integration via ObservableObject Bridge

Bridge Core Data to SwiftUI through an ObservableObject that wraps DatabaseManager:

```swift
class UserInfoProvider: ObservableObject {
    @Injected private var database: DatabaseManager
    @Published var user: CD_User?

    // Computed properties convert CD entities to view models
    var weightRecords: [WeightRecord] {
        user?.records.map { WeightRecord($0) } ?? []
    }

    init() {
        database.$user
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in self?.objectWillChange.send() }
            .store(in: &cancellables)
    }
}
```

## 8. Soft Delete for Sync

Never delete directly when sync is involved. Mark for deletion, let sync engine handle it:

```swift
func markForRemoval(_ item: CD_Item) {
    context.performChanges {
        item.markedForDeletionDate = Date()
        item.user?.update()
    }
}

// Default predicate excludes marked items from UI:
static var defaultPredicate: NSPredicate {
    NSPredicate(format: "%K == NULL", #keyPath(markedForDeletionDate))
}

// Sync engine picks up marked items and handles backend deletion
// After successful backend deletion, perform actual Core Data delete
```

## 9. Entity Inheritance for Payment Methods

Abstract parent entity with concrete subentities when types share relationships but differ in data:

```swift
// Abstract parent
@objc(CD_PaymentMethod)
class CD_PaymentMethod: NSManagedObject, Managed {
    @NSManaged private(set) var id: UUID
    @NSManaged private(set) var isSnapshotClone: Bool

    var paymentMethod: any PaymentMethod { fatalError("Override in subclass") }
    func clonedForSnapshot(in context: NSManagedObjectContext) -> Self { fatalError() }
}

// Concrete subentity
@objc(CD_BankTransfer)
class CD_BankTransfer: CD_PaymentMethod {
    @NSManaged private(set) var title: String
    @NSManaged private(set) var body: String

    override var paymentMethod: any PaymentMethod {
        BankTransfer(title: title, body: body)
    }

    override func clonedForSnapshot(in context: NSManagedObjectContext) -> Self {
        Self.create(in: context) { entity in
            entity.id = UUID()
            entity.isSnapshotClone = true
            entity.title = self.title
            entity.body = self.body
        }
    }
}
```

**Remember:** All subentities share ONE SQLite table. Only use when types are truly variants
of the same concept and you need them in a single relationship/fetch.
