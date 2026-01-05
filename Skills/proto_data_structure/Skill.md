---
name: Proto Data Structure
description: Analyze web application requirements through web search to identify domain entities, relationships, and data contracts. Generates protobuf schema definitions.
dependencies: protobuf>=4.0
---

# Proto Data Structure Skill

## Overview

This skill performs domain analysis for web applications by conducting web searches to identify:
- Core domain entities (nouns in the system)
- Entity relationships and cardinalities
- Data fields and types for each entity
- API request/response patterns
- Real-time event structures

The output is a complete Protocol Buffers schema that serves as the single source of truth for data contracts between frontend and backend.

## When to Use This Skill

**Use this skill when:**
- Starting a new web application project
- Defining data models for a domain you're unfamiliar with
- Need to identify standard industry patterns for a specific domain
- Creating protobuf schemas from requirements

**Do NOT use when:**
- Domain model is already well-defined
- Working with existing protobuf schemas
- Simple CRUD apps with obvious entities

## Workflow

### Step 1: Gather Requirements

Ask clarifying questions about:
1. **Domain**: What problem does this app solve?
2. **Users**: Who are the primary users?
3. **Core actions**: What are the main things users do?
4. **Data sensitivity**: Any compliance requirements (HIPAA, GDPR)?

### Step 2: Web Search for Domain Patterns

Conduct targeted searches to understand:
```
Search queries to perform:
- "[domain] data model best practices"
- "[domain] database schema design"
- "[domain] entity relationship diagram"
- "[domain] API design patterns"
- "[domain] protobuf examples"
```

### Step 3: Identify Core Entities

From search results, extract:

| Entity Type | Examples | Characteristics |
|-------------|----------|-----------------|
| **Primary** | User, Product, Order | Core business objects |
| **Supporting** | Address, PaymentMethod | Belongs to primary entities |
| **Junction** | OrderItem, UserRole | Many-to-many relationships |
| **Audit** | Event, Log | Track changes over time |

### Step 4: Define Field Types

Use protobuf best practices for field types:

| Data Type | Proto Type | Notes |
|-----------|------------|-------|
| IDs | `int32` or `string` | Use string for UUIDs |
| Text | `string` | For all textual content |
| Boolean flags | `bool` | True/false states |
| Timestamps | `int64` | Unix epoch (seconds or ms) |
| Money | `int64` | Store as cents, not floats |
| Enums | `enum` | Fixed set of values |
| Lists | `repeated` | Arrays of items |

### Step 5: Generate Protobuf Schema

Follow this structure pattern:

```protobuf
syntax = "proto3";

package domain_name;

// 1. Core domain entities
message Entity {
  int32 id = 1;
  string name = 2;
  // ... domain-specific fields
  int64 created_at = 100;  // Timestamps at high field numbers
  int64 updated_at = 101;
}

// 2. Collection wrapper
message EntityList {
  repeated Entity items = 1;
}

// 3. Request messages (input validation at schema level)
message CreateEntityRequest {
  string name = 1;
  // Only include required fields for creation
}

message UpdateEntityRequest {
  int32 id = 1;
  // Include all updateable fields
}

// 4. API response wrapper
message ApiResponse {
  bool success = 1;
  string message = 2;
  oneof data {
    Entity entity = 3;
    EntityList entity_list = 4;
    EntityStats stats = 5;
  }
}

// 5. Real-time events
enum EventType {
  CREATED = 0;
  UPDATED = 1;
  DELETED = 2;
}

message DomainEvent {
  EventType type = 1;
  Entity entity = 2;      // For CREATED/UPDATED
  int32 deleted_id = 3;   // For DELETED
  EntityStats stats = 4;  // Updated aggregate stats
}

// 6. Statistics/aggregates
message EntityStats {
  int32 total = 1;
  int32 active = 2;
  // Domain-specific aggregates
}
```

## Output Artifacts

After running this skill, you should have:

1. **`protos/[domain].proto`** - Complete protobuf schema
2. **Entity relationship notes** - Document explaining relationships
3. **Field justifications** - Why each field was chosen

## Example: Task Management Domain

**Web search conducted for:** "task management data model"

**Identified entities:**
- Task (primary)
- Project (primary, parent of Task)
- Label (supporting, many-to-many with Task)
- Comment (supporting, belongs to Task)
- User (primary, assigned to Tasks)

**Generated schema excerpt:**

```protobuf
syntax = "proto3";
package taskmanager;

enum Priority {
  LOW = 0;
  MEDIUM = 1;
  HIGH = 2;
  URGENT = 3;
}

enum TaskStatus {
  TODO = 0;
  IN_PROGRESS = 1;
  REVIEW = 2;
  DONE = 3;
}

message Task {
  int32 id = 1;
  string title = 2;
  string description = 3;
  TaskStatus status = 4;
  Priority priority = 5;
  int32 project_id = 6;
  int32 assignee_id = 7;
  int64 due_date = 8;
  repeated int32 label_ids = 9;
  int64 created_at = 100;
  int64 updated_at = 101;
}

message Project {
  int32 id = 1;
  string name = 2;
  string description = 3;
  string color = 4;
  int64 created_at = 100;
}

message Label {
  int32 id = 1;
  string name = 2;
  string color = 3;
}
```

## Validation Checklist

Before finalizing the schema:

- [ ] All entities have unique `id` field as first field
- [ ] Timestamps use `int64` (Unix epoch)
- [ ] Money/currency uses integer cents, not floats
- [ ] Enums start with a zero value (proto3 requirement)
- [ ] Field numbers follow logical grouping
- [ ] Request messages only include necessary fields
- [ ] Response wrapper supports all response types
- [ ] Event types cover CRUD operations

## Code Generation

After schema is finalized, generate Python code:

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --pyi_out=./protos ./protos/[domain].proto
cp protos/[domain].proto static/[domain].proto
```

## Resources

- [Protocol Buffers Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [API Design Patterns](https://cloud.google.com/apis/design)
- Reference implementation: `protos/todo.proto` in this boilerplate

