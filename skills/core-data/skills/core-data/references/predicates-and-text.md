# Predicates & Text

## Table of Contents
1. NSPredicate Basics
2. Format Specifiers
3. Combining Predicates
4. Relationship Traversal
5. Subqueries
6. String Matching
7. Text Normalization for Search
8. Gotchas

---

## 1. NSPredicate Basics

Always use `#keyPath()` instead of hardcoded strings:

```swift
let predicate = NSPredicate(format: "%K == %@", #keyPath(Person.name), "John")
```

## 2. Format Specifiers

| Specifier | Use For |
|-----------|---------|
| `%K` | Key paths (attribute names) |
| `%@` | Objects, Date (as NSDate), NSNumber, arrays |
| `%ld` | Int |
| `%la` | Double |
| `%a` | Float |

**No automatic NSNumber conversion** — passing Int with `%@` produces wrong predicates.

## 3. Combining Predicates

```swift
// AND
let both = NSCompoundPredicate(andPredicateWithSubpredicates: [pred1, pred2])

// OR
let either = NSCompoundPredicate(orPredicateWithSubpredicates: [pred1, pred2])

// NOT
let negated = NSCompoundPredicate(notPredicateWithSubpredicate: pred1)
```

### Protocol-Based Predicate Composition
```swift
extension Person {
    static var recentPredicate: NSPredicate {
        let date = Calendar.current.date(byAdding: .day, value: -7, to: Date())!
        return NSPredicate(format: "%K > %@", #keyPath(Person.modifiedDate), date as NSDate)
    }
    static var activePredicate: NSPredicate {
        NSPredicate(format: "%K == YES", #keyPath(Person.isActive))
    }
}
```

## 4. Relationship Traversal

### To-One
```swift
NSPredicate(format: "%K.%K > %ld", #keyPath(City.mayor), #keyPath(Person.age), 30)
```

### To-Many with ANY
```swift
NSPredicate(format: "ANY %K.%K <= %ld", #keyPath(City.residents), #keyPath(Person.age), 20)
```

### Matching Objects Directly
```swift
NSPredicate(format: "self == %@", person)
NSPredicate(format: "self IN %@", somePeople)
NSPredicate(format: "%K CONTAINS %@", #keyPath(City.visitors), person)
```

## 5. Subqueries

For checking multiple attributes on the SAME related object (multiple `ANY` checks different objects):

```swift
// Cities where ALL residents are younger than 36
NSPredicate(format: "(SUBQUERY(%K, $x, $x.%K >= %ld).@count == 0)",
    #keyPath(City.residents), #keyPath(Person.age), 36)
```

## 6. String Matching

### Operators

| Operator | CAN use index | Notes |
|----------|--------------|-------|
| `==[n]` | Yes | Exact match |
| `BEGINSWITH[n]` | Yes | Prefix match |
| `IN[n]` | Yes | Set membership |
| `ENDSWITH[n]` | No | Suffix match |
| `CONTAINS[n]` | No | Substring match |
| `LIKE[n]` | No | Wildcard (`?` = one char, `*` = any) |
| `MATCHES[n]` | No | Regex |

The `[n]` option = byte-by-byte comparison (no locale). Use on normalized strings.

### Case/Diacritic-Insensitive (small datasets only)
```swift
NSPredicate(format: "%K BEGINSWITH[cd] %@", #keyPath(City.name), searchTerm)
```
Very expensive on large datasets — cannot use indexes.

## 7. Text Normalization for Search

Create a `name_normalized` attribute alongside `name`:

```swift
extension String {
    var normalizedForSearch: String {
        applyingTransform(
            StringTransform("Any-Latin; Latin-ASCII; Lower"),
            reverse: false
        ) ?? ""
    }
}
```

Keep normalized attribute in sync:
```swift
var name: String {
    set {
        willChangeValue(forKey: #keyPath(name))
        primitiveName = newValue
        setValue(newValue.normalizedForSearch, forKey: "name_normalized")
        didChangeValue(forKey: #keyPath(name))
    }
    // ...
}
```

Search using normalized strings:
```swift
NSPredicate(format: "%K BEGINSWITH[n] %@",
    "name_normalized", searchTerm.normalizedForSearch)
```

With an index on `name_normalized`, this is **10-15x faster** than `[cd]` on ~4,000 rows.

## 8. Gotchas

### Optional Values
`!= 2` on a fetch request will NOT return objects where attribute is `nil` (SQLite behavior).
Always add explicit nil checks:
```swift
NSPredicate(format: "%K != 2 AND %K != nil",
    #keyPath(Person.count), #keyPath(Person.count))
```

### Date Comparisons
Dates stored as floating-point seconds. Use ranges, not equality:
```swift
NSPredicate(format: "%K BETWEEN {%@, %@}",
    #keyPath(Person.modifiedDate), startDate as NSDate, endDate as NSDate)
```

### Performance Ordering
Put indexed/most-selective predicates first:
```swift
NSPredicate(format: "%K == YES AND %K > %ld",
    #keyPath(Person.hidden), #keyPath(Person.age), 30)
```

### Transformable Values Work
```swift
let identifier: NSUUID = someRemoteIdentifier
NSPredicate(format: "%K == %@", #keyPath(City.remoteIdentifier), identifier)
```
Core Data handles transformation automatically.
