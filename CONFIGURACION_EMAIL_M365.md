# Configuración de Envío de Email - Múltiples Entornos

**Versión:** 2.0  
**Fecha:** 2026-09-17  
**Estado:** Implementado - Soporta SMTP y Microsoft Graph

---

## 1. DESCRIPCIÓN GENERAL

Esta aplicación soporta tres modos de envío de email para adaptarse a diferentes entornos:

| Modo | Descripción | Entorno | Complejidad |
|------|-------------|---------|------------|
| **none** | Sin envío (testing) | Desarrollo | Mínima |
| **smtp** | SMTP genérico | Producción (Exchange, Office 365) | Media |
| **graph** | Microsoft Graph OAuth 2.0 | Producción (Entra ID/Azure) | Alta |

---

## 2. ARQUITECTURA DE ENVÍO

```
Configuración (EMAIL_MODE)
         │
    ┌────┴────┬──────────┬──────────┐
    ↓         ↓          ↓          ↓
  DRY_RUN    NONE       SMTP      GRAPH
    │         │          │          │
    └─ NoOpEmailSender ──┴─ SMTPEmailSender ─ GraphEmailSender
                          │                    │
                    ┌─────┴─────┐              │
                    ↓           ↓              ↓
            Office 365    On-Prem     Microsoft Graph
            Exchange       SMTP       (OAuth 2.0)
            Relay
```

---

## 3. MODO 1: DRY_RUN + EMAIL_MODE=none (Development)

### Descripción

Para testing y desarrollo sin enviar correos reales. Usado por defecto.

### Configuración en .env

```env
DRY_RUN=true
EMAIL_MODE=none
```

### Comportamiento

- ✅ Ejecuta flujo completo (MCP → Filtrado → HTML)
- ❌ NO envía correos
- ❌ NO exige configuración SMTP ni Graph
- ❌ NO marca items como enviados en SQLite
- 📁 Guarda preview HTML en `output/roadmap_preview.html`

### Validación de Configuración

- No se validan variables de correo
- No se conecta a SMTP ni Graph

### Cuándo usar

- Instalación inicial
- Testing de cambios
- Validación del flujo MCP
- Verificación de filtrados

---

## 4. MODO 2: EMAIL_MODE=none (Disabled Email)

### Descripción

Deshabilita envío de correos pero ejecuta todo lo demás en modo normal.

### Configuración en .env

```env
DRY_RUN=false
EMAIL_MODE=none
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=recipient@empresa.com
```

### Comportamiento

- ✅ Ejecuta flujo completo
- ✅ Procesa y marca items en SQLite
- ❌ NO envía correos
- ❌ NO exige configuración SMTP ni Graph
- 📁 Guarda preview HTML en `output/roadmap_preview.html`

### Validación de Configuración

- Se valida `EMAIL_FROM` y `EMAIL_TO`
- No se validan credenciales SMTP ni Graph

### Cuándo usar

- Testing en pre-producción
- Validación de filtrajes antes de activar envío
- Acceso a modo log sin dependencias de correo

---

## 5. MODO 3: EMAIL_MODE=smtp (SMTP Genérico)

### Descripción

Soporta cualquier servidor SMTP:
- Microsoft Office 365
- Exchange On-Premise
- Exchange Relay (sin autenticación)
- Servidores SMTP genéricos

### Configuración Básica

```env
DRY_RUN=false
EMAIL_MODE=smtp
EMAIL_FROM=your.email@empresa.com
EMAIL_TO=recipient@empresa.com
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your.email@empresa.com
SMTP_PASSWORD=your_app_password_here
```

