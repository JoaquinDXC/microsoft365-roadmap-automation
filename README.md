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
- **Envía reportes** mediante múltiples métodos:
  - SMTP (Office 365, Exchange relay, servidores genéricos)
  - Microsoft Graph API (OAuth 2.0)
  - Modo sin-envío (para testing)
- **Evita duplicados** con SQLite
- **Registra logs** detallados
- **Soporta múltiples entornos** con configuración flexible

## Requisitos Previos

Antes de instalar esta aplicación, asegúrate de tener instalados los siguientes componentes en Windows.

### 1. Python 3.13

La aplicación requiere **Python 3.13 o superior**.

#### Instalación en Windows

1. Abre **Microsoft Store**
2. Busca **Python 3.13**
3. Haz clic en **Instalar** (descargará la versión más reciente de Python 3.13.x)
4. Una vez instalado, abre **PowerShell** y verifica la instalación:

```powershell
python --version
```

Deberías ver:
```
Python 3.13.x
```

⚠️ **Importante:** Este paso es obligatorio y debe realizarse ANTES de crear el entorno virtual.

### 2. Microsoft C++ Build Tools

Algunas dependencias de Python requieren herramientas de compilación de C/C++. Debes instalar:

**[Microsoft C++ Build Tools - Visual Studio](https://visualstudio.microsoft.com/es/visual-cpp-build-tools/)**

#### Instalación en Windows

1. Descarga desde el enlace anterior
2. Ejecuta el instalador
3. En "Cargas de trabajo", selecciona:
   - ✅ **"Desarrollo para el escritorio con C++"**
4. Completa la instalación

⚠️ **Importante:** Este paso debe completarse ANTES de ejecutar `pip install -r requirements.txt`.

### 3. Conexión a Internet

La aplicación necesita conectividad para:
- Conectar con Microsoft Release Communications MCP Server
- Descargar dependencias Python
- (Opcional) Enviar emails si configuras SMTP o Microsoft Graph

### Requisitos por Modo de Email

- **DRY_RUN / EMAIL_MODE=none**: Solo Python (sin configuración de correo)
- **EMAIL_MODE=smtp**: Acceso a servidor SMTP (Office 365, Exchange, etc.)
- **EMAIL_MODE=graph**: Aplicación registrada en Azure Entra ID (OAuth 2.0)

---

## Instalación

Sigue estos pasos **EN ORDEN** desde una carpeta del proyecto en PowerShell:

### 1. Clonar o Descargar el Proyecto

```powershell
cd m365-roadmap-automation
```

### 2. Crear Entorno Virtual

```powershell
# Windows (PowerShell)
python -m venv venv
```

O si prefieres cmd.exe:

```cmd
# Windows (cmd.exe)
python -m venv venv
```

### 3. Activar el Entorno Virtual

**En PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**En cmd.exe:**

```cmd
venv\Scripts\activate.bat
```

Una vez activado, deberías ver `(venv)` al inicio de cada línea en la terminal.

### 4. Actualizar pip (Recomendado)

```powershell
python -m pip install --upgrade pip
```

### 5. Instalar Dependencias

⚠️ **Requisito previo:** Microsoft C++ Build Tools debe estar instalado (ver "Requisitos Previos").

```powershell
pip install -r requirements.txt
```

Algunas dependencias pueden requerir compilación durante la instalación. Si todo está correctamente instalado, este comando completará sin errores.

### 6. Configurar Variables de Entorno

Copia el archivo de ejemplo:

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

O manualmente:
1. Abre el Explorador de archivos
2. Copia `.env.example` y renómbralo a `.env`
3. Edita `.env` con tu editor favorito (ej: Notepad, VS Code)

Configura según tu modo de envío (ver sección "Configuración" abajo).

### 7. Ejecutar la Aplicación

```powershell
python main.py
```

Para **testing sin configurar correo** (recomendado primero):

```powershell
# .env debe contener:
# DRY_RUN=true
# EMAIL_MODE=none
python main.py
```

## Configuración

### Inicio Rápido (Modo de Prueba)

Para probar la aplicación sin configurar correo:

```bash
DRY_RUN=true
EMAIL_MODE=none
```

Ejecuta `python main.py` y la aplicación completará el flujo completo sin enviar correos.

### Modos de Envío

#### 1. EMAIL_MODE=none (Sin envío)

Útil para testing. La aplicación ignora toda configuración de correo:

```
DRY_RUN=false
EMAIL_MODE=none
```

#### 2. EMAIL_MODE=smtp (SMTP Genérico)

Soporta Office 365, Exchange relay sin autenticación, y servidores SMTP genéricos:

```
DRY_RUN=false
EMAIL_MODE=smtp
EMAIL_FROM=your.email@empresa.com
EMAIL_TO=recipient@empresa.com
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your.email@empresa.com
SMTP_PASSWORD=your_app_password
```

Para **Exchange relay sin autenticación**:

```
SMTP_HOST=exchange-relay.empresa.local
SMTP_PORT=25
SMTP_USE_TLS=false
SMTP_USERNAME=
SMTP_PASSWORD=
```

#### 3. EMAIL_MODE=graph (Microsoft Graph OAuth 2.0)

Para autenticación moderna con Microsoft 365:

```
DRY_RUN=false
EMAIL_MODE=graph
EMAIL_FROM=your.email@empresa.com
EMAIL_TO=recipient@empresa.com
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Ver [CONFIGURACION_EMAIL_M365.md](CONFIGURACION_EMAIL_M365.md) para instrucciones detalladas de configuración OAuth.

### Variables de Entorno Comunes

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `DRY_RUN` | ⭕ | `true` para no enviar emails (default: false) |
| `EMAIL_MODE` | ⭕ | `none`, `smtp`, o `graph` (default: smtp) |
| `EMAIL_FROM` | ✅* | Tu dirección de email |
| `EMAIL_TO` | ✅* | Dirección destino |
| `LOG_LEVEL` | ⭕ | DEBUG, INFO, WARNING, ERROR (default: INFO) |
| `RSS_MONTHS_BACK` | ⭕ | Meses atrás para filtrar (default: 1) |

*Requerido excepto si `DRY_RUN=true` o `EMAIL_MODE=none`

### Variables SMTP

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `SMTP_HOST` | ✅ | Host del servidor SMTP |
| `SMTP_PORT` | ⭕ | Puerto SMTP (default: 587) |
| `SMTP_USE_TLS` | ⭕ | `true` para STARTTLS, `false` para relay (default: true) |
| `SMTP_USERNAME` | ⭕ | Usuario SMTP (opcional para relay) |
| `SMTP_PASSWORD` | ⭕ | Contraseña SMTP (opcional para relay) |

### Variables Microsoft Graph/Azure

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `AZURE_TENANT_ID` | ✅ | ID del tenant de Azure/Entra |
| `AZURE_CLIENT_ID` | ✅ | Client ID de la aplicación registrada |
| `OAUTH_REDIRECT_URI` | ⭕ | URI de redirección OAuth (default: http://localhost) |

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

**IMPORTANTE**: Con `DRY_RUN=true` NO es necesario configurar credenciales de correo.

```bash
# En .env, establece:
DRY_RUN=true
EMAIL_MODE=none

# Luego ejecuta:
python main.py
```

La aplicación completará el flujo completo (MCP → filtrado → HTML) sin enviar correos ni exigir configuración de SMTP/Graph.

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
Email Abstraction
    ├→ NoOp (DRY_RUN=true o EMAIL_MODE=none)
    ├→ SMTP (Exchange, Office 365, relay)
    └→ Microsoft Graph (OAuth 2.0)
```

## Solución de Problemas

### Error: "Missing required environment variables"

**Causa**: Faltan variables en el `.env`

**Solución**: 
1. Verifica que estés usando `DRY_RUN=true` y `EMAIL_MODE=none` para testing
2. Si usas un modo de envío, comprueba variables según tu modo:
   - SMTP: necesita `SMTP_HOST`, `EMAIL_FROM`, `EMAIL_TO`
   - Graph: necesita `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `EMAIL_FROM`, `EMAIL_TO`
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
│   ├── main_workflow_new.py    # Orquestación principal (MCP)
│   ├── config.py               # Configuración centralizada
│   ├── logger.py               # Logging
│   ├── mcp_client.py           # Cliente MCP directo
│   ├── data_processor.py       # Procesamiento determinístico
│   ├── html_generator.py       # Generación de HTML
│   ├── email_sender.py         # Envío SMTP
│   ├── no_op_email_sender.py   # No-op sender (testing)
│   ├── email_factory.py        # Factory para selectores de sender
│   ├── graph_sender.py         # Envío Microsoft Graph
│   ├── oauth_manager.py        # Autenticación OAuth 2.0
│   ├── database.py             # Control de duplicados
│   ├── filter.py               # Filtrado (código legado)
│   ├── utils.py                # Utilidades
│   └── rss_reader.py           # Reader RSS (código legado)
├── data/                       # Base de datos SQLite
│   └── processed_items.db
├── logs/                       # Archivos de log
│   └── app.log
├── tests/                      # Tests unitarios
│   ├── test_email_config.py    # Tests configuración email
│   ├── test_filter.py
│   └── ...
├── .env.example                # Plantilla de configuración
├── .gitignore
├── requirements.txt            # Dependencias Python
├── README.md
├── CONFIGURACION_EMAIL_M365.md # Configuración OAuth/Graph
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
