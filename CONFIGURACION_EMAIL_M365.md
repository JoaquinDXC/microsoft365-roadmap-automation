# Configuración de Envío de Email - Microsoft 365 (OAuth 2.0)

**Versión:** 1.0  
**Fecha:** 2026-09-16  
**Estado:** Guía de próximos pasos (implementación pendiente)

---

## ⚠️ ESTADO ACTUAL

**IMPORTANTE:** El envío de correo mediante Microsoft 365 requiere permisos administrativos en Microsoft Entra ID (anteriormente Azure AD) para registrar la aplicación. Esta guía documenta los pasos necesarios para completar la configuración cuando esos permisos estén disponibles.

---

## 1. OBJETIVO

Configurar la aplicación para enviar reportes de roadmap de Microsoft 365 mediante:

- **Protocolo:** OAuth 2.0 (autenticación moderna y segura)
- **API:** Microsoft Graph (`/me/sendMail`)
- **Biblioteca:** MSAL (Microsoft Authentication Library for Python)
- **Tipo de aplicación:** Desktop/Local (sin servidor web)
- **Permisos:** Delegados (`Mail.Send`)

---

## 2. ARQUITECTURA PREVISTA

```
┌─────────────────────────────────────────────────────────────────┐
│                     Aplicación Python                           │
│  (M365 Roadmap Automation - Desktop App Pattern)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
                 ┌──────────────────┐
                 │  MSAL Library    │
                 │  Token Cache     │
                 └────────┬─────────┘
                          │
                  ┌───────┴──────┐
                  │              │
        ┌─────────▼────┐    ┌────▼──────────┐
        │  First Login │    │ Cached Tokens │
        │  Interactive │    │ (Silent Mode) │
        │  Browser     │    └────┬──────────┘
        └─────────┬────┘         │
                  │              │
                  └──────┬───────┘
                         │
                         ↓
         ┌───────────────────────────────┐
         │  Microsoft Graph API          │
         │  POST /me/sendMail            │
         │  Endpoint: graph.microsoft.com│
         └───────────────┬───────────────┘
                         │
                         ↓
         ┌───────────────────────────────┐
         │  Email Enviado               │
         │  Bandeja de salida usuario   │
         └───────────────────────────────┘
```

### Componentes Clave

