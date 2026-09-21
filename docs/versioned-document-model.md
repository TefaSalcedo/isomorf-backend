# Modelo de documento versionado — por qué importa

> Semana 2 del roadmap. Este documento explica qué se construyó, por qué se
> eligió este diseño y qué habilita para el futuro del producto.

## El problema que resuelve

Antes de este cambio, `project_elements` era una tabla "viva" sin memoria: cada
`PUT/DELETE` sobrescribía el estado y el undo/redo existía solo en la RAM del
navegador. Consecuencias reales:

- Recargar la página o cambiar de dispositivo **borraba el historial de deshacer**.
- Un borrado accidental era **irrecuperable** en cuanto se guardaba.
- No había **trazabilidad**: imposible saber qué cambió, cuándo y en qué orden.
- La colaboración en tiempo real (Fase 1 del roadmap) no tiene base sin un
  historial de revisiones en el servidor: el servidor debe saber cuál es la
  versión "verdadera" del documento para sincronizar clientes.

## El diseño

```
projects.current_revision ──┐   puntero: "el documento está en la revisión N"
                            ▼
project_documents (snapshot completo por revisión)
   rev 1: { elements: [], design_settings: {...}, load_links: {} }   ← baseline
   rev 2: { elements: [wall], ... }
   rev 3: { elements: [wall, column], ... }
                            ▲
element_revisions (diff por elemento de cada revisión)
   rev 3: { element_id: col-1, operation: 'create', before: null, after: {...} }
```

- **Snapshot + diff**: el snapshot permite restaurar cualquier estado en O(1)
  sin replayar la historia; `element_revisions` responde "qué cambió en esta
  revisión" para el panel de historial y para auditoría.
- **Las tablas vivas mandan**: `project_elements` siempre refleja la revisión
  actual. Undo/redo *aplican* el snapshot destino a las tablas vivas en la misma
  transacción, así `GET /projects/{id}` es consistente sin lógica extra.
- **Truncado del futuro**: guardar estando en una revisión antigua descarta las
  revisiones posteriores (semántica clásica de undo, igual que en editores de
  escritorio).
- **Baseline perezoso**: proyectos anteriores a la migración materializan su
  revisión 1 desde el estado vivo en el primer guardado; los nuevos la crean
  al nacer. El undo siempre tiene un estado al que volver.
- **`load_links`**: `element_loads.element_id` usa `ON DELETE SET NULL`. Cada
  snapshot registra qué cargas apuntaban a qué elemento, y los endpoints de
  cargas refrescan el snapshot de la revisión actual — así, deshacer un borrado
  **re-vincula las cargas** en vez de dejarlas huérfanas.
- **Concurrencia**: `SELECT … FOR UPDATE` sobre la fila del proyecto serializa
  save/undo/redo/restore; la restricción `UNIQUE(project_id, revision)` es la
  última línea de defensa.

## Endpoints

| Método | Ruta | Efecto |
|---|---|---|
| `PUT` | `/api/projects/{id}/document` | Guardado atómico: elementos + design_settings + nombre en una transacción, crea revisión |
| `GET` | `/api/projects/{id}/history` | Lista revisiones con sus diffs por elemento |
| `POST` | `/api/projects/{id}/history/undo` | Retrocede el puntero y aplica el snapshot |
| `POST` | `/api/projects/{id}/history/redo` | Avanza el puntero |
| `POST` | `/api/projects/{id}/history/{rev}/restore` | Salta a cualquier revisión (panel de historial) |

Un guardado sin cambios reales no crea revisión (los diffs vacíos no ensucian
el historial).

## Trade-offs conscientes

- **Los endpoints CRUD individuales de elementos no versionan.** El editor ya
  guarda por documento; los endpoints antiguos quedan como API de bajo nivel.
  Un cambio por esa vía queda dentro del siguiente snapshot, sin diff propio.
- **Guardado completo vs. incremental**: enviar todos los elementos en cada save
  es O(n) pero con proyectos de plano 2D es trivial, y la atomicidad elimina la
  clase de errores "guardé 4 de 5 elementos" que tenía el flujo anterior de N
  llamadas.
- **`before`/`after` completos** por elemento en vez de diff campo-a-campo:
  más bytes, pero cada cambio es auditable y reconstruible sin ambigüedad.

## Qué habilita

- **Semana 6 (presencia/edición concurrente)**: `current_revision` es el número
  de versión que los clientes intercambiarán por WebSocket para detectar
  divergencias; `element_revisions` ya separa los cambios por elemento
  (last-writer-wins por elemento).
- **Recuperación ante desastres** y soporte: "vuelve al estado de ayer" es un
  `restore` a una revisión.
- **Memoria de cálculo con trazabilidad** (Fase 4): los resultados podrán
  referenciar la revisión exacta del modelo que los produjo.
