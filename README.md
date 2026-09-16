# M365 Roadmap Automation

Automatización independiente para procesar y distribuir novedades del roadmap de Microsoft 365 mediante Microsoft Release Communications MCP Server.

## Descripción

Esta aplicación obtiene actualizaciones de roadmap de Microsoft 365 directamente desde el servidor MCP de Microsoft, las procesa y distribuye por email en formato HTML profesional.

### Características

- **Obtiene roadmaps** desde Microsoft Release Communications MCP Server (sin RSS)
- **Filtra contenido** por productos específicos:
  - Exchange Online
  - Microsoft Teams
  - SharePoint
  - OneDrive
- **Procesa determinísticamente** (sin dependencias de IA)
- **Genera HTML profesional** optimizado para email
- **Envía reportes** via SMTP (Office 365)
- **Evita duplicados** con SQLite
- **Registra logs** detallados

## Requisitos

- Python 3.8+
- Conexión a internet
- Email de Office 365 y contraseña de aplicación
- Archivo `.env` configurado

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd m365-roadmap-automation
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (cmd.exe)
python -m venv venv
venv\Scripts\activate.bat

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# Valores requeridos:
# - EMAIL_FROM: Tu email de Office 365
# - EMAIL_PASSWORD: Contraseña de aplicación de Office 365
# - EMAIL_TO: Dirección de correo destino
```

## Configuración

### Variables de Entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `EMAIL_FROM` | ✅ | Tu email de Office 365 |
| `EMAIL_PASSWORD` | ✅ | Contraseña de aplicación de Office 365 |
| `EMAIL_TO` | ✅ | Dirección de correo destino |
| `RSS_MONTHS_BACK` | ⭕ | Meses atrás para filtro de fecha (default: 1) |
| `LOG_LEVEL` | ⭕ | Nivel de logging (default: INFO) |
| `DRY_RUN` | ⭕ | Prueba sin enviar emails (default: false) |

### Configuración Avanzada

El archivo `src/config.py` contiene ajustes adicionales que puedes modificar:

```python
# Endpoint MCP
MCP_ENDPOINT = "https://www.microsoft.com/releasecommunications/mcp"

# Productos permitidos para filtrado
ALLOWED_PRODUCTS = {
    "Exchange Online",
    "Microsoft Teams",
    "SharePoint",
    "OneDrive",
}

# Parámetros de reintento
HTTP_RETRIES = 3
HTTP_TIMEOUT = 30
```

## Ejecución

### Ejecución Manual

```bash
# Desde el directorio raíz del proyecto
python main.py
```

### Dry Run (prueba sin enviar email)

```bash
# En .env, establece:
DRY_RUN=true

# Luego ejecuta:
python main.py
```

### Ejecución Automática

#### Windows (Task Scheduler)

1. Abre Task Scheduler (`taskschd.msc`)
2. Crea una nueva tarea básica
3. En "Acciones", establece:
   - Programa/script: `python.exe`
   - Argumentos: `C:\ruta\al\main.py`
   - Iniciar en: `C:\ruta\al\proyecto`
4. En "Desencadenadores", establece la frecuencia deseada (ej: mensualmente)


## Logs

Los logs se guardan en `logs/app.log` con rotación automática.

### Ver logs en tiempo real

```bash
# Windows PowerShell
Get-Content logs/app.log -Tail 50 -Wait

# Linux/Mac
tail -f logs/app.log
```

### Cambiar nivel de logging

Edita `.env`:

```
LOG_LEVEL=DEBUG    # Información detallada
LOG_LEVEL=INFO     # Información estándar
LOG_LEVEL=WARNING  # Solo advertencias y errores
LOG_LEVEL=ERROR    # Solo errores
```

## Base de Datos

La aplicación mantiene una base de datos SQLite en `data/processed_items.db` que registra:

- Elementos procesados (ID)
- Fecha de procesamiento
- Si fue incluido en el informe
- Si fue enviado por email

Esta información evita procesar duplicados innecesariamente.

## Flujo de Procesamiento

```
MRC MCP Server
    ↓
Paginación (50 items/página)
    ↓
Filtro temporal (últimos 30 días)
    ↓
Filtro de productos (4 específicos)
    ↓
Verificación de duplicados (SQLite)
    ↓
Obtención de detalles completos
    ↓
Procesamiento determinístico
    ↓
Generación HTML
    ↓
Envío de email (SMTP)
```

## Solución de Problemas

### Error: "Missing required environment variables"

**Causa**: Faltan variables en el `.env`

**Solución**: 
1. Copia `.env.example` a `.env`
2. Rellena todos los valores requeridos
3. Comprueba que no hay espacios alrededor del `=`

### Error: "Failed to connect to MCP"

**Causa**: Problema de conexión a Microsoft Release Communications MCP

**Solución**:
1. Comprueba la conexión a internet
2. Verifica que https://www.microsoft.com/releasecommunications/mcp es accesible
3. Revisa los logs para más detalles

### Error: "Email failed"

**Causa**: Problema con Office 365 SMTP

**Solución**:
1. Verifica tu EMAIL_FROM y EMAIL_PASSWORD
2. Comprueba que es una contraseña de aplicación (no tu contraseña normal)
3. Verifica permisos en Office 365

### Dry Run no envía email

**Comportamiento normal**: Si `DRY_RUN=true`, el email se procesa pero NO se envía. Esto es intencional para validar el proceso sin afectar a los destinatarios.

## Seguridad

- El archivo `.env` está en `.gitignore` para proteger credenciales
- No se almacenan ni imprimen secretos en logs
- El endpoint MCP es público (sin autenticación requerida)
- Se utiliza solo SMTP de Office 365 (protocolo estándar)

## Estructura del Proyecto

```
m365-roadmap-automation/
├── src/
│   ├── __init__.py
│   ├── main_workflow_new.py   # Orquestación principal (MCP)
│   ├── config.py               # Configuración centralizada
│   ├── logger.py               # Logging
│   ├── mcp_client.py           # Cliente MCP directo
│   ├── data_processor.py       # Procesamiento determinístico
│   ├── html_generator.py       # Generación de HTML
│   ├── email_sender.py         # Envío de emails
│   ├── database.py             # Control de duplicados
│   ├── filter.py               # Filtrado (código legado)
│   ├── utils.py                # Utilidades
│   └── rss_reader.py           # Reader RSS (código legado)
├── data/                       # Base de datos SQLite
│   └── processed_items.db
├── logs/                       # Archivos de log
│   └── app.log
├── tests/                      # Tests unitarios
├── .env.example                # Plantilla de configuración
├── .gitignore
├── requirements.txt            # Dependencias Python
├── README.md
└── main.py                     # Punto de entrada
```

### Ejecutar tests

```bash
python -m pytest tests/ -v
```

### Debugging

Establece `LOG_LEVEL=DEBUG` en `.env` para obtener información detallada.

Los logs incluirán:
- Cada petición al MCP
- Datos recibidos
- Elementos filtrados
- Razones de filtrado
- Errores y reintentos

## Licencia

Privada

## Soporte

Para problemas, revisa los logs en `logs/app.log` con `LOG_LEVEL=DEBUG`.
