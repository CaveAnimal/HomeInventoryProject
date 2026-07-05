# Container Hierarchy

## Idea

Expand the app from a box inventory to a container inventory. A container can be a box, but it can also be a room, garage, basement, closet, shelf, cabinet, drawer, tool chest, bag, safe, vehicle, or area.

## Model

Instead of:

```text
Box -> Items
```

use:

```text
Container -> child containers
Container -> items
Container -> photos
Container -> location
Container -> QR label
```

## Examples

```text
House
  Garage
    Tool chest
      Top drawer
        Wrenches
        Socket set
      Bottom drawer
        Drill bits
    Shelf A
      Blue tote
        Extension cords

Basement
  Storage rack
    Box 014
      Winter gloves
```

## Requirements

- A container can contain other containers.
- A container can contain items directly.
- Every container can have photos, notes, tags, and a QR code.
- A room can be a top-level container.
- A tool chest can have drawers as child containers.
- A garage can contain many nested containers.
- Search results should show the full path to the item.

Example:

```text
Item: 10mm socket
Location: House -> Garage -> Tool chest -> Top drawer
Position: east wall, 4 ft from north wall, 3 ft high
```

## Implementation Notes

- Rename the internal model from `Box` to `Container`.
- Preserve `box` as a container type.
- Migrate existing boxes into containers with `type = "box"`.
- Add `parent_container_id` to support nesting.
- Update QR pages so every container can be scanned.

