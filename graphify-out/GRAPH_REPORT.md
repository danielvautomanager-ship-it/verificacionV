# Graph Report - .  (2026-04-29)

## Corpus Check
- Corpus is ~5,229 words - fits in a single context window. You may not need a graph.

## Summary
- 73 nodes · 136 edges · 11 communities detected
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_KPI & Analytics Charts|KPI & Analytics Charts]]
- [[_COMMUNITY_Flask Route Handlers|Flask Route Handlers]]
- [[_COMMUNITY_Database CRUD Layer|Database CRUD Layer]]
- [[_COMMUNITY_Base Template & Navigation|Base Template & Navigation]]
- [[_COMMUNITY_Dashboard & Reporting API|Dashboard & Reporting API]]
- [[_COMMUNITY_Ordenes de Servicio Views|Ordenes de Servicio Views]]
- [[_COMMUNITY_Core Domain Entities|Core Domain Entities]]
- [[_COMMUNITY_Equipo Edit Flow|Equipo Edit Flow]]
- [[_COMMUNITY_Equipos List & Actions|Equipos List & Actions]]
- [[_COMMUNITY_Tecnicos List & Actions|Tecnicos List & Actions]]
- [[_COMMUNITY_Sidebar Navigation|Sidebar Navigation]]

## God Nodes (most connected - your core abstractions)
1. `Base HTML Template` - 18 edges
2. `get_db()` - 16 edges
3. `Dashboard Template` - 11 edges
4. `Reportes Indicadores KPI Template` - 9 edges
5. `listar_tecnicos()` - 6 edges
6. `kpi_resumen()` - 5 edges
7. `kpi_por_mes()` - 5 edges
8. `kpi_disponibilidad()` - 5 edges
9. `listar_equipos()` - 5 edges
10. `dashboard()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `ordenes_lista()` --calls--> `listar_os()`  [INFERRED]
  app.py → database.py
- `ordenes_detalle()` --calls--> `get_os()`  [INFERRED]
  app.py → database.py
- `ordenes_nueva()` --calls--> `crear_os()`  [INFERRED]
  app.py → database.py
- `ordenes_editar()` --calls--> `actualizar_os()`  [INFERRED]
  app.py → database.py
- `equipos_lista()` --calls--> `listar_equipos()`  [INFERRED]
  app.py → database.py

## Hyperedges (group relationships)
- **ERP Maintenance Core Entities: OS, Equipo, Tecnico** — concept_orden_servicio, concept_equipo, concept_tecnico [INFERRED 0.90]
- **KPI Reporting Flow: Dashboard, Indicadores, MTTR, Disponibilidad** — dashboard_template, reportes_indicadores_template, concept_kpi, concept_mttr, concept_disponibilidad [INFERRED 0.85]
- **All Templates Extend Base Template via Jinja2 Inheritance** — base_template, dashboard_template, equipos_form_template, equipos_lista_template, tecnicos_form_template, tecnicos_lista_template, reportes_indicadores_template, ordenes_lista_template, ordenes_nueva_template, ordenes_detalle_template [EXTRACTED 1.00]

## Communities

### Community 0 - "KPI & Analytics Charts"
Cohesion: 0.21
Nodes (15): Chart.js 4.4.3, KPI Card Component, Disponibilidad de Equipos, KPI Maintenance Indicators, MTTR (Mean Time To Repair), Disponibilidad Chart, OS por Mes Chart, Correctivo vs Preventivo Doughnut Chart (+7 more)

### Community 1 - "Flask Route Handlers"
Cohesion: 0.24
Nodes (11): equipos_lista(), equipos_nuevo(), ordenes_detalle(), ordenes_editar(), ordenes_lista(), ordenes_nueva(), tecnicos_editar(), tecnicos_lista() (+3 more)

### Community 2 - "Database CRUD Layer"
Cohesion: 0.42
Nodes (8): actualizar_os(), actualizar_tecnico(), crear_equipo(), crear_os(), crear_tecnico(), get_db(), get_os(), init_db()

### Community 3 - "Base Template & Navigation"
Cohesion: 0.28
Nodes (9): Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Base HTML Template, Flask Endpoint: dashboard, Flask Endpoint: equipos_lista, Flask Endpoint: reportes, Flask Endpoint: tecnicos_lista, Equipos Form Template (+1 more)

### Community 4 - "Dashboard & Reporting API"
Cohesion: 0.48
Nodes (7): api_kpi(), dashboard(), reportes(), kpi_disponibilidad(), kpi_por_mes(), kpi_resumen(), listar_os()

### Community 5 - "Ordenes de Servicio Views"
Cohesion: 0.33
Nodes (6): Flask Endpoint: ordenes_detalle, Flask Endpoint: ordenes_editar, Flask Endpoint: ordenes_lista, Flask Endpoint: ordenes_nueva, Ordenes Detalle Template, Ordenes Lista Template

### Community 6 - "Core Domain Entities"
Cohesion: 0.6
Nodes (5): Badge Estado Component, Equipo / Activo, Orden de Servicio (OS), Técnico, Ordenes Nueva Template

### Community 7 - "Equipo Edit Flow"
Cohesion: 0.67
Nodes (3): equipos_editar(), actualizar_equipo(), get_equipo()

### Community 8 - "Equipos List & Actions"
Cohesion: 0.67
Nodes (3): Flask Endpoint: equipos_editar, Flask Endpoint: equipos_nuevo, Equipos Lista Template

### Community 9 - "Tecnicos List & Actions"
Cohesion: 0.67
Nodes (3): Flask Endpoint: tecnicos_editar, Flask Endpoint: tecnicos_nuevo, Tecnicos Lista Template

### Community 10 - "Sidebar Navigation"
Cohesion: 1.0
Nodes (1): Sidebar Navigation

## Knowledge Gaps
- **15 isolated node(s):** `KPI Card Component`, `Badge Estado Component`, `Sidebar Navigation`, `Bootstrap 5.3.3`, `Bootstrap Icons 1.11.3` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Sidebar Navigation`** (1 nodes): `Sidebar Navigation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Base HTML Template` connect `Base Template & Navigation` to `KPI & Analytics Charts`, `Ordenes de Servicio Views`, `Core Domain Entities`, `Equipos List & Actions`, `Tecnicos List & Actions`?**
  _High betweenness centrality (0.205) - this node is a cross-community bridge._
- **Why does `Dashboard Template` connect `KPI & Analytics Charts` to `Base Template & Navigation`, `Ordenes de Servicio Views`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `Reportes Indicadores KPI Template` connect `KPI & Analytics Charts` to `Base Template & Navigation`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `listar_tecnicos()` (e.g. with `ordenes_nueva()` and `ordenes_detalle()`) actually correct?**
  _`listar_tecnicos()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `KPI Card Component`, `Badge Estado Component`, `Sidebar Navigation` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._