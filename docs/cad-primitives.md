# CAD primitives — element API contract (Week 8) + blocks (Week 10)

Week 8 does **not** add new endpoints. It extends the `element_type` enum
(migration `0008_cad_primitives`), so the existing element and document
endpoints accept seven new CAD annotation types alongside the structural
ones.

Week 10 adds `block_ref` (migration `0009_blocks_library`) and a
project-scoped block library (`/api/projects/{id}/blocks`).

## `element_type` values (week 8 + 10)

| Type | Geometry stored in `x1,y1 → x2,y2` | Extra keys in `properties` |
|---|---|---|
| `line` | Segment endpoints | — |
| `polyline` | Bounding box | `points: [{x,y}, …]` (cm), `closed: bool` |
| `arc` | Bounding box | `cx`, `cy`, `radius` (cm), `start_angle`, `end_angle` (rad, CCW), `clockwise: bool`, `mid: {x,y}` |
| `circle` | Bounding box (`x1,y1` = center) | `radius` (cm) |
| `ellipse` | Bounding box | — |
| `rectangle` | Bounding box | — |
| `hatch` | Bounding box | `pattern: 'ansi31'`, `spacing` (cm), `angle` (deg) |
| `block_ref` | Bounding box of the placed instance | `block_id` (UUID of a `project_blocks` row), `scale` (optional) |

Coordinates are centimeters in plan space (the `length` column stores
meters where meaningful — e.g. arc length, circle circumference).

## Affected endpoints (unchanged routes, extended enum)

```
GET    /api/projects/{project_id}/elements
POST   /api/projects/{project_id}/elements
PUT    /api/projects/{project_id}/elements/{element_id}
DELETE /api/projects/{project_id}/elements/{element_id}
PUT    /api/projects/{project_id}/document        # versioned snapshot
```

## Example — create a closed polyline (6×4 m plan)

```http
POST /api/projects/{project_id}/elements
Content-Type: application/json
```

```json
{
  "element_type": "polyline",
  "x1": 0, "y1": 0, "x2": 600, "y2": 400,
  "length": 20.0,
  "properties": {
    "points": [{"x":0,"y":0},{"x":600,"y":0},{"x":600,"y":400},{"x":0,"y":400},{"x":0,"y":0}],
    "closed": true
  }
}
```

## Example — arc through three points

```json
{
  "element_type": "arc",
  "x1": 0, "y1": 0, "x2": 100, "y2": 100,
  "length": 157.08,
  "properties": {
    "cx": 50, "cy": 0, "radius": 100,
    "start_angle": 3.1416, "end_angle": 1.5708,
    "clockwise": false, "mid": {"x": 100, "y": 50}
  }
}
```

## Validation rules

- `length` must be `> 0` for every element.
- `x1,y1` and `x2,y2` must differ — **except** for `polyline`, where a
  closed shape legitimately shares its first and last vertex, and
  `block_ref`, whose contents may collapse to a single insertion point.
- CAD types accept `material_id`/`section_id` as `null`; they carry no
  structural role and are ignored by analysis consumers.

## Block library (week 10)

A block is a named group of items stored in block-local coordinates
(plan centimeters, relative to `base_x, base_y`). A `block_ref` element
references it through `properties.block_id`; the frontend expands the
reference for display, and `explode` converts it back into real
elements. Deleting a block that still has live references returns `409`.

```
GET    /api/projects/{project_id}/blocks
POST   /api/projects/{project_id}/blocks
GET    /api/projects/{project_id}/blocks/{block_id}
PUT    /api/projects/{project_id}/blocks/{block_id}
DELETE /api/projects/{project_id}/blocks/{block_id}   # 409 while in use
```

`items[]` follows the same shape as `ElementPayload` (element_type,
x1/y1/x2/y2 in cm, length > 0, rotation, optional material_id /
section_id, properties).

```json
{
  "name": "Title block A1",
  "base_x": 0, "base_y": 0,
  "items": [
    {"element_type": "rectangle", "x1": 0, "y1": 0, "x2": 84, "y2": 59, "length": 286}
  ]
}
```

## Layer line styles (week 10)

`design_settings.layers[]` accepts two optional fields on top of
`id/name/color/visible/locked`:

- `linetype`: `'solid' | 'dashed' | 'dotted' | 'dashdot' | 'center' | 'hidden'`
- `lineweight`: number, millimeters (`0.05`–`2.0`)

Elements may override them per element via `properties.linetype` /
`properties.lineweight` (absent = ByLayer).