### Escenario A: Office 365 (Autenticado)

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your.email@empresa.com
SMTP_PASSWORD=<contraseña_aplicacion>
```

**Notas:**
- Obtén contraseña de aplicación desde: https://account.microsoft.com/account/manage-my-microsoft-account
- NO es tu contraseña de login normal
- Genera una contraseña de aplicación de 16 caracteres

### Escenario B: Exchange On-Premise (Autenticado)

```env
SMTP_HOST=exchange.empresa.local
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=empresa\usuario
SMTP_PASSWORD=contraseña_windows
```

### Escenario C: Exchange Relay (Sin Autenticación) ⭐

```env
SMTP_HOST=exchange-relay.empresa.local
SMTP_PORT=25
SMTP_USE_TLS=false
SMTP_USERNAME=
SMTP_PASSWORD=
```

**Notas:**
- Deja `SMTP_USERNAME` y `SMTP_PASSWORD` vacíos
- Puerto 25 típicamente sin TLS
- Requiere que el relay esté configurado en Exchange

### Variables SMTP

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `SMTP_HOST` | ✅ | - | Host del servidor SMTP |
| `SMTP_PORT` | ⭕ | 587 | Puerto SMTP (25, 587, 465) |
| `SMTP_USE_TLS` | ⭕ | true | STARTTLS (true) o plain (false) |
| `SMTP_USERNAME` | ⭕ | - | Usuario SMTP (opcional) |
| `SMTP_PASSWORD` | ⭕ | - | Contraseña SMTP (opcional) |

### Puertos Comunes

| Puerto | Protocolo | Uso |
|--------|-----------|-----|
| 25 | SMTP Plain | Relay sin auth |
| 587 | SMTP+STARTTLS | Office 365, Exchange auth |
| 465 | SMTP+SSL | Gmail, algunos servidores |

### Comportamiento

- ✅ Envía correos reales vía SMTP
- ✅ Marca items en SQLite si envío exitoso
- ❌ Falla si servidor SMTP inaccesible
- ❌ Falla si credenciales inválidas (en modo auth)

### Validación de Configuración

- ✅ Se valida `SMTP_HOST` (obligatorio)
- ✅ Se valida `EMAIL_FROM` y `EMAIL_TO`
- ⚠️ No se validan credenciales (se detectan en envío)

### Debugging

Activa logs detallados:

```env
LOG_LEVEL=DEBUG
```

Logs mostrarán:
- Conexión a SMTP
- EHLO/STARTTLS
- Autenticación
- Envío de mensaje

---

## 6. MODO 4: EMAIL_MODE=graph (Microsoft Graph OAuth 2.0)

### Descripción

Envía correos usando Microsoft Graph API con autenticación OAuth 2.0. Requiere App Registration en Azure/Entra ID.

**Estado:** Implementado (requiere configuración Azure)

### Requisitos Previos

- ✅ Acceso administrativo a Azure/Entra ID
- ✅ Permisos para registrar aplicaciones
- ✅ Cuenta de Microsoft 365 empresarial

### Configuración en .env

```env
DRY_RUN=false
EMAIL_MODE=graph
EMAIL_FROM=your.email@empresa.com
EMAIL_TO=recipient@empresa.com
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OAUTH_REDIRECT_URI=http://localhost
```

### PASO 1: Crear App Registration

1. Ve a https://portal.azure.com
2. Busca "Microsoft Entra ID" → "App registrations"
3. Haz clic en "+ New registration"
4. Rellena:
   - **Name:** `M365 Roadmap Automation`
   - **Supported account types:** `Accounts in this organizational directory only`
5. Haz clic en "Register"

### PASO 2: Guardar Client ID y Tenant ID

En la página de la aplicación creada:

1. Copia **Application (client) ID** → `AZURE_CLIENT_ID`
2. Copia **Directory (tenant) ID** → `AZURE_TENANT_ID`

### PASO 3: Configurar Redirect URI

1. Menú izquierdo: "Authentication"
2. "+ Add a platform" → "Desktop and mobile applications"
3. Redirect URI: `http://localhost`
4. Haz clic en "Configure"

### PASO 4: Asignar Permisos (API Permissions)

1. Menú izquierdo: "API permissions"
2. "+ Add a permission" → "Microsoft Graph"
3. "Delegated permissions"
4. Busca: `Mail.Send`
5. Selecciona ✓ `Mail.Send`
6. Haz clic en "Add permissions"
7. **IMPORTANTE:** Haz clic en "Grant admin consent for [Organization]"

