# Documentación Técnica - Aplicación de Automatización del Microsoft 365 Roadmap

**Versión:** 2.0  
**Fecha:** 2026-09-16  
**Estado:** Producción (MCP implementado, OAuth pendiente)  
**Tecnologías principales:** Python 3.8+, MCP (Streamable HTTP), SQLite, HTML/CSS, SMTP (Office 365)

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Problema que Resuelve](#problema-que-resuelve)
3. [Objetivos del Proyecto](#objetivos-del-proyecto)
4. [Arquitectura General](#arquitectura-general)
5. [Tecnologías Utilizadas](#tecnologías-utilizadas)
6. [¿Qué es MCP?](#qué-es-mcp)
7. [Streamable HTTP](#streamable-http)
8. [Descubrimiento Dinámico de Herramientas](#descubrimiento-dinámico-de-herramientas)
9. [Obtención de Roadmaps](#obtención-de-roadmaps)
10. [Filtrado de Datos](#filtrado-de-datos)
11. [Filtro Temporal](#filtro-temporal)
12. [SQLite y Deduplicación](#sqlite-y-deduplicación)
13. [Tabla processed_items](#tabla-processed_items)
14. [Reset de Base de Datos](#reset-de-base-de-datos)
15. [DRY_RUN Mode](#dryrun-mode)
16. [Generación del HTML](#generación-del-html)
17. [Estructura del Informe](#estructura-del-informe)
18. [Email y Envío](#email-y-envío)
19. [Configuración](#configuración)
20. [Logging](#logging)
21. [Manejo de Errores](#manejo-de-errores)
22. [Tests](#tests)
23. [Seguridad](#seguridad)
24. [Ejecución Manual](#ejecución-manual)
25. [Prueba Completa desde Cero](#prueba-completa-desde-cero)
26. [Ejecución Automática](#ejecución-automática)
27. [Flujo Completo](#flujo-completo)
28. [Ejemplo Práctico](#ejemplo-práctico)
29. [¿Qué Ocurre si Algo Falla?](#qué-ocurre-si-algo-falla)
30. [Mantenimiento](#mantenimiento)
31. [Limitaciones Actuales](#limitaciones-actuales)
32. [Posibles Evoluciones](#posibles-evoluciones)
33. [Preguntas Frecuentes](#preguntas-frecuentes)
34. [Glosario](#glosario)
35. [Resumen Final](#resumen-final)

---

## RESUMEN EJECUTIVO

### ¿Qué hace la aplicación?

La aplicación automatiza completamente el proceso de recopilación, filtrado y distribución de novedades del **Microsoft 365 Roadmap**. En lugar de revisar manualmente el sitio web de Microsoft cada mes, la aplicación:

1. **Conecta con Microsoft Release Communications MCP** - obtiene datos estructurados de las novedades de productos Microsoft
2. **Filtra automáticamente** - selecciona solo las novedades relevantes para Exchange Online, Teams, SharePoint y OneDrive
3. **Evita duplicados** - mediante SQLite recuerda qué elementos ya se han procesado
4. **Genera un informe HTML profesional** - con formato visual atractivo y optimizado para email
5. **Prepara el envío** - mediante SMTP de Office 365 (con OAuth como evolución futura)

### Valor Aportado

- **Automatización:** Eliminadas todas las tareas manuales de recopilación
- **Consistencia:** El formato y contenido son idénticos cada mes
- **Trazabilidad:** SQLite registra cada elemento procesado con timestamps
- **Control de duplicados:** Imposible procesar dos veces el mismo elemento
- **Seguridad:** Las credenciales se almacenan en variables de entorno, no en código
- **Escalabilidad:** Fácil de extender a más productos o cambiar filtros

### Proceso Anterior vs Actual

**Proceso anterior (estimado basado en documentación):**
- Consulta manual del Microsoft 365 Roadmap website
- Selección manual de elementos relevantes
- Redacción manual del email
- Envío manual

**Proceso actual:**
- Automático: Se ejecuta una vez al mes sin intervención
- Determinístico: Usa reglas fijas, no depende de criterios subjetivos
- Auditable: Cada paso registrado en logs
- Reproducible: Mismo resultado cada vez

---

## PROBLEMA QUE RESUELVE

### Contexto Histórico

Anteriormente, existía un proceso basado en:

```
Microsoft RSS
    ↓
Make (automatización)
    ↓
Gemini (procesamiento con IA)
    ↓
Email (SMTP)
```

**Problemas identificados:**
- RSS de Microsoft puede ser inconsistente
- Dependencia de Gemini (API externa, costo, latencia)
- Dificultad para mantener consistencia en procesamiento
- Falta de control sobre criterios de selección

### Evolución a la Arquitectura Actual

Se decidió evolucionar a:

```
Microsoft Release Communications MCP
    ↓
Python (procesamiento local)
    ↓
Filtrado determinístico
    ↓
SQLite (deduplicación)
    ↓
HTML (generación local)
    ↓
SMTP / Microsoft Graph (email)
```

**Ventajas:**
- MCP proporciona datos más estructurados que RSS
- Procesamiento local sin dependencias de APIs externas
- Reglas determinísticas y auditables (sin IA)
- Base de datos local para control total
- Mayor velocidad y menores costos operativos

---

## OBJETIVOS DEL PROYECTO

### Objetivos Conseguidos ✅

- ✅ Automatizar completamente la recopilación de datos
- ✅ Eliminar procesamiento manual de elementos
- ✅ Filtrar únicamente información relevante (4 productos específicos)
- ✅ Evitar duplicados mediante SQLite
- ✅ Generar informes HTML estructurados y profesionales
- ✅ Permitir pruebas seguras con DRY_RUN
- ✅ Registrar todas las acciones en logs detallados
- ✅ Facilitar mantenimiento del código
- ✅ Reducir dependencias externas innecesarias
- ✅ Implementar envío SMTP de Office 365

### Evoluciones Futuras 🚀

- 🔄 **OAuth 2.0 / Microsoft Graph** - autenticación moderna en lugar de SMTP
- 🔄 **Ejecución automática mensual** - Task Scheduler (Windows) o Cron (Linux)
- 🔄 **Monitorización** - alertas si falla la ejecución automática
- 🔄 **Histórico de elementos** - dashboard web con histórico de cambios
- 🔄 **Configuración de filtros dinámica** - cambiar productos sin modificar código
- 🔄 **Más productos** - extender a otros productos Microsoft

---

## ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────┐
│           MICROSOFT RELEASE COMMUNICATIONS              │
│                      MCP SERVER                         │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ STREAMABLE HTTP
                            │ JSON-RPC 2.0
                            ↓
            ┌───────────────────────────────┐
            │     PYTHON APPLICATION        │
            │  src/main_workflow_new.py     │
            └───────────┬───────────────────┘
                        │
        ┌───────────────┼───────────────────┐
        │               │                   │
        ▼               ▼                   ▼
    ┌─────────┐  ┌─────────┐        ┌──────────────┐
    │Paginación│  │Filtro   │        │ Descubrimiento
    │(50items)│  │Fecha    │        │ Dinámico de
    │por página│  │Temporal │        │ Herramientas
    └────┬────┘  └────┬────┘        └──────┬───────┘
         │             │                    │
         └─────────────┴────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  FILTRO POR PRODUCTOS│
            │ (Exchange, Teams,    │
            │  SharePoint, OneDrive│
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │      SQLITE DB       │
            │  (Deduplicación)     │
            │ processed_items.db   │
            └──────────┬───────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
        ¿Existe?              ¿Existe?
        (Procesar)            (Saltar)
            │                     │
            ▼                     ▼
    ┌─────────────┐      ┌────────────┐
    │Obtener      │      │Siguiente   │
    │Detalles     │      │Elemento    │
    │Completos    │      └────────────┘
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────┐
    │ Procesamiento       │
    │ Determinístico      │
    │ (sin IA)            │
    │ - Enriquecimiento   │
    │ - Valor estratégico │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  GENERACIÓN HTML    │
    │  - Estructura       │
    │  - Estilos CSS      │
    │  - Contenido visual │
    └──────────┬──────────┘
               │
        ┌──────┴───────┐
        │              │
    ¿DRY_RUN?     ¿DRY_RUN?
    (true)        (false)
        │              │
        ▼              ▼
    ┌────────┐    ┌──────────────┐
    │Guardar │    │ENVÍO DE EMAIL│
    │Preview │    │SMTP/Graph    │
    │HTML    │    │Marca como    │
    │Output/ │    │email_sent    │
    │roadmap │    └──────────────┘
    │preview │
    │.html   │
    └────────┘
```

---

## TECNOLOGÍAS UTILIZADAS

| Tecnología | Versión | Función | Estado |
|-----------|---------|---------|--------|
| **Python** | 3.8+ | Lenguaje principal | ✅ Implementado |
| **httpx** | 0.25.2 | Cliente HTTP async | ✅ Implementado |
| **asyncio** | Built-in | Programación asincrónica | ✅ Implementado |
| **sqlite3** | Built-in | Base de datos embebida | ✅ Implementado |
| **python-dotenv** | 1.0.0 | Gestión de variables de entorno | ✅ Implementado |
| **aiosmtplib** | 3.0.1 | Envío de email SMTP async | ✅ Implementado |
| **pytest** | 7.4.3 | Framework de testing | ✅ Implementado |
| **pytest-asyncio** | 0.21.1 | Tests async | ✅ Implementado |
| **msal** | 1.28.0 | OAuth 2.0 (Microsoft) | 🔄 Preparado/Pendiente |
| **aiohttp** | 3.9.1 | HTTP alternativo | ✅ Disponible |
| **MCP (Protocol)** | - | Acceso a Microsoft MCP | ✅ Implementado |

**Nota importante:** OAuth 2.0 está documentado y preparado para implementación futura cuando se dispongan de permisos en Azure AD.

---

## ¿QUÉ ES MCP?

### Concepto Fundamental

**MCP = Model Context Protocol**

Pero en esta aplicación, MCP **NO es un sistema de IA**. Es un protocolo estandarizado para comunicación estructurada entre clientes y servidores.

### Comparación Importante

❌ **NO es esto:**
- No usamos Claude, ChatGPT ni ninguna IA
- No es "Machine Learning"
- No hay procesamiento inteligente

✅ **Es esto:**
- Un protocolo de comunicación estructurado
- Un mecanismo para acceder a datos organizados
- Una API estandarizada de Microsoft

### Analogía Práctica

```
MCP es como un "camarero en un restaurante"

Cliente (nuestra app):
"Camarero, necesito los roadmaps recientes"

MCP (el camarero):
"Claro, aquí tengo 50 elementos para elegir"

Cliente:
"¿Cuál es la herramienta para obtener detalles?"

MCP:
"Tengo estas herramientas disponibles: [lista]"

Cliente:
"Dame detalles del elemento #123"

MCP:
"Aquí está toda la información estructurada"
```

### Componentes Clave

**Servidor MCP:**
- Microsoft Release Communications MCP
- Endpoint: `https://www.microsoft.com/releasecommunications/mcp`
- Proporciona herramientas para consultar datos de roadmap
- No requiere autenticación (es público)

**Cliente MCP:**
- Nuestra aplicación Python (`src/mcp_client.py`)
- Se conecta al servidor mediante HTTP
- Descubre herramientas disponibles dinámicamente
- Invoca herramientas con parámetros

**Herramientas MCP:**
- `get_recent_m365_roadmaps` - obtiene listado reciente (paginado)
- `get_m365_roadmap_by_id` - obtiene detalles de un elemento

---

## STREAMABLE HTTP

### ¿Qué es Streamable HTTP en MCP?

En lugar de HTTP tradicional, MCP usa **Streamable HTTP** con **Server-Sent Events (SSE)**.

### Flujo Técnico

```
Cliente Python
    │
    ├─ Construye JSON-RPC 2.0 request
    │  {
    │    "jsonrpc": "2.0",
    │    "id": 1,
    │    "method": "tools/list",
    │    "params": {...}
    │  }
    │
    ▼
POST https://www.microsoft.com/releasecommunications/mcp
    │
    ├─ Content-Type: application/json
    │
    ▼
Servidor MCP procesa
    │
    ▼
Respuesta SSE
    │
    data: {"jsonrpc": "2.0", "result": {...}}
    │
    ▼
Cliente parsea respuesta
    │
    ├─ Extrae contenido JSON
    ├─ Procesa datos
    ▼
Resultado disponible para aplicación
```

### Ventajas

- **Eficiente:** Una sola conexión para múltiples operaciones
- **Escalable:** Servidor puede procesar muchos clientes simultáneamente
- **Estructurado:** Protocolo JSON-RPC estandarizado
- **Confiable:** Manejo de errores explícito en protocolo

### En el Código

```python
# src/mcp_client.py - línea 29-48
def _build_request(self, method: str, params: Optional[Dict] = None) -> Dict:
    """Build JSON-RPC 2.0 request with MCP protocol metadata."""
    
    if params is None:
        params = {}
    
    if "_meta" not in params:
        params["_meta"] = {}
    
    params["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2026-07-28"
    params["_meta"]["io.modelcontextprotocol/clientInfo"] = {
        "name": "m365-roadmap-client",
        "version": "2.0.0"
    }
    
    return {
        "jsonrpc": "2.0",
        "id": self._get_next_id(),
        "method": method,
        "params": params
    }
```

---

## DESCUBRIMIENTO DINÁMICO DE HERRAMIENTAS

### ¿Por Qué Dinámico?

En lugar de hardcodear nombres de herramientas, la aplicación **descubre automáticamente** qué herramientas están disponibles.

**Ventajas:**
- Si Microsoft cambia nombres de herramientas, la app sigue funcionando
- Menor acoplamiento al servidor MCP
- Mayor robustez ante cambios futuros
- Facilita debugging

### Proceso Real

```python
# src/mcp_client.py - línea 108-138
async def discover_tools(self) -> List[Dict]:
    """Discover available tools via tools/list."""
    # Calcula request JSON-RPC con method="tools/list"
    # Envía POST al servidor MCP
    # Parsea respuesta
    # Cachea resultado para no repetir llamadas
    # Retorna lista de herramientas
```

### Ejemplo de Herramientas Descubiertas

Resultado real (estructura aproximada):

```python
[
    {
        "name": "get_recent_m365_roadmaps",
        "description": "Get recent M365 roadmap items with pagination",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Number of items to skip"}
            }
        }
    },
    {
        "name": "get_m365_roadmap_by_id",
        "description": "Get full details of a specific roadmap item",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Item ID"}
            }
        }
    }
]
```

### Uso en el Código

```python
# src/mcp_client.py - línea 140-162
async def get_recent_roadmaps(self, skip: int = 0) -> Dict:
    """Get recent M365 roadmap items with pagination."""
    # Descubre herramientas disponibles
    tools = await self.discover_tools()
    tool_names = [t.get("name") for t in tools]
    
    # Elige la herramienta disponible
    if "get_recent_m365_roadmaps" in tool_names:
        tool_name = "get_recent_m365_roadmaps"
    elif "get_recent_roadmaps" in tool_names:
        tool_name = "get_recent_roadmaps"
    else:
        return {"error": "Tool not found", "items": []}
    
    # Llama a la herramienta
    result = await self._call_tool(tool_name, {"skip": skip})
    return result
```

**Resultado:** Si Microsoft cambia el nombre, el código automáticamente usa el nuevo nombre disponible.

---

## OBTENCIÓN DE ROADMAPS

### Flujo Paso a Paso

#### PASO 1: Conexión al MCP

```python
# src/main_workflow_new.py - línea 48-58
mcp_client = MCPClient()
tools = await mcp_client.discover_tools()

if not tools:
    logger.error("Failed to discover MCP tools")
    return 1
```

#### PASO 2: Fetch Paginado

Microsoft roadmap puede tener cientos o miles de elementos. Para eficiencia, se devuelven en **páginas de 50 elementos**.

```python
# src/main_workflow_new.py - línea 60-86
all_items = []
page = 0
has_more = True

while has_more and page < 50:  # Seguridad: máximo 50 páginas = 2500 items
    result = await mcp_client.get_recent_roadmaps(skip=page * 50)
    
    items = result.get("items", [])
    all_items.extend(items)
    has_more = result.get("hasMore", False)
    
    if page % 5 == 0:
        logger.info(f"Page {page + 1}: {len(items)} items (total: {len(all_items)})")
    
    page += 1
    await asyncio.sleep(0.1)  # Rate limiting
```

**Ejemplo real de ejecución:**
```
Página 1: 50 items (total: 50)
Página 2: 50 items (total: 100)
Página 3: 50 items (total: 150)
...
Página 8: 23 items (total: 373) - hasMore=false
```

#### PASO 3: Estructura de Datos Recibida

Cada elemento contiene:

```python
{
    "id": "a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p",
    "title": "New Teams functionality for better collaboration",
    "description": "Teams is getting new features for...",
    "created": "2026-09-10T14:32:00Z",
    "modified": "2026-09-15T09:15:00Z",
    "status": "In development",
    "products": ["Microsoft Teams"],
    "platforms": ["Web", "Desktop"],
    "cloudInstances": ["WWW", "GCC", "DoD"],
    "generalAvailabilityDate": "2026-Q4",
    "previewAvailabilityDate": "2026-10-15",
    "moreInfoUrls": ["https://microsoft.com/..."]
}
```

---

## FILTRADO DE DATOS

### Visión General

No todos los elementos de roadmap son relevantes. El filtrado usa dos criterios:

```
Elementos totales (370)
        │
        ▼
Filtro 1: FECHA (últimos 30 días)
        │
        ▼
Elementos recientes (120)
        │
        ▼
Filtro 2: PRODUCTO (4 específicos)
        │
        ▼
Elementos relevantes (28)
        │
        ▼
A procesamiento
```

### Implementación

```python
# src/main_workflow_new.py

# FILTRO TEMPORAL
date_filtered, date_info = DataProcessor.filter_by_date(
    all_items,
    months_back=config.RSS_MONTHS_BACK  # Default: 1 mes = 30 días
)

logger.info(f"After date filter: {date_info['items_after']} items")

# FILTRO POR PRODUCTOS
product_filtered, product_info = DataProcessor.filter_by_products(date_filtered)

logger.info(f"After product filter: {product_info['items_after']} items")
```

---

## FILTRO TEMPORAL

### Lógica

Se conservan únicamente elementos creados o modificados en los **últimos 30 días** (configurable).

```python
# src/data_processor.py - línea 44-83
@staticmethod
def filter_by_date(items: List[Dict], months_back: int = 1) -> Tuple[List[Dict], Dict]:
    """Filter items by date (last X months)."""
    
    # Calcula fecha límite: ahora - (30 * months_back) días
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * months_back)
    
    filtered_items = []
    date_field_usage = {"created": 0, "modified": 0, "no_date": 0}
    
    for item in items:
        # Prefiere 'created', si no existe usa 'modified'
        date_str = item.get("created") or item.get("modified")
        
        if not date_str:
            continue  # Ignora elementos sin fecha
        
        try:
            # Parsea ISO 8601: "2026-09-15T14:32:00Z"
            item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            
            # Compara con fecha límite
            if item_date >= cutoff_date:
                filtered_items.append(item)
        except Exception as e:
            logger.warning(f"Failed to parse date for item {item_id}: {e}")
    
    return filtered_items, {
        "cutoff_date": cutoff_date.isoformat(),
        "items_before": len(items),
        "items_after": len(filtered_items),
        "date_field_usage": date_field_usage
    }
```

### Configuración

```env
# .env
RSS_MONTHS_BACK=1  # Últimos 30 días (1 mes)
```

Cambiar a `RSS_MONTHS_BACK=3` incluiría últimos 90 días.

### Ejemplo de Aplicación

Hoy: 2026-09-16

Fecha límite (RSS_MONTHS_BACK=1): 2026-08-17

- ✅ Elemento creado: 2026-09-15 → INCLUIDO
- ✅ Elemento creado: 2026-08-20 → INCLUIDO
- ❌ Elemento creado: 2026-08-10 → DESCARTADO
- ❌ Elemento creado: 2026-07-20 → DESCARTADO

---

## SQLITE Y DEDUPLICACIÓN

### ¿Por Qué SQLite?

SQLite es una base de datos **embebida** que no requiere servidor separado. Funciona como un archivo local (`data/processed_items.db`).

**Ventajas:**
- Sin dependencias de servidores externos
- Rápida y eficiente
- Portable (funciona en Windows/Linux/Mac)
- Confiable (transacciones ACID)
- Fácil de respaldar (es solo un archivo)

### Problema que Resuelve

Si ejecutamos la app dos veces en el mismo mes, sin SQLite enviaríamos el mismo elemento dos veces.

```
Ejecución 1 (2026-09-01):
MCP → Elemento "New Teams Feature"
SQLite → ¿Existe? NO → Procesa y marca como email_sent
↓
Email enviado ✓

Ejecución 2 (2026-09-15):
MCP → Elemento "New Teams Feature" (nuevamente)
SQLite → ¿Existe? SÍ → Salta elemento
↓
Evita envío duplicado ✓
```

### Consulta Básica

```python
# src/database.py - línea 49-66
def item_exists(self, guid: str) -> bool:
    """Check if item has been processed."""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_items WHERE guid = ?", (guid,))
        return cursor.fetchone() is not None
```

---

## TABLA PROCESSED_ITEMS

### Esquema Real

```python
# src/database.py - línea 30-42
CREATE TABLE IF NOT EXISTS processed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- PK único auto-increment
    guid TEXT UNIQUE NOT NULL,                -- ID de roadmap (único)
    url TEXT,                                 -- URL del elemento
    title TEXT,                               -- Título del elemento
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Cuándo se procesó
    included_in_report BOOLEAN DEFAULT 0,    -- ¿Se incluyó en informe?
    filter_reason TEXT,                       -- Motivo si fue descartado
    gemini_processed BOOLEAN DEFAULT 0,       -- Legacy (no usado)
    email_sent BOOLEAN DEFAULT 0              -- ¿Se envió por email?
)
```

### Ejemplo de Datos

```sql
-- Elemento procesado e incluido, email enviado
id=1, guid=a1b2c3d4, title="Teams Feature", 
processed_at=2026-09-01, included_in_report=1, 
email_sent=1

-- Elemento procesado pero descartado (fecha anterior)
id=2, guid=x9y8z7w6, title="Exchange Change",
processed_at=2026-09-16, included_in_report=0,
filter_reason="Date filter: created 2026-07-01"
email_sent=0

-- Elemento procesado en DRY_RUN (sin marcar email_sent)
id=3, guid=p1q2r3s4, title="SharePoint Update",
processed_at=2026-09-16, included_in_report=1,
email_sent=0  -- ← DRY_RUN no marca como enviado
```

### Métodos Principales

```python
# Verificar si existe
if db.item_exists(item_id):
    logger.debug("Item already processed")
    continue

# Agregar nuevo
db.add_item(
    guid=item_id,
    url=item_url,
    title=item_title,
    included=True
)

# Marcar como enviado
db.mark_email_sent(item_id)

# Estadísticas
stats = db.get_stats()
# Retorna: {"total": X, "included": Y, "filtered": Z, "email_sent": W}
```

---

## RESET DE BASE DE DATOS

### Propósito

Herramienta para limpiar SQLite cuando necesitas probar desde cero, sin afectar el esquema de la base de datos.

### Uso

```bash
# Modo interactivo (con confirmaciones)
python reset_database.py

# Modo automático (sin prompts)
python reset_database.py --yes
```

### Lo que Hace

1. **Crea backup** - `data/backups/processed_items_YYYYMMDD_HHMMSS.db`
2. **Verifica schema** - comprueba que la estructura es correcta
3. **Borra registros** - `DELETE FROM processed_items` (no toca schema)
4. **Verifica schema nuevamente** - asegura que nada se rompió
5. **Resumen final** - muestra estadísticas

### Implementación

```python
# reset_database.py - línea 85-131
class DatabaseReset:
    
    def create_backup(self) -> bool:
        """Create backup of current database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"processed_items_{timestamp}.db"
        self.backup_path = self.backup_dir / backup_name
        shutil.copy2(self.db_path, self.backup_path)
        return True
    
    def reset_database(self) -> bool:
        """Clear all records from processed_items table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM processed_items")
            conn.commit()
        return True
    
    def verify_schema_unchanged(self, original_schema: dict) -> bool:
        """Verify database schema is unchanged after reset."""
        # Compara tablas, columnas e índices
        # Retorna True si todo es idéntico
        ...
```

### Seguridad

- Siempre crea backup antes de borrar
- Verifica confirmación (a menos que se use `--yes`)
- Detecta si `DRY_RUN=false` y advierte
- Valida que el schema siga intacto

---

## DRY_RUN MODE

### Concepto

**DRY_RUN = Ensayo sin consecuencias**

Cuando `DRY_RUN=true`, la aplicación ejecuta TODO el proceso EXCEPTO:
- NO envía email
- NO marca elementos como `email_sent` en SQLite

### Configuración

```env
# .env
DRY_RUN=true   # Modo ensayo
DRY_RUN=false  # Modo producción (por defecto)
```

### Flujo en Modo DRY_RUN

```python
# src/main_workflow_new.py - línea 173-220

# PASOS QUE SE EJECUTAN IGUAL:
# 1. Conecta a MCP ✓
# 2. Descarga elementos ✓
# 3. Filtra por fecha ✓
# 4. Filtra por producto ✓
# 5. Verifica SQLite (¿existe?) ✓
# 6. Obtiene detalles completos ✓
# 7. Procesa elementos ✓
# 8. Genera HTML ✓
# 9. Guarda preview en output/roadmap_preview.html ✓

# PASO QUE SE SALTA:
# 10. Envío de email ✗

# VERIFICACIÓN AL FINAL:
# - Logs muestran "DRY_RUN: Email would be sent to recipient@empresa.com"
# - Archivo HTML creado ✓
# - SQLite SIN cambios (elementos NO marcados como email_sent) ✓
```

### Código Real

```python
# src/email_sender.py - línea 154-159
if config.DRY_RUN:
    logger.info(f"DRY_RUN: Email would be sent to {config.EMAIL_TO}")
    logger.debug(f"Email subject: {config.EMAIL_SUBJECT}")
    logger.debug(f"Email body length: {len(email_body)} bytes")
    return True  # Retorna éxito sin enviar

# Si no es DRY_RUN:
sender = SMTPEmailSender()
return await sender.send(to_address=config.EMAIL_TO, ...)
```

### Procedimiento de Prueba Típico

```bash
# 1. Activar venv
.\venv\Scripts\Activate.ps1

# 2. Modificar .env
# DRY_RUN=true

# 3. Ejecutar
python main.py

# 4. Resultados esperados:
# - Logs finalizan sin errores
# - output/roadmap_preview.html existe y contiene HTML válido
# - SQLite SIN cambios en email_sent
# - NO se envió email
```

### Output Esperado

```
[INFO] M365 Roadmap Automation Started (MRC MCP)
[INFO] Connecting to MRC MCP Server
[INFO] Fetching roadmaps from MCP (paginated)
[INFO] Total items fetched: 370 from 8 pages
[INFO] After date filter: 120 items
[INFO] After product filter: 28 items
[INFO] New items: 8 (already processed: 20)
[INFO] Generating HTML email
[INFO] HTML preview saved to: C:\Users\...\output\roadmap_preview.html
[INFO] Sending email
[INFO] DRY_RUN: Email would be sent to recipient@empresa.com
[INFO] M365 Roadmap Automation Completed Successfully
[INFO] HTML Preview:
[INFO]   File: C:\...\output\roadmap_preview.html
[INFO]   Size: 45230 bytes
[INFO] DRY_RUN MODE: Email was NOT sent
[INFO] Items were NOT marked as email_sent in SQLite
```

---

## GENERACIÓN DEL HTML

### Proceso

El HTML se genera en dos fases:

**Fase 1:** Contenido principal (items)
```python
# src/html_generator.py
html_content = HTMLGenerator.generate_html(processed_items)
```

**Fase 2:** Wrapper completo para email + preview
```python
# src/main_workflow_new.py - línea 187-216
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)
preview_file = output_dir / "roadmap_preview.html"

with open(preview_file, "w", encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microsoft 365 Roadmap Update - Preview</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif;">
    <div style="max-width: 900px; margin: 0 auto;">
        <div style="background-color: #f3f3f3; padding: 20px; text-align: center; border-bottom: 3px solid #0078d4;">
            <h1 style="color: #0078d4; margin: 0; font-size: 28px;">Microsoft 365 Roadmap Update</h1>
            <p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">Preview - {len(processed_items)} Items</p>
            <p style="color: #999; margin: 5px 0 0 0; font-size: 12px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div style="padding: 20px;">
            {html_content}
        </div>
    </div>
</body>
</html>""")
```

### Archivo Generado

```
output/roadmap_preview.html
```

Contiene HTML completo con:
- DOCTYPE y head
- Meta tags (charset, viewport)
- Body con estilos inline
- Contenido de elementos
- Metadata (fecha generación, cantidad de items)

---

## ESTRUCTURA DEL INFORME

### Componentes Principales

El HTML generado contiene:

```html
<div class="container">
    
    <div class="header">
        <!-- Encabezado con gradiente y título -->
        <h1>Roadmap Microsoft 365</h1>
    </div>
    
    <div class="content">
        <div class="items-container">
            <!-- Tarjetas de elementos -->
        </div>
    </div>
    
</div>
```

### Tarjeta de Elemento (Item Card)

Cada elemento del roadmap se muestra como una tarjeta con:

```python
# src/data_processor.py - línea 115-139
{
    "id": "unique-id",
    "title": "Feature Title",
    "description": "Detailed description...",
    "products": ["Microsoft Teams", "SharePoint"],
    "status": "In development",
    "status_es": "En desarrollo",
    "platforms": ["Web", "Desktop"],
    "platforms_formatted": "Web, Desktop",
    "cloud_instances": ["WWW", "GCC"],
    "cloud_formatted": "WWW, GCC",
    "ga_date": "2026-Q4",
    "ga_date_formatted": "October 2026",  # Formateado
    "preview_date": "2026-10-15",
    "preview_date_formatted": "October 2026",
    "created": "2026-09-10T14:32:00Z",
    "modified": "2026-09-15T09:15:00Z",
    "more_info_urls": ["https://..."],
    "strategic_value": {
        "level": "HIGH",  # HIGH, MEDIUM, INFORMATIVE
        "score": 4,
        "reasoning": ["Feature affects critical product: Microsoft Teams"],
        "note": "Assessed using deterministic rules (no AI)"
    }
}
```

### Ejemplo Visual HTML

```html
<div class="item-card">
    <div class="item-title">New Teams Collaboration Features</div>
    
    <div class="item-meta">
        <span class="badge status-high">En desarrollo</span>
        <span class="badge">Microsoft Teams</span>
        <span class="badge">Web, Desktop</span>
    </div>
    
    <p class="item-description">
        New collaboration features in Teams including improved file sharing...
    </p>
    
    <div class="item-metadata">
        <div class="meta-item">
            <strong>Available:</strong> October 2026
        </div>
        <div class="meta-item">
            <strong>Platforms:</strong> Web, Desktop
        </div>
    </div>
    
    <div class="strategic-value">
        <strong>Strategic Value:</strong> HIGH
        <p>Feature affects critical product: Microsoft Teams</p>
    </div>
    
    <div class="item-footer">
        <a href="https://...">More information</a>
    </div>
</div>
```

---

## EMAIL Y ENVÍO

### Arquitectura Abstracta de Envío

La aplicación implementa un patrón de abstracción para soportar múltiples mecanismos de envío:

```python
# src/email_factory.py
# Factory pattern para seleccionar sender según configuración

def create_email_sender():
    if config.DRY_RUN or config.EMAIL_MODE == "none":
        return NoOpEmailSender()
    elif config.EMAIL_MODE == "smtp":
        return SMTPEmailSender(config)
    elif config.EMAIL_MODE == "graph":
        return GraphEmailSender(OAuthManager(config))
```

### Matriz de Modos de Envío

| Modo | Archivo | Descripción | Uso |
|------|---------|-------------|-----|
| **none** | `no_op_email_sender.py` | Sin envío (testing) | DRY_RUN=true |
| **smtp** | `email_sender.py` | SMTP genérico | Office 365, Exchange, relay |
| **graph** | `graph_sender.py` | Microsoft Graph OAuth 2.0 | Azure/Entra ID |

### 1. NoOp Sender (Testing)

```python
# src/no_op_email_sender.py
class NoOpEmailSender:
    async def send(self, to_address: str, subject: str, body_html: str) -> bool:
        logger.info(f"[NoOp] Email would be sent to {to_address}")
        return True  # Simula éxito sin enviar
```

Usado cuando:
- `DRY_RUN=true` (ignora EMAIL_MODE)
- `EMAIL_MODE=none` + `DRY_RUN=false`

Comportamiento:
- ✅ Registra en logs
- ❌ No conecta a servidor
- ❌ No marca SQLite
- No valida credenciales

### 2. SMTP Sender (Flexible)

Soporta:
- **Office 365 autenticado** (puerto 587, STARTTLS)
- **Exchange relay** (puerto 25, sin auth)
- **Servidores genéricos** SMTP

```python
# src/email_sender.py
class SMTPEmailSender:
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        from_address: str,
        username: Optional[str],    # ← Opcional
        password: Optional[str],    # ← Opcional
        use_tls: bool,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send(self, to_address: str, subject: str, body_html: str) -> bool:
        # Conecta, autentica (si credenciales), envía, cierra
```

Configuración:

```env
EMAIL_MODE=smtp
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=user@empresa.com  # ← Opcional
SMTP_PASSWORD=password          # ← Opcional
```

Casos de uso:

| Caso | SMTP_HOST | Puerto | TLS | Auth |
|------|-----------|--------|-----|------|
| Office 365 | smtp.office365.com | 587 | Sí | Sí |
| Exchange relay | mail.empresa.local | 25 | No | No |
| Gmail | smtp.gmail.com | 587 | Sí | Sí |

### 3. Graph Sender (OAuth 2.0)

```python
# src/graph_sender.py
class GraphEmailSender:
    def __init__(self, oauth_manager: OAuthManager):
        self.oauth_manager = oauth_manager
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"

    async def send(self, to_address: str, subject: str, html_body: str) -> bool:
        token = self.oauth_manager.get_token()
        # POST https://graph.microsoft.com/v1.0/me/sendMail
        # Retorna True si 202 (Accepted)
```

Configuración:

```env
EMAIL_MODE=graph
AZURE_TENANT_ID=xxxxxxxx-...
AZURE_CLIENT_ID=yyyyyyyy-...
OAUTH_REDIRECT_URI=http://localhost
```

Autenticación:
1. Primera ejecución: abre navegador para login (interactive)
2. Token se cachea en `~/.m365_roadmap/token_cache.json`
3. Siguientes ejecuciones: reutiliza token (silent mode)
4. Si expira: renovación automática

Ver `CONFIGURACION_EMAIL_M365.md` para instrucciones completas de Azure/Entra ID.

### Validación Condicional de Configuración

La validación depende de `DRY_RUN` y `EMAIL_MODE`:

```python
# src/config.py
def _validate_env_vars(self) -> None:
    # Si DRY_RUN=true → Sin validación email
    if self.DRY_RUN:
        logger.debug("DRY_RUN=true: skipping email validation")
        return
    
    # Si DRY_RUN=false → Validar según EMAIL_MODE
    if self.EMAIL_MODE == "none":
        # Solo valida EMAIL_FROM, EMAIL_TO
        pass
    elif self.EMAIL_MODE == "smtp":
        # Valida: SMTP_HOST (obligatorio)
        self._validate_smtp_config()
    elif self.EMAIL_MODE == "graph":
        # Valida: AZURE_TENANT_ID, AZURE_CLIENT_ID
        self._validate_graph_config()
```

Matriz de validación:

| Variable | DRY_RUN | none | smtp | graph |
|----------|---------|------|------|-------|
| EMAIL_FROM | ❌ | ✅ | ✅ | ✅ |
| EMAIL_TO | ❌ | ✅ | ✅ | ✅ |
| SMTP_HOST | ❌ | ❌ | ✅ | ❌ |
| SMTP_USERNAME | ❌ | ❌ | ⭕ | ❌ |
| SMTP_PASSWORD | ❌ | ❌ | ⭕ | ❌ |
| AZURE_TENANT_ID | ❌ | ❌ | ❌ | ✅ |
| AZURE_CLIENT_ID | ❌ | ❌ | ❌ | ✅ |

Leyenda: ✅=Obligatoria, ⭕=Opcional, ❌=No necesaria


## CONFIGURACIÓN

### Sistema de Configuración

La aplicación usa un sistema centralizado con validación condicional:

```python
# src/config.py
class Config:
    """Application configuration with conditional validation."""
    
    def __init__(self):
        env_path = self._find_env_file()
        load_dotenv(dotenv_path=env_path)
        self._load_env_vars()
        self._validate_env_vars()  # ← Depende de DRY_RUN y EMAIL_MODE
```

### Variables Principales de Entorno (.env)

#### Ejecución y Modo Email

```env
# Dry run mode
DRY_RUN=false               # true para no enviar emails

# Email mode selector
EMAIL_MODE=none             # none, smtp, o graph
```

#### Email Común (todos los modos)

```env
EMAIL_FROM=your.email@empresa.com
EMAIL_TO=recipient@empresa.com
```

#### SMTP (si EMAIL_MODE=smtp)

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your.email@empresa.com    # Opcional para relay
SMTP_PASSWORD=your_app_password         # Opcional para relay
```

#### Graph/OAuth (si EMAIL_MODE=graph)

```env
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OAUTH_REDIRECT_URI=http://localhost
```

#### Opcionales

```env
# Roadmap filtering
RSS_MONTHS_BACK=1           # Default: 1 mes = 30 días

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR (default: INFO)
```

### Validación Dinámica

```python
# src/config.py - _validate_env_vars()

def _validate_env_vars(self) -> None:
    # 1. Valida EMAIL_MODE es válido
    if self.EMAIL_MODE not in {"none", "smtp", "graph"}:
        raise ConfigError(f"Invalid EMAIL_MODE: {self.EMAIL_MODE}")
    
    # 2. Si DRY_RUN=true → Sin validación email
    if self.DRY_RUN:
        logger.debug("DRY_RUN=true: skipping email validation")
        return
    
    # 3. Si DRY_RUN=false → Valida según EMAIL_MODE
    # Valida EMAIL_FROM, EMAIL_TO (común a todos)
    # Luego valida mode-específicas
    
    if self.EMAIL_MODE == "smtp":
        self._validate_smtp_config()
    elif self.EMAIL_MODE == "graph":
        self._validate_graph_config()
```

**IMPORTANTE:** Con `DRY_RUN=true` NO se exigen credenciales de correo.

### Constantes de Configuración (hardcoded)

```python
# src/config.py

# MRC MCP
MCP_ENDPOINT = "https://www.microsoft.com/releasecommunications/mcp"
MCP_TIMEOUT = 30

# Productos permitidos
ALLOWED_PRODUCTS = {
    "Exchange Online",
    "Microsoft Teams",
    "SharePoint",
    "OneDrive",
}

# Email
EMAIL_SUBJECT = "Roadmap Microsoft 365 - Actualización Mensual"

# Directorios
DB_PATH = Path("data/processed_items.db")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"

# HTTP
HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
HTTP_BACKOFF_FACTOR = 1.5
```

### Ejemplo de Configuraciones Completas

**Desarrollo (sin email):**
```env
DRY_RUN=true
EMAIL_MODE=none
```

**SMTP Office 365:**
```env
DRY_RUN=false
EMAIL_MODE=smtp
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=team@empresa.com
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=roadmap@empresa.com
SMTP_PASSWORD=AbCd!234XyZw567*aBcD
```

**SMTP Relay (sin auth):**
```env
DRY_RUN=false
EMAIL_MODE=smtp
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=team@empresa.com
SMTP_HOST=mail.empresa.local
SMTP_PORT=25
SMTP_USE_TLS=false
```

**Graph (OAuth):**
```env
DRY_RUN=false
EMAIL_MODE=graph
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=team@empresa.com
AZURE_TENANT_ID=12345678-...
AZURE_CLIENT_ID=87654321-...
```

---

## LOGGING

### Sistema de Logging

Cada operación se registra para auditoría y debugging.

```python
# src/logger.py
logger.info("Message")      # Información general
logger.debug("Message")     # Detalles para debugging
logger.warning("Message")   # Advertencias
logger.error("Message")     # Errores
```

### Archivo de Log

```
logs/app.log
```

Contiene toda la actividad de la aplicación con timestamps y niveles.

### Configuración de Nivel

```env
# .env
LOG_LEVEL=INFO   # Estándar (recomendado)
LOG_LEVEL=DEBUG  # Muy detallado (para troubleshooting)
LOG_LEVEL=WARNING  # Solo advertencias y errores
LOG_LEVEL=ERROR  # Solo errores
```

### Ejemplo de Logs

```
2026-09-16 14:32:00,123 - INFO - M365 Roadmap Automation Started (MRC MCP)
2026-09-16 14:32:01,456 - INFO - STEP 1: Connecting to MRC MCP Server
2026-09-16 14:32:02,789 - INFO - Discovered 2 MCP tools
2026-09-16 14:32:03,012 - INFO - STEP 2: Fetching roadmaps from MCP (paginated)
2026-09-16 14:32:05,345 - INFO - Page 1: 50 items (total: 50)
2026-09-16 14:32:07,678 - INFO - Page 2: 50 items (total: 100)
2026-09-16 14:32:09,901 - INFO - Total items fetched: 370 from 8 pages
2026-09-16 14:32:10,234 - INFO - STEP 3: Filtering by date (last 30 days)
2026-09-16 14:32:10,567 - INFO - After date filter: 120 items
2026-09-16 14:32:11,890 - INFO - STEP 4: Filtering by products
2026-09-16 14:32:12,123 - INFO - After product filter: 28 items
2026-09-16 14:32:12,456 - INFO - STEP 5: Checking for new items
2026-09-16 14:32:13,789 - INFO - New items: 8 (already processed: 20)
2026-09-16 14:32:14,012 - INFO - STEP 6: Fetching full details from MCP
2026-09-16 14:32:20,345 - INFO - Fetched full details for 8 items
2026-09-16 14:32:21,678 - INFO - STEP 7: Processing items (deterministic, no AI)
2026-09-16 14:32:22,901 - INFO - Processed 8 items
2026-09-16 14:32:23,234 - INFO - STEP 8: Generating HTML email
2026-09-16 14:32:23,567 - DEBUG - HTML generated (45230 bytes)
2026-09-16 14:32:23,890 - INFO - HTML preview saved to: C:\...\output\roadmap_preview.html
2026-09-16 14:32:24,123 - INFO - Saving items to database
2026-09-16 14:32:24,456 - INFO - STEP 9: Sending email
2026-09-16 14:32:24,789 - INFO - DRY_RUN: Email would be sent to recipient@empresa.com
2026-09-16 14:32:24,901 - INFO - M365 Roadmap Automation Completed Successfully
2026-09-16 14:32:25,234 - INFO - Elapsed time: 25.12s
2026-09-16 14:32:25,567 - INFO - Database statistics (last 30 days):
2026-09-16 14:32:25,890 - INFO - Total processed: 150
2026-09-16 14:32:26,123 - INFO - Included in reports: 120
2026-09-16 14:32:26,456 - INFO - Filtered out: 30
2026-09-16 14:32:26,789 - INFO - Email sent: 45
```

### Ver Logs en Tiempo Real

```powershell
# Windows PowerShell
Get-Content logs/app.log -Tail 50 -Wait

# Linux/Mac
tail -f logs/app.log
```

---

## MANEJO DE ERRORES

### Problemas Comunes y Recuperación

| Problema | Síntomas | Qué Hace la App |
|----------|----------|-----------------|
| MCP no responde | `Failed to connect to MCP` | Registra error, retorna exit code 1 |
| No hay resultados | `No items fetched from MCP` | Registra advertencia, retorna exit code 1 |
| Error HTTP | `HTTP 500` en MCP | Registra error, intenta nuevamente (HTTP_RETRIES=3) |
| SQLite corrupto | `Database error` | Registra error, detiene ejecución |
| HTML falla | `Failed to save HTML preview` | Registra advertencia, continúa (no es crítico) |
| Email falla | `SMTP error` | Registra error, retorna false |
| Timeout | `MCP request timeout after 30s` | Registra error, reintentar según configuración |

### Mecanismo de Retry

```python
# src/config.py - línea 115-116
HTTP_RETRIES = 3
HTTP_BACKOFF_FACTOR = 1.5
```

Si una petición HTTP falla:
- Intento 1: Espera 1.5s
- Intento 2: Espera 2.25s (1.5 * 1.5)
- Intento 3: Espera 3.375s
- Si sigue fallando: Retorna error

### Ejemplo de Recuperación

```python
# Pseudocódigo del patrón de retry
for attempt in range(1, HTTP_RETRIES + 1):
    try:
        result = await call_mcp()
        return result
    except Exception as e:
        if attempt < HTTP_RETRIES:
            wait_time = HTTP_BACKOFF_FACTOR ** attempt
            await asyncio.sleep(wait_time)
        else:
            raise
```

---

## TESTS

### Framework y Ubicación

```bash
# Tests unitarios
tests/test_filter.py
tests/test_reset_database.py

# Ejecutar tests
python -m pytest tests/ -v
```

### Tipos de Tests

#### Tests de Filtrado (`tests/test_filter.py`)

Verifica que los filtros funcionen correctamente:

```python
def test_filter_by_date():
    """Items are filtered correctly by date range."""
    # Prepara items con diferentes fechas
    # Aplica filtro de fecha
    # Verifica que se incluyen/excluyen correctamente

def test_filter_by_products():
    """Items are filtered correctly by product."""
    # Prepara items con diferentes productos
    # Aplica filtro de producto
    # Verifica que solo quedan los 4 productos objetivo
```

#### Tests de Reset Database (`tests/test_reset_database.py`)

Verifica que reset_database.py sea seguro:

```python
def test_database_reset_clears_records():
    """Database reset successfully clears all records."""

def test_backup_creation():
    """Backup is created before reset."""

def test_schema_unchanged():
    """Database schema remains unchanged after reset."""

def test_no_emails_sent():
    """reset_database.py never imports email modules."""

def test_no_internet_access():
    """reset_database.py doesn't access external services."""
```

### Ejecutar Tests Específicos

```bash
# Un test específico
python -m pytest tests/test_filter.py::test_filter_by_date -v

# Con cobertura
python -m pytest tests/ --cov=src

# Verbose con output
python -m pytest tests/ -vv -s
```

---

## SEGURIDAD

### Protección de Credenciales

**✅ SIEMPRE:**
- Usar variables de entorno (.env)
- Añadir .env a .gitignore
- Usar contraseñas de aplicación (no la normal)
- Usar protocolos seguros (STARTTLS, OAuth)

### .env.example vs .env

```bash
# .env.example (PÚBLICO - seguro compartir)
EMAIL_FROM=your.email@empresa.com
EMAIL_TO=recipient@empresa.com
EMAIL_PASSWORD=your_app_password
DRY_RUN=false

# .env (PRIVADO - en .gitignore)
EMAIL_FROM=juan.diaz@empresa.com
EMAIL_TO=equipo@empresa.com
EMAIL_PASSWORD=mY5uP3r5ecR3tP4ssw0rd!
DRY_RUN=false
```

### .gitignore

```
# .gitignore
.env              # Archivo de configuración privado
*.log             # Logs con información sensible
data/             # SQLite puede contener datos sensibles
.env.local        # Variantes locales
*.pem             # Certificados
```

### Consideraciones de Seguridad

1. **Endpoint MCP es público** - No requiere autenticación
2. **SMTP usa STARTTLS** - Encriptación en tránsito
3. **DRY_RUN previene emails accidentales** - Testeo seguro
4. **Backups de SQLite automáticos** - Recuperación ante errores
5. **Logs no contienen credenciales** - Auditables con seguridad

### Permisos de Archivo

```bash
# En Windows (PowerShell)
# Asegurar que .env solo sea legible por el usuario
icacls ".env" /inheritance:r /grant:r "%USERNAME%:F"

# En Linux/Mac
chmod 600 .env
```

---

## EJECUCIÓN MANUAL

### Pasos

```bash
# 1. Abrir PowerShell/Terminal en directorio del proyecto
cd "C:\Users\...\Documents\Claude\make"

# 2. Activar entorno virtual
.\venv\Scripts\Activate.ps1

# En caso de restricción de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Verificar .env
# - EMAIL_FROM configurado ✓
# - EMAIL_TO configurado ✓
# - EMAIL_PASSWORD configurado ✓
# - DRY_RUN=false si quieres enviar, =true si es prueba

# 4. Ejecutar
python main.py

# 5. Observar logs
Get-Content logs/app.log -Tail 20 -Wait
```

### Output Esperado

```
2026-09-16 15:00:00,000 - INFO - M365 Roadmap Automation Started (MRC MCP)
2026-09-16 15:00:01,000 - INFO - STEP 1: Connecting to MRC MCP Server
...
2026-09-16 15:00:30,000 - INFO - M365 Roadmap Automation Completed Successfully
2026-09-16 15:00:30,000 - INFO - Email sent: 1 (or DRY_RUN if corresponde)
```

### Códigos de Salida

```python
return 0   # Éxito
return 1   # Error (revisar logs)
```

---

## PRUEBA COMPLETA DESDE CERO

### Procedimiento Seguro

```bash
# PASO 1: Preparación
.\venv\Scripts\Activate.ps1

# PASO 2: Configurar DRY_RUN
# Editar .env:
# DRY_RUN=true

# PASO 3: Reset de base de datos
python reset_database.py

# Output:
# RESET DATABASE - TESTING MODE
# Database path: data/processed_items.db
# Current records: 150
# This action will:
#   1. Create a backup of the database
#   2. Delete all processing records
#   3. Keep the database schema unchanged
# Continue with reset? [y/N]: y
# → Crea backup
# → Borra registros
# → Verifica schema
# → Resumen: ✅ RESET COMPLETED SUCCESSFULLY

# PASO 4: Ejecutar aplicación
python main.py

# Output esperado:
# [INFO] Connecting to MRC MCP Server
# [INFO] Total items fetched: 370 from 8 pages
# [INFO] After date filter: 120 items
# [INFO] After product filter: 28 items
# [INFO] New items: 28 (already processed: 0)
# [INFO] HTML preview saved to: C:\...\output\roadmap_preview.html
# [INFO] DRY_RUN: Email would be sent to recipient@empresa.com
# [SUCCESS] M365 Roadmap Automation Completed Successfully

# PASO 5: Verificar HTML
# Abrir archivo: output/roadmap_preview.html en navegador
# Verificar que contiene:
#   ✓ Encabezado "Microsoft 365 Roadmap Update"
#   ✓ 28 elementos (o cantidad según filtro)
#   ✓ Tarjetas con títulos, descripción, estado
#   ✓ Fechas formateadas correctamente

# PASO 6: Verificar SQLite
# Base de datos SIN cambios en email_sent
# Todos los items tienen email_sent=0 (porque DRY_RUN=true)

# PASO 7: Verificar No Email
# Revisar bandeja de entrada/enviados
# Confirmar que NO se recibió email (DRY_RUN)

# PASO 8: Cambiar a producción
# Editar .env:
# DRY_RUN=false

# PASO 9: Reset nuevamente (opcional)
python reset_database.py --yes

# PASO 10: Ejecutar en producción
python main.py

# Resultado:
# [INFO] Sending email to recipient@empresa.com
# [SMTP] Email sent to recipient@empresa.com
# [SUCCESS] M365 Roadmap Automation Completed Successfully

# VERIFICAR: Email recibido ✓
# VERIFICAR: SQLite con email_sent=1 para los elementos ✓
```

---

## EJECUCIÓN AUTOMÁTICA

### Objetivo

Ejecutar la aplicación automáticamente una vez al mes sin intervención manual.

### Windows: Task Scheduler

Ver: `EJECUCION_AUTOMATICA_MENSUAL.md`

Pasos resumidos:

1. Abrir `taskschd.msc` (Task Scheduler)
2. Crear tarea básica
3. Trigger: Mensual, día específico
4. Acción: Ejecutar `python.exe C:\ruta\main.py`
5. Opciones: Ejecutar aunque no esté conectado


### Consideraciones

- Guardar logs en archivo (stdout no se captura)
- Redireccionar stderr
- Usar rutas absolutas
- Activar venv si es necesario

---

## FLUJO COMPLETO

```
┌────────────────────────────────────────────────────────────────┐
│                   EXECUTION FLOW                               │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  START                                                          │
│    │                                                            │
│    ▼                                                            │
│  Load Config (.env)                                            │
│    │                                                            │
│    ▼                                                            │
│  Validate Environment                                          │
│    │                                                            │
│    ├─ EMAIL_FROM exists?                                       │
│    ├─ EMAIL_TO exists?                                         │
│    ├─ EMAIL_PASSWORD exists?                                   │
│    └─ OK → Continue, Fail → EXIT(1)                            │
│    │                                                            │
│    ▼                                                            │
│  Connect to MCP ─────────────────────── HTTP POST              │
│    │                                    tools/list             │
│    ├─ Discover tools                    (JSON-RPC)             │
│    ├─ Get tool names                                           │
│    └─ Cache for reuse                                          │
│    │                                                            │
│    ▼                                                            │
│  Fetch Roadmaps (Paginated) ─────────── HTTP POST              │
│    │                                    tools/call             │
│    ├─ Page 1: GET 50 items              get_recent_...         │
│    ├─ Page 2: GET 50 items              ({skip: 0})            │
│    ├─ ...                               ({skip: 50})           │
│    ├─ Until hasMore=false               ({skip: 100})          │
│    └─ Total: ~370 items                                        │
│    │                                                            │
│    ▼                                                            │
│  Filter by Date                                                │
│    │                                                            │
│    ├─ Cutoff: now - (30 * RSS_MONTHS_BACK)                     │
│    ├─ Prefer 'created', fallback 'modified'                    │
│    ├─ Keep items >= cutoff_date                                │
│    └─ Result: ~120 items                                       │
│    │                                                            │
│    ▼                                                            │
│  Filter by Products                                            │
│    │                                                            │
│    ├─ Target: Exchange, Teams, SharePoint, OneDrive            │
│    ├─ Check each item.products against TARGET_PRODUCTS         │
│    ├─ Keep matches only                                        │
│    └─ Result: ~28 items                                        │
│    │                                                            │
│    ▼                                                            │
│  Check for Duplicates (SQLite)                                 │
│    │                                                            │
│    ├─ For each item: SELECT FROM processed_items WHERE id      │
│    ├─ If found: Mark as "already processed", skip              │
│    ├─ If not found: Mark as "new", add to list                 │
│    └─ Result: ~8 new items                                     │
│    │                                                            │
│    ▼                                                            │
│  Fetch Full Details ─────────────────── HTTP POST              │
│    │                                    tools/call             │
│    ├─ For each new item                 get_roadmap_by_id      │
│    ├─ Call MCP with item.id             ({id: "..."})          │
│    ├─ Wait for full data                                       │
│    └─ Result: Complete information                             │
│    │                                                            │
│    ▼                                                            │
│  Process Deterministically                                     │
│    │                                                            │
│    ├─ Enrich fields (format dates, join arrays)                │
│    ├─ Calculate Strategic Value (rules-based, no AI)           │
│    ├─ Translate status to Spanish                              │
│    └─ Result: Processed items ready for HTML                   │
│    │                                                            │
│    ▼                                                            │
│  Save to SQLite (BEFORE EMAIL)                                 │
│    │                                                            │
│    ├─ INSERT INTO processed_items                              │
│    ├─ Mark: processed_at, included, (email_sent if not DRY)    │
│    └─ Critical: Do this BEFORE sending email                   │
│    │              (guarantees no reprocessing if email fails)   │
│    │                                                            │
│    ▼                                                            │
│  Generate HTML                                                 │
│    │                                                            │
│    ├─ Create item cards                                        │
│    ├─ Apply CSS styles                                         │
│    ├─ Format content                                           │
│    └─ Result: HTML content string                              │
│    │                                                            │
│    ▼                                                            │
│  Save HTML Preview                                             │
│    │                                                            │
│    ├─ Create output/ directory if missing                      │
│    ├─ Write to output/roadmap_preview.html                     │
│    ├─ Wrap content in full HTML document                       │
│    ├─ Add meta tags, doctype, styles                           │
│    └─ Log: "HTML preview saved to: C:\..."                     │
│    │                                                            │
│    ▼                                                            │
│  Decision: DRY_RUN?                                            │
│    │                                                            │
│    ├─ DRY_RUN=true?                                            │
│    │   ├─ Log: "DRY_RUN: Email would be sent to..."            │
│    │   ├─ Skip email sending                                   │
│    │   ├─ Skip marking email_sent in SQLite                    │
│    │   └─ Return: Success (not sent)                           │
│    │                                                            │
│    └─ DRY_RUN=false?                                           │
│        ├─ Continue to email sending                            │
│        ▼                                                        │
│    Send Email via SMTP ─────────────── Conexión TCP            │
│    │                                    EHLO                   │
│    ├─ Connect to smtp.office365.com:587 STARTTLS               │
│    ├─ EHLO, STARTTLS, EHLO (Exchange requirement)              │
│    ├─ LOGIN with EMAIL_FROM, EMAIL_PASSWORD                   │
│    ├─ SEND message                                            │
│    ├─ QUIT connection                                          │
│    └─ Result: Email sent or error                              │
│    │                                                            │
│    ├─ Success? Mark email_sent=1 in SQLite                     │
│    ├─ Failure? Log error, items NOT marked                     │
│    │          (can retry next execution)                       │
│    │                                                            │
│    ▼                                                            │
│  Display Summary                                               │
│    │                                                            │
│    ├─ Elapsed time                                             │
│    ├─ Database statistics (last 30 days)                       │
│    ├─ Total processed, included, filtered, email_sent          │
│    ├─ HTML Preview file path                                   │
│    ├─ DRY_RUN status                                           │
│    │                                                            │
│    ▼                                                            │
│  END (exit code 0)                                             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## EJEMPLO PRÁCTICO

### Scenario: Ejecución Real del 16 de Septiembre 2026

**Configuración:**
```env
DRY_RUN=false
RSS_MONTHS_BACK=1
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=team@empresa.com
```

**Paso 1: MCP devuelve elementos**

Microsoft ha publicado recientemente:

```json
[
  {
    "id": "teams-001",
    "title": "New Teams Meeting Features",
    "created": "2026-09-15T10:00:00Z",
    "products": ["Microsoft Teams"],
    "status": "In rollout"
  },
  {
    "id": "exchange-001", 
    "title": "Exchange Online Performance Improvements",
    "created": "2026-09-01T10:00:00Z",
    "products": ["Exchange Online"],
    "status": "Launched"
  },
  {
    "id": "onedrive-001",
    "title": "OneDrive new sync features",
    "created": "2026-08-10T10:00:00Z",  ← Older, will be filtered
    "products": ["OneDrive"],
    "status": "In development"
  }
]
```

**Paso 2: Filtro de fecha**

Fecha actual: 2026-09-16  
Cutoff (30 días atrás): 2026-08-17

Resultado:
- ✅ teams-001 (created 2026-09-15) - INCLUIDO
- ✅ exchange-001 (created 2026-09-01) - INCLUIDO
- ❌ onedrive-001 (created 2026-08-10) - DESCARTADO (anterior a cutoff)

**Paso 3: Filtro de producto**

TARGET_PRODUCTS = {Exchange, Teams, SharePoint, OneDrive}

Resultado:
- ✅ teams-001 - Microsoft Teams en target
- ✅ exchange-001 - Exchange Online en target
- (onedrive-001 ya fue descartado)

**Paso 4: Verificación de duplicados**

SQLite check:

```sql
SELECT FROM processed_items WHERE guid = 'teams-001'
```

Resultado:
- ✅ teams-001 - NO existe en BD → NUEVO
- ✅ exchange-001 - NO existe en BD → NUEVO

(Hipotéticamente, si hubiera sido procesado antes, saltaría)

**Paso 5: Obtención de detalles**

Para cada nuevo item, se llama a `get_roadmap_by_id`:

```json
{
  "id": "teams-001",
  "title": "New Teams Meeting Features",
  "description": "Enhanced meeting capabilities including...",
  "products": ["Microsoft Teams"],
  "status": "In rollout",
  "platforms": ["Web", "Desktop", "Mobile"],
  "cloudInstances": ["WWW", "GCC"],
  "generalAvailabilityDate": "2026-Q4",
  "previewAvailabilityDate": "2026-10-01",
  "moreInfoUrls": ["https://microsoft.com/teams-roadmap/meeting-features"]
}
```

**Paso 6: Procesamiento**

DataProcessor enriquece:

```python
{
  "title": "New Teams Meeting Features",
  "description": "Enhanced meeting capabilities including...",
  "status": "In rollout",
  "status_es": "En despliegue",  # Traducido
  "ga_date_formatted": "October 2026",  # Formateado
  "platforms_formatted": "Web, Desktop, Mobile",  # Unido
  "strategic_value": {
    "level": "HIGH",  # Teams es producto crítico
    "score": 3,
    "reasoning": ["Feature affects critical product: Microsoft Teams"]
  }
}
```

**Paso 7: HTML generado**

```html
<div class="item-card">
  <div class="item-title">New Teams Meeting Features</div>
  <div class="item-meta">
    <span class="badge status-high">En despliegue</span>
    <span class="badge">Microsoft Teams</span>
  </div>
  <p>Enhanced meeting capabilities including...</p>
  <div class="meta-item">
    <strong>Available:</strong> October 2026
  </div>
  <div class="strategic-value">
    <strong>Strategic Value:</strong> HIGH
    <p>Feature affects critical product: Microsoft Teams</p>
  </div>
</div>
```

**Paso 8: Guardado en SQLite**

```sql
INSERT INTO processed_items
(guid, url, title, included_in_report)
VALUES ('teams-001', 'https://...', 'New Teams Meeting Features', 1)

INSERT INTO processed_items
(guid, url, title, included_in_report)
VALUES ('exchange-001', 'https://...', 'Exchange Online Performance...', 1)
```

**Paso 9: Envío de Email**

Contenido del email:

```
From: roadmap@empresa.com
To: team@empresa.com
Subject: Roadmap Microsoft 365 - Actualización Mensual

[HTML con 2 tarjetas de elementos]
- New Teams Meeting Features (HIGH)
- Exchange Online Performance Improvements (MEDIUM)
```

**Paso 10: Marcado final**

```sql
UPDATE processed_items SET email_sent = 1 
WHERE guid IN ('teams-001', 'exchange-001')
```

**Resultado:**

Email enviado ✓  
SQLite actualizado ✓  
Logs registran éxito ✓

---

## ¿QUÉ OCURRE SI ALGO FALLA?

### Matriz de Fallas y Recuperación

| Falla | Síntoma | Ubicación | Acción |
|-------|---------|-----------|--------|
| **MCP no responde** | `Failed to connect to MCP` | mcp_client.py | Registra error, intenta retry según config, luego exit(1) |
| **HTTP Timeout** | `MCP request timeout after 30s` | mcp_client.py:104 | Timeout automático, retry con backoff |
| **Herramienta MCP desaparecida** | `No compatible roadmap tool found` | mcp_client.py:151 | Descubrimiento dinámico busca alternativa |
| **JSON parsing error** | `Failed to parse MCP response` | mcp_client.py:83 | Registra error, retorna {"error": "..."} |
| **Conexión perdida (Internet)** | `httpx.NetworkError` | mcp_client.py:105 | Registra, intenta retry con backoff |
| **No hay resultados** | `No items fetched from MCP` | main_workflow_new.py:89 | Registra warning, retorna exit code 0 |
| **Filtro elimina todo** | `No items matched filter` | main_workflow_new.py:116-118 | Registra info, retorna exit code 0 |
| **SQLite no encontrado** | `Database initialization error` | database.py:45 | Crea nueva DB automáticamente |
| **SQLite corrupto** | `Database query error` | database.py:65 | Registra error, detiene ejecución |
| **No se puede escribir HTML** | `Failed to save HTML preview` | main_workflow_new.py:219 | Registra warning, continúa (no es crítico) |
| **SMTP auth falla** | `SMTP authentication failed` | email_sender.py:126 | Registra error, retorna False |
| **SMTP timeout** | `SMTP request timeout` | email_sender.py:133 | Registra error, retorna False |
| **SMTP connection error** | `Email send error` | email_sender.py:133 | Registra error, retorna False |
| **.env falta variable** | `Missing required environment variables` | config.py:81 | Detiene ejecución con mensaje claro |
| **Permission denied** | Sistema operativo | config.py:122 | Intenta crear directorio, registra si falla |

### Estrategia de Retries

```python
# Configurado en config.py
HTTP_RETRIES = 3          # Máximo 3 intentos
HTTP_TIMEOUT = 30         # Espera máximo 30s por petición
HTTP_BACKOFF_FACTOR = 1.5 # Espera cada vez más (1.5s, 2.25s, 3.375s)
```

### Recuperación Automática

```python
# Pseudo-código de retry automático
for attempt in range(1, HTTP_RETRIES + 1):
    try:
        result = await call_mcp()
        if result.ok:
            return result
    except TimeoutError:
        if attempt < HTTP_RETRIES:
            wait_time = HTTP_BACKOFF_FACTOR ** attempt
            await asyncio.sleep(wait_time)
            continue
        else:
            raise
    except Exception as e:
        logger.error(f"Attempt {attempt}: {e}")
        raise
```

### Puntos de No Retorno

Si estas fallan, la ejecución se detiene inmediatamente:

1. **Config inválida** - exit(1)
2. **SQLite corrompido** - exit(1)
3. **Todas las peticiones MCP fallan** - exit(1)
4. **Email falla después de marcar en SQLite** - Registra pero continúa (ya está en BD)

### Debugging

Establecer `LOG_LEVEL=DEBUG` en .env para ver:

```
[DEBUG] MCP Request ID: 1
[DEBUG] MCP Method: tools/list
[DEBUG] MCP Response: {"result": {"tools": [...]}}
[DEBUG] Tools discovered: get_recent_m365_roadmaps, get_m365_roadmap_by_id
[DEBUG] Calling tool: get_recent_m365_roadmaps with skip=0
[DEBUG] [SMTP] Connected to smtp.office365.com:587
[DEBUG] [SMTP] EHLO sent
[DEBUG] [SMTP] STARTTLS initiated
[DEBUG] [SMTP] Authenticated as roadmap@empresa.com
```

---

## MANTENIMIENTO

### Archivos Seguros de Modificar

**✅ MODIFICABLES:**

- `.env` - Cambiar credenciales, filtros, logging
- `src/config.py` - Líneas 94-99 (ALLOWED_PRODUCTS)
- `src/config.py` - Líneas 91 (RSS_MONTHS_BACK)
- `src/data_processor.py` - Lógica de filtrado y procesamiento
- `src/html_generator.py` - Estilos y formato HTML
- Tests en `tests/`

### Archivos Críticos (Tocar con cuidado)

**⚠️ CRÍTICOS:**

- `src/main_workflow_new.py` - Orquestación principal (cambios = bugs)
- `src/mcp_client.py` - Protocolo MCP (cambios pueden romper comunicación)
- `src/database.py` - Operaciones SQLite (cambios = corrupción)
- `src/email_sender.py` - SMTP/OAuth (cambios = emails fallidos)

### Archivos NUNCA de Modificar Directamente

**❌ NO MODIFICAR:**

- `data/processed_items.db` - Usar `reset_database.py` en su lugar
- `.gitignore` - Protege .env
- `requirements.txt` - Usar `pip install` para añadir paquetes

### ¿Qué hacer si Microsoft cambia MCP?

**Síntoma:** Error "No compatible roadmap tool found"

**Solución:**

```bash
# 1. Verificar herramientas disponibles
# Añadir a main_workflow_new.py línea 56:
logger.info(f"Available tools: {[t.get('name') for t in tools]}")

# 2. Revisar logs y encontrar nuevos nombres
# Ejemplo: "get_recent_roadmaps_v2" en lugar de "get_recent_m365_roadmaps"

# 3. Actualizar mcp_client.py líneas 146-149:
if "get_recent_roadmaps_v2" in tool_names:
    tool_name = "get_recent_roadmaps_v2"

# 4. Similar para get_m365_roadmap_by_id (líneas 169-173)
```

El descubrimiento dinámico hace esto más fácil, pero puede requerir ajustes manuales.

### ¿Qué hacer si Microsoft cambia estructura de datos?

**Síntoma:** HTML vacío o campos faltantes

**Solución:**

```bash
# 1. Ejecutar con LOG_LEVEL=DEBUG
# 2. Revisar estructura real que devuelve MCP
# 3. Actualizar DataProcessor.process_batch() para nuevos campos
# 4. Actualizar HTMLGenerator para mostrar nuevos campos
# 5. Probar con DRY_RUN=true antes de producción
```

### Actualizar Dependencias

```bash
# Ver qué hay de actualizar
pip list --outdated

# Actualizar una librería
pip install --upgrade httpx

# Actualizar todo (CUIDADO)
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Añadir Nuevo Producto al Filtrado

```python
# src/config.py línea 94-99
ALLOWED_PRODUCTS = {
    "Exchange Online",
    "Microsoft Teams",
    "SharePoint",
    "OneDrive",
    "Power BI",  # ← Nuevo
}
```

Luego ejecutar con DRY_RUN=true para probar.

---

## LIMITACIONES ACTUALES

### Funcionales

1. **Un solo email destinatario**
   - Actual: `EMAIL_TO=single@empresa.com`
   - Imposible: Múltiples destinatarios sin modificar código
   - **Solución futura:** Variable de entorno con lista

2. **Cuatro productos fijos**
   - Actual: Exchange, Teams, SharePoint, OneDrive
   - Imposible: Cambiar dinámicamente sin código
   - **Solución futura:** Configuración por usuario

3. **Histórico limitado**
   - Actual: `RSS_MONTHS_BACK=1` (últimos 30 días)
   - Imposible: Queries complejas sobre histórico
   - **Solución futura:** Dashboard web con histórico

4. **Sin notificaciones de error**
   - Actual: Solo logs locales
   - Imposible: Alertas por email si falla
   - **Solución futura:** Alertas automáticas

### Datos y Almacenamiento

1. **SQLite local solo**
   - Datos no se replican
   - No hay backup automático en cloud
   - **Solución:** Hacer backup manual de data/

2. **Información limitada por MCP**
   - No todas las propiedades de roadmap están disponibles
   - **Solución:** Esperar actualizaciones de Microsoft

3. **Sin análisis histórico**
   - BD registra "procesado" pero no cambios
   - Imposible: Ver cómo evolucionó un elemento
   - **Solución futura:** Tabla de histórico

---