| Componente | Descripción | Ubicación |
|-----------|-------------|-----------|
| **MSAL** | Microsoft Authentication Library | `src/oauth_manager.py` |
| **OAuthManager** | Gestión de tokens y cache | `src/oauth_manager.py` |
| **GraphEmailSender** | Cliente HTTP para Graph API | `src/graph_sender.py` |
| **Token Cache** | Almacenamiento persistente | `~/.m365_roadmap/token_cache.json` (Windows: `%APPDATA%\` ) |
| **Configuración** | Variables de entorno | `.env` |

---

## 3. REQUISITOS PREVIOS

### Permisos Necesarios

⚠️ **Requiere:** Acceso administrativo a Microsoft Entra ID (Azure AD) de tu organización

- Capacidad para registrar aplicaciones
- Capacidad para asignar permisos delegados
- Acceso a Azure Portal → Azure AD → App registrations

### Credenciales

- Email de cuenta de Microsoft 365 empresarial
- Permisos para recibir emails desde la aplicación

### Software

- Python 3.8+
- pip (gestor de paquetes)
- Internet Explorer o navegador moderno (para OAuth flow interactivo)

---

## 4. PASO 1: CREAR APP REGISTRATION EN MICROSOFT ENTRA ID

### Acceso a Azure Portal

1. Ve a https://portal.azure.com
2. Inicia sesión con cuenta de administrador de tu tenant
3. Busca "Azure AD" o "Microsoft Entra ID"
4. Selecciona "App registrations" en el menú izquierdo

### Crear Nueva Aplicación

1. Haz clic en "+ New registration"
2. Rellena el formulario:

   | Campo | Valor | Notas |
   |-------|-------|-------|
   | **Name** | `M365 Roadmap Automation` | Nombre descriptivo |
   | **Supported account types** | `Accounts in this organizational directory only` | Solo tu tenant |
   | **Redirect URI** | Déjalo en blanco por ahora | Lo agregaremos en el siguiente paso |

3. Haz clic en "Register"
4. **Copia y guarda estos valores ahora:**
   - **Client ID** (Application ID): `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - **Tenant ID** (Directory ID): `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### Obtener Tenant ID

Desde la página de la app registration recién creada:

1. En el panel izquierdo, selecciona "Overview"
2. Busca los campos:
   - **Application (client) ID** ← Este es el CLIENT_ID
   - **Directory (tenant) ID** ← Este es el TENANT_ID
3. Copia ambos valores (similares a `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### Configurar Redirect URI (Paso Crítico)

1. En el menú izquierdo, selecciona "Authentication"
2. En la sección "Platform configurations", busca "Desktop and mobile applications"
3. Haz clic en "+ Add a platform"
4. Selecciona "Desktop and mobile applications"
5. En "Redirect URIs", ingresa: `http://localhost`
6. Haz clic en "Configure"

**Resultado esperado:**
```
Platform: Desktop and mobile applications
Redirect URI: http://localhost
```

### Configuración de Autenticación (Recomendado)

En la página "Authentication":

- Desmarca: "Accounts for any organizational directory" (mantén solo tu tenant)
- Marca las opciones de flujo permitidas:
  - ✅ Authorization code flow
  - ❌ Implicit and hybrid flows (no necesario)

**¿Por qué `http://localhost`?**

- Es un patrón estándar para aplicaciones de escritorio
- MSAL abre el navegador automáticamente en http://localhost:PUERTO_DINÁMICO
- No requiere servidor web
- Totalmente seguro para aplicaciones locales

---

## 5. PASO 2: CONFIGURAR PERMISOS (DELEGADOS)

### ¿Qué son los permisos delegados?

- La aplicación actúa en nombre del usuario
- El usuario autoriza la aplicación la primera vez
- La aplicación solo accede a los recursos que el usuario aprobó
- Diferente de "Application Permissions" (que requieren Client Secret)

### Asignar Permiso Mail.Send

1. Desde la página de app registration, ve a "API permissions"
2. Haz clic en "+ Add a permission"
3. Selecciona "Microsoft Graph"
4. Elige "Delegated permissions"
5. Busca "Mail" y encuentra "Mail.Send"
6. Marca el checkbox de `Mail.Send`
7. Haz clic en "Add permissions"

### Agregar Offline Access (Opcional pero Recomendado)

Para obtener un refresh token que permita renovar sesiones sin interacción:

1. Haz clic nuevamente en "+ Add a permission"
2. Selecciona "Microsoft Graph"
3. Elige "Delegated permissions"
4. Busca "offline_access"
5. Marca el checkbox
6. Haz clic en "Add permissions"

**Nota:** Con offline_access, los tokens se pueden renovar automáticamente durante 90 días sin requerir login.

---

## 6. PASO 3: VERIFICAR CONFIGURACIÓN EN AZURE

Después de los pasos anteriores, tu app registration debe tener:

- ✅ **Client ID:** Guardado
- ✅ **Tenant ID:** Guardado
- ✅ **Redirect URI:** `http://localhost` configurado
- ✅ **Permisos API:** 
  - `Mail.Send` (delegated)
  - `offline_access` (delegated, opcional)
- ✅ **Sin Client Secret:** (no necesario para desktop apps con MSAL)

---

## 7. PASO 4: CONFIGURAR VARIABLES DE ENTORNO

### Archivo `.env`

En la raíz de tu proyecto, actualiza el archivo `.env`:

```bash
# OAuth 2.0 Configuration - Microsoft 365
OAUTH_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OAUTH_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OAUTH_REDIRECT_URI=http://localhost

# Email Configuration
EMAIL_FROM=tu.email@empresa.com
EMAIL_TO=destinatario@empresa.com

# Logging
LOG_LEVEL=INFO
DRY_RUN=false
```

### ⚠️ IMPORTANTE: NO INCLUIR SECRETOS

- ❌ NO incluir contraseñas
- ❌ NO incluir tokens
- ❌ NO incluir Client Secret (no se usa en desktop apps)
- ✅ Los tokens se guardan automáticamente en `~/.m365_roadmap/token_cache.json` en login

### Valores Reales vs. Placeholders

Reemplaza los siguientes valores con tus valores reales de Azure:

- `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (CLIENT_ID y TENANT_ID) → Tus valores de Azure
- `tu.email@empresa.com` → Tu email de Microsoft 365
- `destinatario@empresa.com` → Email de destino de los reportes

---

## 8. PASO 5: INSTALAR DEPENDENCIAS

Desde la terminal, en la raíz del proyecto:

```bash
pip install -r requirements.txt
```

Esto instala:
- `msal>=1.28.0` (Microsoft Authentication Library)
- `aiohttp>=3.9.1` (Cliente HTTP asincrónico)
- `python-dotenv>=1.0.0` (Carga de .env)
- Otras dependencias existentes

---

## 9. PASO 6: PRIMER INICIO DE SESIÓN (AUTENTICACIÓN INTERACTIVA)

El primer inicio de sesión requiere interacción del usuario (navegador):

### Ejecutar Diagnóstico

```bash
python test_m365_oauth_diagnosis.py
```

### Flujo Esperado

1. **Script se inicia**
   ```
   Inicializando OAuth Manager...
   Verificando token cache existente...
   ```

2. **Se abre navegador automáticamente**
   - URL: Algo como `https://login.microsoftonline.com/...`
   - Pantalla: "Sign in to your account"

3. **Usuario ingresa credenciales**
   - Email: tu.email@empresa.com
   - Contraseña: Tu contraseña de Microsoft 365

4. **Se pide consentimiento**
   - Título: "M365 Roadmap Automation wants to access your mail"
   - Permisos solicitados: "Send mail as you" (Mail.Send)
   - Botón: "Accept"

5. **Usuario acepta**
   - Pantalla redirecciona a `http://localhost` (página vacía, es normal)
   - MSAL captura el código de autorización

6. **Token se obtiene y almacena**
   - Ubicación: `~/.m365_roadmap/token_cache.json`
   - Permisos: Solo lectura/escritura del usuario (0600)

7. **Diagnóstico finaliza**
   ```
   [OK] Usuario autenticado: usuario@empresa.com
   [OK] Tenant: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   [OK] Scopes autorizados: Mail.Send, offline_access
   [OK] Conectividad a Microsoft Graph: EXITOSA
   ```

---

## 10. PASO 7: RENOVACIÓN AUTOMÁTICA DE TOKENS

### Access Token (Corta duración)

- **Duración:** 1 hora
- **Almacenamiento:** Cache persistente
- **Renovación:** Automática por MSAL

### Refresh Token (Larga duración)

- **Duración:** 90 días
- **Almacenamiento:** Cache persistente (encriptado por MSAL)
- **Automatización:** Ejecutar la aplicación antes de 90 días sin interacción

### Tokens Expirados (Después de 90 días)

Si la aplicación no se ejecuta durante 90 días:

1. El refresh token expira
2. En la siguiente ejecución, se requiere login interactivo nuevamente
3. Ejecutar: `python test_m365_oauth_diagnosis.py --reauth`
4. Sigue el mismo flujo del Paso 6

---

## 11. PASO 8: PRUEBA DE AUTENTICACIÓN

Verifica que la autenticación funciona sin errores:

```bash
python test_m365_oauth_diagnosis.py
```

### Salida Esperada

```
================================================================================
DIAGNÓSTICO OAUTH - MICROSOFT GRAPH
================================================================================

1. INICIALIZANDO OAUTH MANAGER
   [OK] MSAL configurado correctamente

2. VERIFICANDO TOKEN CACHE
   [OK] Cache encontrado en: ~/.m365_roadmap/token_cache.json

3. ADQUIRIENDO TOKEN
   [OK] Token adquirido silenciosamente (sin interacción)

4. INFORMACIÓN DE CUENTA
   Usuario: usuario@empresa.com
   Tenant ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Scopes: https://graph.microsoft.com/.default offline_access

5. PROBANDO CONECTIVIDAD A MICROSOFT GRAPH
   [OK] Conectividad: EXITOSA
   Endpoint: POST https://graph.microsoft.com/v1.0/me/sendMail

================================================================================
STATUS: AUTENTICACIÓN VALIDADA
================================================================================
```

---

## 12. PASO 9: PRUEBA DE ENVÍO DE EMAIL

**IMPORTANTE:** Esta prueba requiere que el script de diagnóstico haya completado exitosamente.

### Crear Script de Prueba

En la raíz del proyecto, crea un archivo `test_email_send.py`:

```python
#!/usr/bin/env python3
import asyncio
from src.oauth_manager import OAuthManager
from src.graph_sender import GraphEmailSender

async def test_send_email():
    oauth = OAuthManager()
    sender = GraphEmailSender(oauth)
    
    # Obtener token
    token = await oauth.get_token()
    if not token:
        print("[ERROR] No se pudo obtener token")
        return
    
    # Prueba de envío
    try:
        result = await sender.send_email(
            to_address="tu.email@empresa.com",
            subject="PRUEBA: Email desde Microsoft Graph",
            html_body="<h1>Prueba de envío</h1><p>Este es un email de prueba desde OAuth 2.0.</p>"
        )
        
        print(f"[OK] Email enviado exitosamente")
        print(f"    ID de mensaje: {result.get('id')}")
    except Exception as e:
        print(f"[ERROR] Fallo en envío: {e}")

if __name__ == "__main__":
    asyncio.run(test_send_email())
```

### Ejecutar Prueba

```bash
python test_email_send.py
```

### Resultado Esperado

- Email aparece en la bandeja de salida de tu cuenta Microsoft 365
- Asunto: "PRUEBA: Email desde Microsoft Graph"
- Contenido: HTML con título y párrafo

---

## 13. ACTIVAR ENVÍO REAL EN PRODUCCIÓN

Una vez validada la autenticación y el envío, la aplicación está lista para:

1. **Ejecutarse mensualmente:**
   - Obtiene roadmap de MRC MCP
   - Filtra por productos
   - Genera HTML
   - **Envía email real** mediante Microsoft Graph

2. **Integración en workflow:**
   - Modificar `src/email_sender.py` para usar `GraphEmailSender` en lugar de SMTP
   - O crear nuevo flujo exclusivo para Graph API
   - Actualizar `main_workflow.py` para invocar el nuevo código

3. **Automatización:**
   - Windows Task Scheduler (ver `EJECUCION_AUTOMATICA_MENSUAL.md`)
   - O Linux cron equivalente

---

## 14. SOLUCIÓN DE PROBLEMAS

### Error: "AADSTS700016: Application with identifier was not found"

**Causa:** Client ID incorrecto o aplicación no registrada

**Solución:**
1. Verifica que `OAUTH_CLIENT_ID` en `.env` sea exacto
2. Ve a Azure Portal → App registrations → tu app
3. Copia nuevamente el Client ID
4. Actualiza `.env`

### Error: "AADSTS65001: User or admin has not consented to use application"

**Causa:** El usuario no ha aceptado los permisos

**Solución:**
1. Ejecuta nuevamente: `python test_m365_oauth_diagnosis.py`
2. Se abrirá el navegador
3. Acepta los permisos en la pantalla de consentimiento

### Error: "Invalid redirect_uri"

**Causa:** Redirect URI no coincide entre .env y Azure

**Solución:**
1. En Azure Portal, verifica que `http://localhost` esté configurado en Authentication
2. En `.env`, asegúrate que `OAUTH_REDIRECT_URI=http://localhost`
3. No incluir puerto específico (MSAL asigna uno dinámicamente)

### Error: "The user has not consented to Mail.Send permission"

**Causa:** Permiso Mail.Send no asignado a la app

**Solución:**
1. Ve a Azure Portal → tu app registration → API permissions
2. Verifica que "Mail.Send" esté en la lista
3. Si no está, haz clic en "+ Add a permission"
4. Microsoft Graph → Delegated → Mail.Send → Add
5. Ejecuta nuevamente el diagnóstico y acepta permisos

### Token Expirado Después de 90 Días

**Síntoma:** Error 401 Unauthorized en primer intento del mes 4+

**Solución:**
```bash
python test_m365_oauth_diagnosis.py --reauth
```

Esto fuerza un login interactivo nuevo, actualiza el cache y reinicia el ciclo de 90 días.

---

## 15. CONSIDERACIONES DE SEGURIDAD

### ✅ SEGURO

- ✅ Tokens almacenados en cache encriptado (MSAL maneja encriptación)
- ✅ Token cache con permisos 0600 (solo usuario puede leer)
- ✅ Sin Client Secret en código (no se usa en desktop apps)
- ✅ Sin contraseñas en .env
- ✅ Permisos delegados (Mail.Send únicamente)
- ✅ Redirect URI local (http://localhost)

### ⚠️ PRECAUCIONES

- ⚠️ Token cache en `~/.m365_roadmap/` → Asegura que directorio está protegido
- ⚠️ `.env` nunca debe commitearse a control de versiones
- ⚠️ No compartir valores de CLIENT_ID o TENANT_ID públicamente
- ⚠️ No ejecutar script con permisos "Run as Administrator" innecesariamente

### 🔐 MEJOR PRÁCTICA

```bash
# Proteger el directorio de cache de tokens
chmod 700 ~/.m365_roadmap
```

---

## 16. ARQUITECTURA ACTUAL vs. ANTERIOR

### ❌ ARQUITECTURA ANTERIOR (DESCARTADA)

```
SMTP Básico (smtp.office365.com:587)
    ↓
Autenticación: usuario@empresa.com + contraseña de aplicación
    ↓
Ventajas: Simple
    ↓
Desventajas:
  - Menor seguridad
  - Contraseña en .env
  - No permite offline_access
  - Problemas con autenticación multifactor
```

### ✅ ARQUITECTURA ACTUAL (OAUTH 2.0)

```
OAuth 2.0 + MSAL
    ↓
Autenticación: Login interactivo + consentimiento delegado
    ↓
Token Cache: Almacenamiento persistente y encriptado
    ↓
Microsoft Graph API: /me/sendMail
    ↓
Ventajas:
  - Mayor seguridad
  - Sin contraseñas
  - Offline access (90 días)
  - Compatible con MFA
  - Tokens automáticamente renovados
```

---

## 17. PRÓXIMOS PASOS

1. **Verificar permisos administrativos:**
   - ¿Tienes acceso a Microsoft Entra ID?
   - ¿Puedes registrar aplicaciones?

2. **Crear App Registration** (Paso 1-5 de esta guía)

3. **Obtener Client ID y Tenant ID**

4. **Actualizar `.env`**

5. **Ejecutar diagnóstico** (Paso 9)

6. **Validar envío de email** (Paso 10)

7. **Activar en workflow** (Paso 13)

8. **Automatizar ejecución mensual** (Ver `EJECUCION_AUTOMATICA_MENSUAL.md`)

---

## REFERENCIAS

- [Microsoft Entra ID](https://entra.microsoft.com/)
- [Microsoft Graph API - Send Mail](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0)
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [OAuth 2.0](https://oauth.net/2/)

---

**Fin del documento de configuración OAuth 2.0**
