# Graph Report - .  (2026-04-29)

## Corpus Check
- Corpus is ~5,421 words - fits in a single context window. You may not need a graph.

## Summary
- 108 nodes · 191 edges · 13 communities detected
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 38 edges (avg confidence: 0.81)
- Token cost: 3,800 input · 2,100 output

## Community Hubs (Navigation)
- [[_COMMUNITY_UI Templates & Base Layout|UI Templates & Base Layout]]
- [[_COMMUNITY_KPI & Analytics Charts|KPI & Analytics Charts]]
- [[_COMMUNITY_DB Layer & Edit Routes|DB Layer & Edit Routes]]
- [[_COMMUNITY_Flask Route Handlers|Flask Route Handlers]]
- [[_COMMUNITY_Equipos & Tecnicos Edit Flow|Equipos & Tecnicos Edit Flow]]
- [[_COMMUNITY_Ordenes & Equipos List Routes|Ordenes & Equipos List Routes]]
- [[_COMMUNITY_Ordenes & Equipos CRUD|Ordenes & Equipos CRUD]]
- [[_COMMUNITY_Dashboard & KPI API|Dashboard & KPI API]]
- [[_COMMUNITY_Dashboard & Reporting Layer|Dashboard & Reporting Layer]]
- [[_COMMUNITY_App Bootstrap & DB Schema|App Bootstrap & DB Schema]]
- [[_COMMUNITY_Ordenes Detail & Tecnicos|Ordenes Detail & Tecnicos]]
- [[_COMMUNITY_Sidebar Navigation|Sidebar Navigation]]
- [[_COMMUNITY_Agent Configuration|Agent Configuration]]