**Resultado esperado:**
```
Mail.Send (Delegated) - Status: ✓ Granted for [Organization]
```

### Comportamiento

- ✅ Envía correos vía Microsoft Graph
- ✅ Autenticación OAuth interactiva (primera vez abre navegador)
- ✅ Token se cachea en `~/.m365_roadmap/token_cache.json`
- ✅ Siguiente ejecución no requiere login
- ✅ Marca items en SQLite si envío exitoso

### Variables Graph/OAuth

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `AZURE_TENANT_ID` | ✅ | ID del tenant Azure/Entra |
| `AZURE_CLIENT_ID` | ✅ | ID de aplicación |
| `OAUTH_REDIRECT_URI` | ⭕ | URI redirección (default: http://localhost) |

### Token Cache

- **Ubicación:** `~/.m365_roadmap/token_cache.json` (Windows: `%APPDATA%\.m365_roadmap\`)
- **Permisos:** 0600 (solo lectura propietario)
- **Renovación:** Automática si token expira
- **Limpieza:** Opcional con `reset_database.py`

### Debugging

```env
LOG_LEVEL=DEBUG
```

Logs mostrarán:
- Inicialización MSAL
- Cache token (hit/miss)
- Login interactivo
- Llamadas Graph API
- Respuestas (200, 401, 403, etc.)

---

## 7. VALIDACIÓN DE CONFIGURACIÓN

### Matriz de Validación

| Configuración | DRY_RUN=true | EMAIL_MODE=none | EMAIL_MODE=smtp | EMAIL_MODE=graph |
|---|---|---|---|---|
| EMAIL_FROM | ⭕ | ✅ | ✅ | ✅ |
| EMAIL_TO | ⭕ | ✅ | ✅ | ✅ |
| SMTP_HOST | ❌ | ❌ | ✅ | ❌ |
| SMTP_PORT | ❌ | ❌ | ⭕ | ❌ |
| SMTP_USERNAME | ❌ | ❌ | ⭕ | ❌ |
| SMTP_PASSWORD | ❌ | ❌ | ⭕ | ❌ |
| AZURE_TENANT_ID | ❌ | ❌ | ❌ | ✅ |
| AZURE_CLIENT_ID | ❌ | ❌ | ❌ | ✅ |

**Leyenda:**
- ✅ Obligatoria
- ⭕ Opcional
- ❌ No necesaria

---

## 8. FLUJO DE DRY_RUN

El flag `DRY_RUN=true` siempre:

1. ✅ Ejecuta MCP, filtrado, HTML
2. ❌ No envía correos (independiente de EMAIL_MODE)
3. ❌ No marca items en SQLite
4. ✅ Guarda preview HTML
5. ❌ No valida credenciales de correo

```
DRY_RUN=true (cualquier EMAIL_MODE)
         │
         ↓
    NoOpEmailSender
         │
         ├→ Registra: "Email would be sent to X"
         ├→ NO conecta a SMTP/Graph
         ├→ NO marca SQLite
         └→ Retorna True (éxito simulado)
```

---

## 9. SEGURIDAD

### Protección de Credenciales

✅ **Archivo .env:**
- Está en `.gitignore`
- Nunca se commitea a Git
- Contiene credenciales reales

❌ **Archivo .env.example:**
- Público (ejemplo seguro)
- Sin credenciales reales
- Muestra estructura

### Logs

✅ **Seguro:**
- No se imprimen contraseñas
- No se imprimen tokens
- Se registran solo operaciones

❌ **Peligro:**
- Variables raw en debug
- Headers de API sin sanitizar

### Token Cache (Graph)

✅ **Protegido:**
- Permisos 0600 (solo propietario)
- Guardado en directorio home privado
- Renovación automática

---

## 10. SOLUCIÓN DE PROBLEMAS

### "Missing SMTP_HOST"

**Causa:** `EMAIL_MODE=smtp` pero `SMTP_HOST` no está configurado

**Solución:**
```env
EMAIL_MODE=smtp
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
```

### "SMTP authentication failed"

**Causa:** Usuario/contraseña incorrectos (modo smtp con auth)

**Solución:**
1. Verifica `SMTP_USERNAME` y `SMTP_PASSWORD`
2. Para Office 365: usa contraseña de aplicación, no login
3. Prueba conexión manual con telnet:
   ```bash
   telnet smtp.office365.com 587
   ```

### "SMTP connection refused"

**Causa:** Servidor SMTP inaccesible o puerto incorrecto

**Solución:**
1. Verifica conectividad: `ping smtp.office365.com`
2. Verifica puerto: puerto 25/587 vs 465
3. Revisa firewall/proxy corporativo

### "Graph authentication failed"

**Causa:** Token OAuth inválido o permisos insuficientes

**Solución:**
1. Verifica `AZURE_TENANT_ID` y `AZURE_CLIENT_ID`
2. Comprueba que tengas `Mail.Send` permission con "Grant admin consent"
3. Limpia cache:
   ```bash
   rm ~/.m365_roadmap/token_cache.json  # Linux/Mac
   rmdir %APPDATA%\.m365_roadmap\       # Windows
   ```
4. Ejecuta nuevamente para re-autenticar

### "Permission denied (403)"

**Causa:** Aplicación no tiene permisos Mail.Send

**Solución:**
1. Ve a Azure Portal → tu aplicación
2. API permissions → Verifica `Mail.Send` tiene ✓ "Granted"
3. Si no: haz clic en "Grant admin consent for [Organization]"

---

## 11. EJEMPLOS DE CONFIGURACIÓN COMPLETA

### Ejemplo 1: Desarrollo (DRY_RUN)

```env
DRY_RUN=true
EMAIL_MODE=none
LOG_LEVEL=INFO
```

Ejecutar: `python main.py`

Resultado: ✅ Flujo completo, ❌ sin correos, ❌ sin validación email

### Ejemplo 2: Office 365 Producción

```env
DRY_RUN=false
EMAIL_MODE=smtp
EMAIL_FROM=roadmap@empresa.onmicrosoft.com
EMAIL_TO=team@empresa.com
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=roadmap@empresa.onmicrosoft.com
SMTP_PASSWORD=AbCd!234XyZw567*aBcD
LOG_LEVEL=INFO
```

### Ejemplo 3: Exchange Relay On-Prem

```env
DRY_RUN=false
EMAIL_MODE=smtp
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=team@empresa.com
SMTP_HOST=mail.empresa.local
SMTP_PORT=25
SMTP_USE_TLS=false
LOG_LEVEL=INFO
```

**Nota:** Sin `SMTP_USERNAME`/`SMTP_PASSWORD` (relay abierto)

### Ejemplo 4: Microsoft Graph

```env
DRY_RUN=false
EMAIL_MODE=graph
EMAIL_FROM=roadmap@empresa.com
EMAIL_TO=team@empresa.com
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
OAUTH_REDIRECT_URI=http://localhost
LOG_LEVEL=INFO
```

---

## 12. MIGRACIÓN DE CONFIGURACIÓN ANTIGUA

Si usabas `EMAIL_PASSWORD` (formato antiguo):

**Antes:**
```env
EMAIL_PASSWORD=password123
```

**Ahora:**
```env
EMAIL_MODE=smtp
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your.email@empresa.com
SMTP_PASSWORD=password123
```

O si prefieres mantener compatibilidad, el código fallback automáticamente a `EMAIL_PASSWORD` si `SMTP_PASSWORD` no está configurado.

---

## 13. REFERENCIAS

- **Microsoft Graph API:** https://docs.microsoft.com/en-us/graph/api/user-sendmail
- **MSAL Python:** https://msal-python.readthedocs.io/
- **Office 365 SMTP:** https://docs.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/authenticated-client-smtp-submission
- **Azure App Registration:** https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app

