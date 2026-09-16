# Guía de Scripts del Proyecto - M365 Roadmap Automation

**Versión:** 1.0  
**Fecha:** 2026-09-16  
**Última actualización tras limpieza de proyecto**

---

## 📋 Tabla de Contenidos

1. [Funcionamiento Normal de la Aplicación](#funcionamiento-normal-de-la-aplicación)
2. [Herramientas de Configuración](#herramientas-de-configuración)
3. [Herramientas de Diagnóstico](#herramientas-de-diagnóstico)
4. [Herramientas de Validación](#herramientas-de-validación)
5. [Herramientas Manuales Útiles](#herramientas-manuales-útiles)
6. [Tests](#tests)
7. [Referencia Rápida](#referencia-rápida)

---

## FUNCIONAMIENTO NORMAL DE LA APLICACIÓN

### Ejecutar la Aplicación (Uso Normal)

Para ejecutar la aplicación en modo normal y procesar el roadmap:

```bash
python main.py
```

### ¿Qué hace main.py?

1. **Conecta a Microsoft Release Communications MCP Server**
   - Accede a https://www.microsoft.com/releasecommunications/mcp
   - No requiere autenticación adicional

2. **Descarga el roadmap de Microsoft 365**
   - Obtiene todos los items de los últimos 30 días
   - Total aproximado: 1,766 items

3. **Filtra por productos específicos**
   - Exchange Online
   - Microsoft Teams
   - SharePoint
   - OneDrive

4. **Filtra por fecha**
   - Últimos 30 días de cambios

5. **Verifica duplicados en SQLite**
   - Base de datos: `data/processed_items.db`
   - Evita procesar items ya enviados

6. **Procesa determinísticamente (sin IA)**
   - Análisis de valor estratégico
   - Genera texto formateado

7. **Genera HTML profesional**
   - Estructura responsive
   - Optimizado para email
   - Archivos generados (solo si se envía):
     - Email enviado
     - Items marcados como `email_sent=1` en SQLite

8. **Envía email via Microsoft Graph API**
   - Requiere OAuth 2.0 configurado
   - Usa token en cache (`~/.m365_roadmap/token_cache.json`)
   - Envía a la dirección configurada en `EMAIL_TO`

9. **Registra logs**
   - Archivo: `logs/app.log`
   - Contiene: pasos ejecutados, errores, resultados

### Requisitos para Ejecutar

- Python 3.8+
- `.env` configurado con:
  - `OAUTH_CLIENT_ID`
  - `OAUTH_TENANT_ID`
  - `EMAIL_FROM`
  - `EMAIL_TO`
- Token OAuth en cache (del primer login interactivo)
- Conexión a Internet

### DRY_RUN Mode

Si `DRY_RUN=true` en `.env`:

- ✅ Descarga roadmap
- ✅ Filtra items
- ✅ Genera HTML
- ✅ Registra logs
- ❌ **NO envía email**
- ❌ **NO modifica SQLite**

**Propósito:** Probar la lógica sin realizar cambios permanentes.

### Posibles Resultados de Ejecución

#### ✅ ÉXITO

```
PASO 1: Conectar a MRC MCP... ✓
PASO 2: Descargar 1,766 items... ✓
PASO 3: Filtrar por fecha... ✓ (26 items nuevos)
PASO 4: Filtrar por productos... ✓
PASO 5: Deduplicación... ✓ (0 duplicados)
PASO 6: Generar HTML... ✓
PASO 7: Enviar email... ✓
PASO 8: Marcar SQLite... ✓
[EXIT CODE 0]
```

#### ⚠️ SIN ITEMS NUEVOS

```
PASO 1-5: OK
PASO 6: 0 items nuevos encontrados
No se envía email (esperado)
[EXIT CODE 0]
```

#### ❌ ERROR

```
[Error details en logs/app.log]
[EXIT CODE 1]
```

---

## HERRAMIENTAS DE CONFIGURACIÓN

### test_config.py

**¿Para qué sirve?**

Valida que tu archivo `.env` tenga todas las variables de configuración necesarias y que sus valores sean válidos.

**¿Cuándo ejecutarlo?**

- Después de crear/actualizar `.env`
- Antes de ejecutar `main.py` por primera vez
- Si tienes errores de configuración

**¿Qué hace?**

1. Lee archivo `.env`
2. Verifica que existan todas las variables requeridas:
   - `EMAIL_FROM`
   - `EMAIL_TO`
   - `OAUTH_CLIENT_ID` (si usas OAuth)
   - `OAUTH_TENANT_ID` (si usas OAuth)
3. Valida que los valores no estén vacíos
4. Reporta cualquier falta

**¿Modifica datos?**

- ❌ No modifica nada
- ℹ️ Solo lectura de `.env`

**¿Necesario para producción?**

- No es crítico, pero es útil para debug

**Cómo ejecutarlo:**

```bash
python test_config.py
```

**Resultado esperado:**

```
Configuration test PASSED
All required variables are set
```

---

## HERRAMIENTAS DE DIAGNÓSTICO

### test_m365_oauth_diagnosis.py

**¿Para qué sirve?**

Verifica que la autenticación OAuth 2.0 con Microsoft está correctamente configurada y que puedes acceder a Microsoft Graph API.

**¿Cuándo ejecutarlo?**

- **Primera vez:** Antes de la ejecución mensual
  - Abrirá navegador para que hagas login
  - Guardará tokens en cache
- **Problemas de autenticación:** Si `main.py` falla con error 401
- **Después de 90 días:** Si quieres renovar la sesión

**¿Qué hace?**

1. Intenta obtener token del cache (silenciosamente)
2. Si no hay token o está expirado:
   - Abre tu navegador
   - Te pide que inicies sesión
   - Te pide que aceptes permisos ("Mail.Send")
3. Obtiene token de Microsoft
4. Guarda token en: `~/.m365_roadmap/token_cache.json`
5. Verifica que puedes acceder a Microsoft Graph API

**¿Modifica datos?**

- ✅ SÍ modifica:
  - Crea/actualiza: `~/.m365_roadmap/token_cache.json`
- ❌ NO modifica:
  - SQLite
  - .env
  - Archivos del proyecto

**¿Envía emails?**

- ❌ NO

**¿Necesario para producción?**

- SÍ, al menos una vez
- Se ejecuta una sola vez para guardar tokens
- Luego `main.py` reutiliza los tokens

**Cómo ejecutarlo:**

```bash
python test_m365_oauth_diagnosis.py
```

**Resultado esperado:**

```
[OK] Usuario autenticado: usuario@empresa.com
[OK] Tenant: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
[OK] Scopes autorizados: Mail.Send, offline_access
[OK] Conectividad a Microsoft Graph: EXITOSA
```

**Problemas comunes:**

- **"Application with identifier was not found"** → CLIENT_ID incorrecto en `.env`
- **"User or admin has not consented"** → No aceptaste los permisos en el navegador
- **"401 Unauthorized"** → Token expirado después de 90 días, ejecuta este script nuevamente

---

### test_dryrun_sqlite.py

**¿Para qué sirve?**

Verifica que el modo `DRY_RUN=true` en `.env` realmente impide que se modifique la base de datos SQLite.

**¿Cuándo ejecutarlo?**

- Cuando quieras validar que DRY_RUN funciona
- Antes de cambiar `DRY_RUN=false` para producción
- Si tienes dudas sobre si SQLite fue modificado

**¿Qué hace?**

1. Lee el valor de `DRY_RUN` de `.env`
2. Intenta agregar un item de prueba a SQLite
3. Verifica si realmente se modificó o si fue ignorado

**¿Modifica datos?**

- Depende de `DRY_RUN`:
  - Si `DRY_RUN=true` → ❌ NO modifica
  - Si `DRY_RUN=false` → ✅ SÍ modifica (agrega item de prueba)

**¿Envía emails?**

- ❌ NO

**¿Necesario para producción?**

- No es crítico
- Útil para debugging

**Cómo ejecutarlo:**

```bash
python test_dryrun_sqlite.py
```

**Resultado esperado (con DRY_RUN=true):**

```
DRY_RUN Setting: True
Database: data/processed_items.db
Testing: Item NOT added to database (DRY_RUN=true, as expected)
✓ Test PASSED
```

---

## HERRAMIENTAS DE VALIDACIÓN

### setup.bat (Windows)

**¿Para qué sirve?**

Automatiza la configuración inicial del proyecto:

1. Verifica que Python está instalado
2. Crea entorno virtual (`venv`)
3. Instala dependencias (`requirements.txt`)
4. Copia `.env.example` a `.env`
5. Valida la configuración

**¿Cuándo ejecutarlo?**

- Primera vez que instalas el proyecto
- Cuando reinstales el proyecto

**Cómo ejecutarlo:**

```bash
setup.bat
```

**¿Modifica datos?**

- ✅ Crea `venv/`
- ✅ Crea/actualiza `.env` (si no existe)
- ✅ Instala dependencias

---

## HERRAMIENTAS MANUALES ÚTILES

### reset_database.py

**¿Para qué sirve?**

Reinicia la base de datos SQLite eliminando el historial de procesamiento. Útil para:
- Pruebas completas desde cero
- Verificar que el workflow funciona correctamente
- Debug de deduplicación
- Validar procesamiento sin historial

**¿Cuándo ejecutarlo?**

- **ANTES de una prueba completa** desde cero
- **NO antes de ejecuciones normales** (elimina el historial de deduplicación)
- **SOLO en desarrollo/testing**, no en producción

**¿Cuándo NO ejecutarlo?**

- ❌ Antes de la ejecución mensual normal (perderías el historial)
- ❌ Si necesitas conservar el registro de items enviados
- ❌ En base de datos de producción (usa backup si es necesario)

**¿Qué hace?**

1. Verifica que la base de datos existe
2. Crea automáticamente un backup (con timestamp)
3. Muestra cuántos registros hay
4. Pide confirmación (a menos que uses --yes)
5. Elimina todos los registros de `processed_items`
6. Verifica que el esquema no se modificó
7. Muestra resumen final

**¿Modifica datos?**

- ✅ SÍ modifica:
  - Tabla `processed_items`: elimina todos los registros
  - Crea backup automático en: `data/backups/processed_items_YYYYMMDD_HHMMSS.db`
- ❌ NO modifica:
  - Esquema de la base de datos
  - .env
  - Otro archivos del proyecto

**¿Envía emails?**

- ❌ NO

**¿Accede a Internet?**

- ❌ NO

**¿Necesario para producción?**

- ❌ NO
- Es una herramienta exclusivamente para testing/debugging

**Cómo ejecutarlo:**

```bash
# Modo interactivo (pide confirmación)
python reset_database.py

# Modo automatizado (sin prompts, pero sigue validando)
python reset_database.py --yes
```

**Resultado esperado:**

```
================================================================================
RESET DATABASE - TESTING MODE
================================================================================

Database path:
  data/processed_items.db

Current records: 26

Warnings checked...

1. Capturing schema...
   Schema captured: OK

2. Creating backup...
   Backup created: data/backups/processed_items_20260916_203045.db

3. Verifying backup...
   Backup verified: 26 records

4. Resetting database...
   Reset completed: OK

5. Verifying schema...
   Schema verification: OK

================================================================================
✅ RESET COMPLETED SUCCESSFULLY
================================================================================

Database:
  Path: data/processed_items.db

Records:
  Before: 26
  After:  0
  Deleted: 26

Backup:
  Location: data/backups/processed_items_20260916_203045.db
  Size: 61440 bytes

Schema: ✅ Unchanged

You can now run:
  python main.py
to process items from scratch.
```

**Flujo de Prueba Completa Desde Cero:**

```bash
# 1. Limpiar la base de datos
python reset_database.py

# 2. Ejecutar la aplicación
python main.py

# 3. Verificar logs
tail -f logs/app.log
```

**Backup:**

Si algo va mal, el backup está en:
```
data/backups/processed_items_YYYYMMDD_HHMMSS.db
```

Puedes restaurarlo manualmente si es necesario:
```bash
cp data/backups/processed_items_YYYYMMDD_HHMMSS.db data/processed_items.db
```

---

### generate_html_preview.py

**¿Para qué sirve?**

Genera una vista previa del HTML que se enviaría en el email, **sin necesidad de enviar email ni modificar la base de datos**.

Útil para:
- Ver cómo se verá el informe
- Validar el formato antes de enviarlo
- Debug de contenido HTML

**¿Cuándo ejecutarlo?**

- Después de cambios en la plantilla HTML
- Para validar contenido sin modificar nada
- Cuando quieres ver el reporte sin enviar email
- NO es necesario ejecutarlo para el funcionamiento mensual normal

**¿Qué hace?**

1. Lee los 26 items más recientes de SQLite
2. Obtiene detalles completos de cada uno desde MCP
3. Procesa cada item determinísticamente
4. Genera HTML profesional
5. Guarda en: `output/roadmap_preview.html`
6. NO envía email
7. NO modifica SQLite

**¿Modifica datos?**

- ✅ Crea/actualiza: `output/roadmap_preview.html`
- ❌ NO modifica:
  - SQLite
  - .env
  - Otros archivos

**¿Envía emails?**

- ❌ NO

**¿Necesario para producción?**

- ❌ NO
- Es una herramienta manual opcional

**Cómo ejecutarlo:**

```bash
python generate_html_preview.py
```

**Resultado esperado:**

```
GENERANDO HTML PREVIEW - VISUAL TEST

1. READING ITEMS FROM SQLITE
   Found 26 items in SQLite

2. FETCHING FULL DETAILS FROM MCP
   Fetched 26/26 items successfully

3. GENERATING HTML
   [OK] HTML generated (58822 bytes)

4. SAVING TO FILE
   [OK] Saved to: output/roadmap_preview.html
   File size: 61114 bytes
```

**Luego:**

```bash
# Abre el archivo en tu navegador
start output/roadmap_preview.html
```

---

## TESTS

### Ejecutar All Tests

```bash
pytest tests/
```

### Tests Disponibles

#### test_mcp_workflow.py

Verifica que el workflow con MCP funciona correctamente.

```bash
pytest tests/test_mcp_workflow.py
```

#### test_filter.py

Verifica que el filtrado de items funciona correctamente.

```bash
pytest tests/test_filter.py
```

**Nota:** Estos tests son útiles para desarrollo/debugging. No es necesario ejecutarlos mensualmente.

---

## REFERENCIA RÁPIDA

| Script | Propósito | Necesario | Modifica | Envía Email |
|--------|-----------|-----------|----------|-------------|
| **main.py** | Ejecutar aplicación | ✅ Sí | SQLite + Email | ✅ Sí |
| test_m365_oauth_diagnosis.py | Configurar OAuth | ✅ Primera vez | Token cache | ❌ No |
| test_config.py | Validar .env | ⚠️ Opcional | ❌ No | ❌ No |
| test_dryrun_sqlite.py | Validar DRY_RUN | ⚠️ Opcional | Depende | ❌ No |
| generate_html_preview.py | Ver preview HTML | ⚠️ Opcional | HTML archivo | ❌ No |
| reset_database.py | Reset para testing | ⚠️ Opcional | SQLite + backup | ❌ No |
| setup.bat | Instalar proyecto | ✅ Primera vez | venv + .env | ❌ No |
| pytest tests/ | Ejecutar tests | ⚠️ Opcional | ❌ No | ❌ No |

---

## FLUJO DE USO TÍPICO

### Instalación Inicial (Primera vez)

```bash
# 1. Ejecutar setup
setup.bat

# 2. Actualizar .env con tus credenciales
# (editar en editor de texto)

# 3. Validar configuración
python test_config.py

# 4. Configurar OAuth (abrirá navegador)
python test_m365_oauth_diagnosis.py
```

### Ejecución Normal (Mensual)

```bash
# Ejecutar la aplicación
python main.py
```

**Eso es todo.** La aplicación descargará, procesará y enviará el email automáticamente.

### Si Quieres Ver el HTML sin Enviar Email

```bash
# Generar preview
python generate_html_preview.py

# Abrir en navegador
start output/roadmap_preview.html
```

### Si Algo Falla

```bash
# 1. Ver logs
cat logs/app.log

# 2. Si es error de autenticación
python test_m365_oauth_diagnosis.py

# 3. Si es error de configuración
python test_config.py

# 4. Si es error de datos
python test_dryrun_sqlite.py
```

### Automatización Mensual (Windows)

Ver: `EJECUCION_AUTOMATICA_MENSUAL.md`

```
Día: 1 de cada mes
Hora: 08:00
Acción: python main.py
```

---

## INFORMACIÓN TÉCNICA

### Módulos Utilizados por main.py

```python
# main.py utiliza estos módulos de src/:

from mcp_client import MCPClient              # Conexión a MCP
from data_processor import DataProcessor      # Procesamiento de datos
from html_generator import HTMLGenerator      # Generación HTML
from email_sender import send_roadmap_email   # Envío de email
from database import ProcessedItemsDB         # SQLite
from config import config                     # Configuración
from logger import logger                     # Logging
from oauth_manager import OAuthManager        # Autenticación OAuth
from graph_sender import GraphEmailSender     # Microsoft Graph API
```

### Base de Datos

```
Ubicación: data/processed_items.db
Tabla: processed_items
Campos:
  - guid: Identificador único del item
  - url: URL del item en Microsoft
  - title: Título del item
  - processed_at: Timestamp de procesamiento
  - email_sent: 1 si se envió email, 0 si no
```

### Archivos Generados

```
logs/
  └─ app.log                  # Logs de ejecución

output/
  └─ roadmap_preview.html     # Preview HTML (generado por generate_html_preview.py)

~/.m365_roadmap/
  └─ token_cache.json         # Tokens OAuth (creado por test_m365_oauth_diagnosis.py)
```

---

**Fin de la guía de scripts**
