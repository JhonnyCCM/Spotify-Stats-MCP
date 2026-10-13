# 🎵 Spotify Stats & Activity (MCP Server + Web Dashboard)

Servidor **Model Context Protocol (MCP)** y **Dashboard Web** con tema oscuro estilo Spotify para visualizar y consultar tus estadísticas musicales, reproducciones en vivo y hábitos de escucha en tiempo real.

---

## ✨ Características

* 🟢 **Reproductor en vivo (Live Now Playing):** Muestra qué canción estás escuchando en directo, con barra de progreso segundo a segundo y dispositivo de reproducción.
* 🏆 **Top Canciones y Top Artistas:**
  * 1 Semana (7 días)
  * Último Mes (4 semanas)
  * Últimos 6 Meses
  * De por Vida (All-Time)
  * Rango Personalizado con selector de fechas (calendario).
* 🔲 **3 Vistas Interactivas (Layouts):**
  * 📋 Modo Lista
  * ▥ Modo 2 Columnas
  * ⊞ Modo Cuadrícula (Mosaico de portadas)
* 🕒 **Historial Reciente auto-actualizable:** Detecta cambios de canción y sincroniza automáticamente los temas que acabas de escuchar.
* 📁 **Tus Playlists:** Consulta directa de tus listas guardadas en Spotify.
* 🤖 **Servidor MCP nativo:** Permite a asistentes de Inteligencia Artificial (Antigravity, Claude, etc.) consultar tus estadísticas mediante herramientas en lenguaje natural.

---

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/JhonnyCCM/Spotify-Stats-MCP.git
cd Spotify-Stats-MCP
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv .venv

# En Windows:
.venv\Scripts\activate

# En Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Obtener credenciales de Spotify
1. Ve al [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Haz clic en **Create app**:
   * **App name:** `Spotify Stats MCP` (o el que gustes).
   * **Redirect URIs:** `http://127.0.0.1:8888/callback` *(Asegúrate de pulsar Add y guardar)*.
   * **Which API/SDKs are you planning to use?:** Marca **Web API**.
3. En los **Settings** de tu app, copia tu **Client ID** y haz clic en **View client secret** para copiar tu **Client Secret**.

### 4. Configurar variables de entorno
Crea un archivo llamado `.env` basándote en `.env.example`:
```env
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### 5. Autorización única (OAuth)
Ejecuta el script de inicio de sesión:
```bash
python auth.py
```
Se abrirá tu navegador para que inicies sesión en Spotify y hagas clic en **Aceptar**. Una vez concedido el permiso, tu sesión permanente se guardará localmente en `.cache`. ¡No tendrás que volver a loguearte!

---

## 🖥️ Uso del Dashboard Web

Para abrir la interfaz gráfica en tu navegador:
```bash
python app.py
```
O en Windows simplemente haz doble clic en `start_dashboard.bat`.

Abre en tu navegador: **`http://localhost:5000`**

---

## 🤖 Uso como Servidor MCP

Para usar las herramientas con asistentes de IA compatibles con el Model Context Protocol, agrega la configuración a tu archivo `mcp_config.json`:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "python",
      "args": ["/ruta/absoluta/a/Spotify-Stats-MCP/server.py"]
    }
  }
}
```

### Herramientas MCP expuestas:
* `get_currently_playing`: Canción reproduciéndose en vivo y dispositivo.
* `get_user_profile`: Perfil del usuario, ID, avatar y seguidores.
* `get_top_tracks`: Canciones más escuchadas por período (`short_term`, `medium_term`, `long_term`).
* `get_top_artists`: Artistas más escuchados por período.
* `get_recently_played`: Canciones reproducidas recientemente con marcas de tiempo.
* `get_user_playlists`: Listas de reproducción del usuario.
* `get_music_profile_summary`: Reporte de evolución musical consolidado.

---

## 🔒 Privacidad y Seguridad
* Tus credenciales de Spotify y tokens de sesión (`.env`, `.cache`) y tu base de datos local (`history.db`) están protegidos en `.gitignore` y **nunca** se suben al repositorio.
* La comunicación se realiza exclusivamente entre tu máquina local y los servidores oficiales de Spotify.

---

## 📄 Licencia
MIT