## God Nodes (most connected - your core abstractions)
1. `Base HTML Template` - 18 edges
2. `get_db()` - 16 edges
3. `get_db` - 15 edges
4. `Dashboard Template` - 11 edges
5. `Reportes Indicadores KPI Template` - 9 edges
6. `listar_tecnicos()` - 6 edges
7. `init_db` - 6 edges
8. `kpi_disponibilidad` - 6 edges
9. `listar_os` - 6 edges
10. `kpi_resumen()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `dashboard()` --calls--> `listar_os()`  [INFERRED]
  app.py → database.py
- `equipos_lista()` --calls--> `listar_equipos()`  [INFERRED]
  app.py → database.py
- `ordenes_nueva()` --calls--> `listar_tecnicos()`  [INFERRED]
  app.py → database.py
- `tecnicos_lista()` --calls--> `listar_tecnicos()`  [INFERRED]
  app.py → database.py
- `ordenes_lista route handler` --calls--> `listar_os`  [EXTRACTED]
  app.py → database.py

## Hyperedges (group relationships)
- **All Templates Extend Base Template via Jinja2 Inheritance** — base_template, dashboard_template, equipos_form_template, equipos_lista_template, tecnicos_form_template, tecnicos_lista_template, reportes_indicadores_template, ordenes_lista_template, ordenes_nueva_template, ordenes_detalle_template [EXTRACTED 1.00]
- **KPI Reporting Flow: Dashboard, Indicadores, MTTR, Disponibilidad** — dashboard_template, reportes_indicadores_template, concept_kpi, concept_mttr, concept_disponibilidad [INFERRED 0.85]
- **ERP Maintenance Core Entities: OS, Equipo, Tecnico** — concept_orden_servicio, concept_equipo, concept_tecnico [INFERRED 0.90]
- **KPI Data Flow: Dashboard and Reportes consume KPI functions from database** — app_dashboard, app_reportes, database_kpi_resumen, database_kpi_por_mes, database_kpi_disponibilidad [INFERRED 0.90]
- **Service Order CRUD Flow: routes create/read/update orders via database layer recording history** — app_ordenes_nueva, database_crear_os, database_tabla_historial_estados [EXTRACTED 0.95]
- **Database Schema Initialization: init_db creates all four core tables** — database_init_db, database_tabla_equipos, database_tabla_tecnicos, database_tabla_ordenes_servicio, database_tabla_historial_estados [EXTRACTED 1.00]

## Communities

### Community 0 - "UI Templates & Base Layout"
Cohesion: 0.12
Nodes (26): Badge Estado Component, Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Base HTML Template, Equipo / Activo, Orden de Servicio (OS), Técnico, Flask Endpoint: dashboard (+18 more)

### Community 1 - "KPI & Analytics Charts"
Cohesion: 0.21
Nodes (15): Chart.js 4.4.3, KPI Card Component, Disponibilidad de Equipos, KPI Maintenance Indicators, MTTR (Mean Time To Repair), Disponibilidad Chart, OS por Mes Chart, Correctivo vs Preventivo Doughnut Chart (+7 more)

### Community 2 - "DB Layer & Edit Routes"
Cohesion: 0.33
Nodes (9): equipos_editar(), equipos_nuevo(), ordenes_editar(), actualizar_equipo(), actualizar_os(), crear_equipo(), get_db(), get_equipo() (+1 more)

### Community 3 - "Flask Route Handlers"
Cohesion: 0.28
Nodes (8): ordenes_detalle(), tecnicos_editar(), tecnicos_lista(), tecnicos_nuevo(), actualizar_tecnico(), crear_tecnico(), get_os(), listar_tecnicos()

### Community 4 - "Equipos & Tecnicos Edit Flow"
Cohesion: 0.29
Nodes (8): equipos_editar route handler, equipos_nuevo route handler, tecnicos_nuevo route handler, actualizar_equipo, crear_equipo, crear_tecnico, get_db, get_equipo

### Community 5 - "Ordenes & Equipos List Routes"
Cohesion: 0.25
Nodes (8): equipos_lista route handler, ordenes_editar route handler, ordenes_lista route handler, ordenes_nueva route handler, actualizar_os, crear_os, listar_equipos, DB Table: historial_estados

### Community 6 - "Ordenes & Equipos CRUD"
Cohesion: 0.33
Nodes (6): equipos_lista(), ordenes_lista(), ordenes_nueva(), crear_os(), listar_equipos(), listar_os()

### Community 7 - "Dashboard & KPI API"
Cohesion: 0.6
Nodes (6): api_kpi(), dashboard(), reportes(), kpi_disponibilidad(), kpi_por_mes(), kpi_resumen()

### Community 8 - "Dashboard & Reporting Layer"
Cohesion: 0.73
Nodes (6): api_kpi route handler, dashboard route handler, reportes route handler, kpi_disponibilidad, kpi_por_mes, kpi_resumen

### Community 9 - "App Bootstrap & DB Schema"
Cohesion: 0.47
Nodes (6): Flask Application, init_db, listar_os, DB Table: equipos, DB Table: ordenes_servicio, DB Table: tecnicos

### Community 10 - "Ordenes Detail & Tecnicos"
Cohesion: 0.33
Nodes (6): ordenes_detalle route handler, tecnicos_editar route handler, tecnicos_lista route handler, actualizar_tecnico, get_os, listar_tecnicos

### Community 11 - "Sidebar Navigation"
Cohesion: 1.0
Nodes (1): Sidebar Navigation

### Community 12 - "Agent Configuration"
Cohesion: 1.0
Nodes (1): Graphify Knowledge Graph Rules

## Knowledge Gaps
- **22 isolated node(s):** `OS por Mes Chart`, `KPI Card Component`, `Badge Estado Component`, `Sidebar Navigation`, `Bootstrap 5.3.3` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Sidebar Navigation`** (1 nodes): `Sidebar Navigation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Agent Configuration`** (1 nodes): `Graphify Knowledge Graph Rules`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Base HTML Template` connect `UI Templates & Base Layout` to `KPI & Analytics Charts`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `get_db` connect `Equipos & Tecnicos Edit Flow` to `Dashboard & Reporting Layer`, `App Bootstrap & DB Schema`, `Ordenes Detail & Tecnicos`, `Ordenes & Equipos List Routes`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `Dashboard Template` connect `KPI & Analytics Charts` to `UI Templates & Base Layout`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **What connects `OS por Mes Chart`, `KPI Card Component`, `Badge Estado Component` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `UI Templates & Base Layout` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._