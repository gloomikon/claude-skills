# Model Versions & Migrations

## Table of Contents
1. When Migrations Are Needed
2. Lightweight (Inferred) Migrations
3. Model Version Management
4. Progressive Migration
5. Custom Mapping Models
6. Custom Entity Mapping Policies
7. Testing Migrations

---

## 1. When Migrations Are Needed

Once an app is in production, changes to the data model require versioned models and migrations.
Opening an SQLite store with a mismatched model throws an exception.

**Consider first:** Can you skip migration entirely? (re-download from server, regenerate data)

## 2. Lightweight (Inferred) Migrations

Handle automatically:
- Adding, removing, renaming attributes/relationships/entities
- Changing optional status (must provide default for optional → non-optional)
- Adding/removing indexes and unique constraints

**For renames:** Set the **renaming ID** on the new attribute to the old name.

`NSPersistentContainer` uses automatic (lightweight) migration by default.

## 3. Model Version Management

```swift
enum MoodyModelVersion: String {
    case version1 = "Moody"
    case version2 = "Moody 2"
    case version3 = "Moody 3"

    static var all: [MoodyModelVersion] { [.version1, .version2, .version3] }
    static var current: MoodyModelVersion { .version3 }

    var successor: MoodyModelVersion? {
        switch self {
        case .version1: return .version2
        case .version2: return .version3
        case .version3: return nil
        }
    }
}
```

### Loading a Specific Model Version
```swift
func managedObjectModel() -> NSManagedObjectModel {
    let omoURL = bundle.url(forResource: name, withExtension: "omo", subdirectory: modelDir)
    let momURL = bundle.url(forResource: name, withExtension: "mom", subdirectory: modelDir)
    guard let url = omoURL ?? momURL else { fatalError("model \(self) not found") }
    return NSManagedObjectModel(contentsOf: url)!
}
```

### Detecting Store Version
```swift
guard let metadata = try? NSPersistentStoreCoordinator
    .metadataForPersistentStore(ofType: NSSQLiteStoreType, at: storeURL)
else { return nil }
let version = versions.first {
    $0.managedObjectModel().isConfiguration(withName: nil,
        compatibleWithStoreMetadata: metadata)
}
```

## 4. Progressive Migration

Migrate step-by-step: v1 → v2 → v3 → ... → current. Scales better than automatic migration
from any version to current.

```swift
func migrateStore(from sourceURL: URL, to targetURL: URL, targetVersion: Version) {
    guard let sourceVersion = Version(storeURL: sourceURL) else { fatalError() }
    var currentURL = sourceURL
    let steps = sourceVersion.migrationSteps(to: targetVersion)

    for step in steps {
        let manager = NSMigrationManager(sourceModel: step.source, destinationModel: step.destination)
        let destinationURL = URL.temporary
        for mapping in step.mappings {
            try! manager.migrateStore(
                from: currentURL, sourceType: NSSQLiteStoreType,
                options: nil, with: mapping,
                toDestinationURL: destinationURL,
                destinationType: NSSQLiteStoreType, destinationOptions: nil
            )
        }
        if currentURL != sourceURL {
            NSPersistentStoreCoordinator.destroyStore(at: currentURL)
        }
        currentURL = destinationURL
    }
    try! NSPersistentStoreCoordinator.replaceStore(at: targetURL, withStoreAt: currentURL)
}
```

**Safety:** Only replace the original store AFTER migration succeeds. Always run on background queue.

## 5. Custom Mapping Models

Create in Xcode: File → New → Mapping Model. Set source and destination models.

Custom expressions in attribute mappings:
```
$source.continent.numericISO3166Code
FUNCTION($manager, "destinationInstancesForEntityMappingNamed:sourceInstances:",
    "ContinentToContinent", $source.country.continent)
```

## 6. Custom Entity Mapping Policies

```swift
final class ItemV5ToV6Policy: NSEntityMigrationPolicy {
    override func createDestinationInstances(
        forSource sInstance: NSManagedObject,
        in mapping: NSEntityMapping,
        manager: NSMigrationManager
    ) throws {
        try super.createDestinationInstances(forSource: sInstance, in: mapping, manager: manager)
        guard let dest = manager.destinationInstances(
            forEntityMappingName: mapping.name, sourceInstances: [sInstance]).first
        else { fatalError() }
        // Custom logic using KVC on NSManagedObject
        // (old model classes are not available during migration)
    }
}
```

Use `fileprivate` KVC extensions on `NSManagedObject` since typed model classes are not available.

## 7. Testing Migrations

- Create SQLite stores with known data in old formats
- Test ALL potential migration paths (v1→v3, v2→v3, etc.)
- Verify post-migration data against hardcoded fixtures
- Use `-com.apple.CoreData.MigrationDebug 1` for diagnostics
- Integrate `NSProgress` for progress reporting on large migrations
