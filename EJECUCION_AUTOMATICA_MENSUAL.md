# Ejecución Automática Mensual - M365 Roadmap Automation

**Versión:** 1.0  
**Fecha:** 2026-09-16  
**Objetivo:** Configurar ejecución automática el día 1 de cada mes

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen de Ejecución](#resumen-de-ejecución)
2. [Preparación General](#preparación-general)
3. [Windows Task Scheduler](#windows-task-scheduler)
4. [Linux Cron](#linux-cron)
5. [Verificación de Ejecuciones](#verificación-de-ejecuciones)
6. [Solución de Problemas](#solución-de-problemas)
7. [Flujo de Ejecución Detallado](#flujo-de-ejecución-detallado)
8. [Escenarios de Error](#escenarios-de-error)

---

## RESUMEN DE EJECUCIÓN

### Timing

| Aspecto | Valor |
|---------|-------|
| **Día** | 1 de cada mes (predeterminado) |
| **Hora** | 08:00 (configurable) |
| **Duración estimada** | 2-5 minutos |
| **Frecuencia** | Mensual |

### Acciones Ejecutadas

```
Inicio
  ↓
Conectarse a MRC MCP Server
  ↓
Obtener roadmap completo (últimos 30 días)
  ↓
Filtrar por productos:
  ├─ Exchange Online
  ├─ Microsoft Teams
  ├─ SharePoint
  └─ OneDrive
  ↓
Filtrar por fecha (últimos 30 días)
  ↓
Deduplicar contra SQLite
  ↓
Procesar nuevos items
  ↓
Generar HTML profesional
  ↓
Autenticarse con OAuth (si es necesario)
  ↓
Enviar email via Microsoft Graph API
  ↓
Marcar items como "email_sent" en SQLite
  ↓
Registrar en logs
  ↓
Finalizar
```

---

## PREPARACIÓN GENERAL

### Requisitos Previos

- Método de envío seleccionado:
  - **SMTP:** Configuración de servidor SMTP
  - **Graph/OAuth:** Token cache en `~/.m365_roadmap/token_cache.json`
  - **No envío:** Configuración mínima (no requiere credenciales)
- `.env` configurado según tu `EMAIL_MODE`
- Dependencias instaladas: `pip install -r requirements.txt`
- Acceso administrativo a la máquina

### Archivos Críticos

```
C:\RUTA\DEL\PROYECTO\
├── src/
│   ├── main_workflow.py          ← Script principal
│   ├── oauth_manager.py
│   ├── graph_sender.py
│   ├── mcp_client.py
│   ├── data_processor.py
│   ├── html_generator.py
│   └── config.py
├── .env                           ← Configuración
├── .env.example
├── requirements.txt
└── logs/                          ← Registros de ejecución
```

### Python Verificado

```bash
python --version
# Esperado: Python 3.8 o superior
```

---

# WINDOWS TASK SCHEDULER

## PASO 1: ACCEDER A TASK SCHEDULER

### Opción A: Interfaz Gráfica

1. Presiona `Windows Key + R`
2. Escribe: `taskschd.msc`
3. Presiona `Enter`
4. Se abre "Task Scheduler"

### Opción B: Panel de Control

1. Panel de Control → Herramientas Administrativas → Programador de tareas

## PASO 2: CREAR TAREA NUEVA

1. En el panel izquierdo, haz clic en "Task Scheduler Library"
2. En el panel derecho, haz clic en "Create Basic Task..."
3. Se abre el asistente de creación

## PASO 3: CONFIGURAR INFORMACIÓN GENERAL

### Nombre y Descripción

```
Nombre:        M365 Roadmap Monthly Update
Descripción:   Obtiene y envía actualizaciones del roadmap de Microsoft 365 el día 1 de cada mes
Ubicación:     \M365_Roadmap_Tasks\ (crear carpeta nueva)
```

**Importancia:**

- Nombre descriptivo facilita identificar la tarea
- Descripción ayuda para auditoría y mantenimiento
- Carpeta organiza múltiples tareas relacionadas

## PASO 4: CONFIGURAR TRIGGER (ACTIVADOR)

1. Haz clic en "Next"
2. Se abre "Trigger" dialog
3. Haz clic en "New..."
4. Configura el trigger:

   | Setting | Valor |
   |---------|-------|
   | **Begin the task** | On a schedule |
   | **Recurrence** | Monthly |
   | **Day** | 1 |
   | **Time** | 08:00:00 (configurable) |

5. Haz clic en "OK"

### Configuración Avanzada de Trigger

Haz clic en "New..." → "Advanced settings":

```
☑ Repeat task every:    (dejar desmarcado)
☑ If the task fails, retry every:    5 minutes (until 3 times)
☑ Stop the task if it runs longer than:    15 minutes
☑ If the task is already running:    Do not start a new instance
```

**Explicación:**

- **Retry:** Si falla, reintentar cada 5 minutos (máximo 3 veces)
- **Stop if:** Cancelar si lleva más de 15 minutos (protección contra cuelgues)
- **Already running:** Evitar ejecutiones simultáneas si la anterior aún está activa

## PASO 5: CONFIGURAR ACCIÓN (ACTION)

1. Haz clic en "Next"
2. Se abre "Action" dialog
3. Haz clic en "New..."
4. Configura:

   | Setting | Valor |
   |---------|-------|
   | **Action** | Start a program |
   | **Program/script** | `python` o `/ruta/a/python.exe` |
   | **Add arguments** | `src/main_workflow.py` |
   | **Start in** | `C:\RUTA\DEL\PROYECTO` |

### Ejemplo Concreto (Windows)

Si Python está en el PATH:

```
Program/script:  python
Arguments:       src/main_workflow.py
Start in:        C:\Users\TuUsuario\Documents\M365_Roadmap_Project
```

Si Python NO está en el PATH:

```
Program/script:  C:\Users\TuUsuario\AppData\Local\Programs\Python\Python313\python.exe
Arguments:       src/main_workflow.py
Start in:        C:\Users\TuUsuario\Documents\M365_Roadmap_Project
```

Para encontrar la ruta de Python:

```powershell
where python
# o
python -c "import sys; print(sys.executable)"
```

## PASO 6: CONFIGURAR CONDICIONES

1. Haz clic en "Conditions" tab
2. Configura:

   | Opción | Valor |
   |--------|-------|
   | **Power** | ☑ Start the task only if the computer is on AC power |
   | **Network** | ☑ Start the task only if the following network connection is available (Any) |

**Explicación:**

- **AC Power:** No ejecutar si está en batería
- **Network:** Asegurar conexión a internet para conectar a MRC MCP

## PASO 7: CONFIGURAR CONFIGURACIÓN (SETTINGS)

1. Haz clic en "Settings" tab
2. Marca estas opciones:

   ```
   ☑ Allow task to be run on demand
   ☑ Stop the task if it runs longer than: 15 minutes
   ☑ If the running task does not end when requested, force it to stop
   ☑ If the task fails, restart every: 5 minutes (until 3 times)
   ☑ Run task as soon as possible after a scheduled start is missed
   ☑ If the task is already running:
       ○ Do not start a new instance
   ```

**Explicación:**

- **Run on demand:** Permite ejecutar manualmente desde Task Scheduler
- **Stop/Force:** Previene procesos "zombie"
- **Restart:** Reintenta automáticamente
- **Missed schedule:** Si se perdió una ejecución, ejecutar en el próximo reinicio

## PASO 8: CONFIGURAR USUARIO

1. Haz clic en "General" tab
2. En "Security options":

   | Setting | Valor |
   |---------|-------|
   | **Run as user** | TU_USUARIO (actual) |
   | **Run whether user is logged on or not** | ☑ Marcado |
   | **Run with highest privileges** | ☐ Desmarcado (solo si necesario) |

### ¿Cuándo Marcar "Run whether user is logged on or not"?

✅ **Sí marcar** si:
- Quieres que se ejecute incluso cuando no estés conectado
- La máquina ejecuta Task Scheduler automáticamente

❌ **No marcar** si:
- Solo quieres que se ejecute cuando hayas iniciado sesión
- Tienes problemas con variables de entorno

### ¿Cuándo Marcar "Run with highest privileges"?

❌ **Generalmente NO:** La aplicación Python no necesita permisos elevados

✅ **Solo si:**
- Necesitas escribir en directorios protegidos (raro)
- Tienes problemas de permisos de archivos

## PASO 9: GUARDAR TAREA

1. Verifica que todos los campos estén configurados
2. Haz clic en "Finish"
3. Se te pedirá confirmación de usuario

### Verificación Post-Creación

En Task Scheduler:

1. Haz clic en "Task Scheduler Library"
2. Busca "M365 Roadmap Monthly Update"
3. Verifica que aparezca en la lista
4. Haz clic derecho → "Properties" para revisar

---

## PASO 10: PROBAR TAREA (IMPORTANTE)

Antes de confiar en la automatización, prueba manualmente:

### Ejecución Manual

1. En Task Scheduler, localiza tu tarea
2. Haz clic derecho → "Run"
3. La tarea se ejecuta inmediatamente

### Verificación de Ejecución

1. Abre el archivo `logs/app.log`
2. Busca la última línea para ver el resultado
3. Verificar: ¿Se ejecutó correctamente? ¿Se envió email?

### Logs Esperados

```
2026-09-01 08:00:15 INFO     === M365 Roadmap Automation Started ===
2026-09-01 08:00:16 INFO     Connecting to MRC MCP...
2026-09-01 08:00:22 INFO     Downloaded 1766 roadmap items
2026-09-01 08:00:23 INFO     Filtered: 26 items matching criteria
2026-09-01 08:00:24 INFO     Deduplication: 0 duplicates, 26 new items
2026-09-01 08:00:45 INFO     HTML generated: 61114 bytes
2026-09-01 08:00:46 INFO     Authenticating with OAuth...
2026-09-01 08:00:47 INFO     Email sent successfully to: destinatario@empresa.com
2026-09-01 08:00:48 INFO     Marked 26 items as email_sent in SQLite
2026-09-01 08:00:49 INFO     === M365 Roadmap Automation Completed ===
```

---

## PASO 11: VERIFICAR HISTORIAL

En Task Scheduler:

1. Localiza tu tarea
2. En el panel inferior, verifica la sección "History"
3. Cada ejecución debe mostrar:
   - Fecha y hora
   - Status: "The task completed with an exit code (0)." (0 = éxito)

### Si ves errores

- Exit code 1: Error en la aplicación Python
- Exit code 2: Archivo no encontrado
- Ver logs en `logs/app.log` para detalles

---

## PASO 12: MANTENIMIENTO

### Deshabilitar Tarea

1. Haz clic derecho en la tarea
2. Selecciona "Disable"
3. La tarea no se ejecutará hasta ser re-habilitada

### Re-habilitar Tarea

1. Haz clic derecho
2. Selecciona "Enable"

### Eliminar Tarea

1. Haz clic derecho
2. Selecciona "Delete"
3. Confirma eliminación

---