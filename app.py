"""
Spotify Stats Web Dashboard
Interfaz gráfica web avanzada para estadísticas y actividad de Spotify.
Soporta vistas (Lista, 2 Columnas, Cuadrícula) y rangos temporales (1 semana, personalizado, mensual, semestral, all-time).
"""

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import uvicorn

import server
import database

app = FastAPI(title="Spotify Stats Dashboard")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spotify Stats Dashboard | JhonnyCM</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            spotify: {
              green: '#1DB954',
              greenHover: '#1ed760',
              dark: '#121212',
              card: '#181818',
              cardHover: '#282828',
              subtext: '#b3b3b3',
              border: '#2a2a2a'
            }
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .custom-scrollbar::-webkit-scrollbar { width: 8px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: #121212; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #282828; border-radius: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #3e3e3e; }
  </style>
</head>
<body class="bg-black text-white min-h-screen custom-scrollbar selection:bg-spotify-green selection:text-black">

  <!-- TOP NAVIGATION / HEADER -->
  <header class="sticky top-0 z-50 backdrop-blur-xl bg-black/80 border-b border-spotify-border px-6 py-4">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-spotify-green flex items-center justify-center text-black text-xl shadow-lg shadow-spotify-green/20">
          <i class="fa-brands fa-spotify"></i>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight flex items-center gap-2">
            Spotify Stats
            <span class="text-xs px-2 py-0.5 rounded-full bg-spotify-green/10 text-spotify-green border border-spotify-green/30 font-medium">MCP Live</span>
          </h1>
          <p class="text-xs text-spotify-subtext">Estadísticas personales en tiempo real</p>
        </div>
      </div>

      <!-- PERFIL DE USUARIO -->
      <div id="user-profile-badge" class="flex items-center gap-3 bg-spotify-card border border-spotify-border hover:border-spotify-green/40 transition-all rounded-full px-3 py-1.5">
        <div class="w-8 h-8 rounded-full overflow-hidden bg-zinc-800 flex items-center justify-center">
          <img id="user-avatar" src="" alt="Avatar" class="w-full h-full object-cover hidden">
          <i id="user-avatar-placeholder" class="fa-solid fa-user text-xs text-zinc-400"></i>
        </div>
        <div class="text-left">
          <a id="user-name" href="#" target="_blank" class="text-xs font-bold hover:text-spotify-green block leading-tight">Cargando...</a>
          <span id="user-followers" class="text-[10px] text-spotify-subtext">0 seguidores</span>
        </div>
        <a id="user-link" href="#" target="_blank" class="text-xs text-spotify-subtext hover:text-white ml-1">
          <i class="fa-solid fa-arrow-up-right-from-square"></i>
        </a>
      </div>
    </div>
  </header>

  <!-- CONTENIDO PRINCIPAL -->
  <main class="max-w-7xl mx-auto px-6 py-8">
    
    <!-- NOW PLAYING BANNER (LIVE WIDGET) -->
    <div id="now-playing-banner" class="mb-8 p-4 rounded-2xl bg-gradient-to-r from-zinc-900 via-spotify-card to-zinc-900 border border-spotify-border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all shadow-xl">
      <div class="flex items-center gap-4 min-w-0">
        <div class="relative flex-shrink-0">
          <img id="np-cover" src="https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?w=100" class="w-14 h-14 rounded-xl object-cover shadow-lg border border-zinc-800">
          <span id="np-pulse" class="hidden absolute -top-1 -right-1 w-3 h-3 bg-spotify-green rounded-full animate-ping"></span>
          <span id="np-dot" class="hidden absolute -top-1 -right-1 w-3 h-3 bg-spotify-green rounded-full"></span>
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span id="np-badge" class="text-[10px] uppercase tracking-wider font-extrabold text-zinc-400 flex items-center gap-1.5">
              <i class="fa-solid fa-circle text-[7px] text-zinc-500"></i>
              <span id="np-status-text">Sin reproducción activa</span>
            </span>
            <span id="np-device" class="text-[10px] text-zinc-500"></span>
          </div>
          <a id="np-song" href="#" target="_blank" class="font-bold text-sm md:text-base text-white hover:text-spotify-green transition-colors truncate block">
            Pon algo de música en Spotify
          </a>
          <p id="np-artists" class="text-xs text-spotify-subtext truncate">El reproductor se actualizará en vivo aquí</p>
        </div>
      </div>

      <!-- BARRA DE PROGRESO DE LA CANCIÓN -->
      <div id="np-progress-box" class="hidden sm:w-72 flex flex-col gap-1.5 flex-shrink-0">
        <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
          <div id="np-progress-bar" class="bg-spotify-green h-full rounded-full transition-all duration-1000" style="width: 0%"></div>
        </div>
        <div class="flex justify-between text-[10px] text-zinc-400 font-medium">
          <span id="np-time-curr">0:00</span>
          <span id="np-time-total">0:00</span>
        </div>
      </div>
    </div>

    <!-- CONTROLES, SELECTORES Y SELECTOR DE VISTAS (LAYOUT) -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
      
      <!-- PERIOD SELECTOR (Pills) -->
      <div class="flex flex-wrap items-center p-1 bg-spotify-card rounded-xl border border-spotify-border gap-1">
        <button onclick="setTimeRange('week_7d')" id="btn-week" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-spotify-subtext hover:text-white transition-all">
          <i class="fa-solid fa-calendar-week mr-1"></i>1 Semana (7d)
        </button>
        <button onclick="setTimeRange('short_term')" id="btn-short" class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all bg-spotify-green text-black shadow-md">
          <i class="fa-solid fa-bolt mr-1"></i>Último Mes (4 sem)
        </button>
        <button onclick="setTimeRange('medium_term')" id="btn-medium" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-spotify-subtext hover:text-white transition-all">
          <i class="fa-solid fa-calendar mr-1"></i>Últimos 6 Meses
        </button>
        <button onclick="setTimeRange('long_term')" id="btn-long" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-spotify-subtext hover:text-white transition-all">
          <i class="fa-solid fa-crown mr-1"></i>De por Vida
        </button>
        <button onclick="toggleCustomDates()" id="btn-custom" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-spotify-subtext hover:text-white transition-all">
          <i class="fa-solid fa-calendar-days mr-1"></i>Por Fechas
        </button>
      </div>

      <!-- LAYOUT SWITCHER & BUSCADOR -->
      <div class="flex items-center gap-3">
        
        <!-- SELECTOR DE VISTA (LISTA / 2 COLUMNAS / CUADRÍCULA) -->
        <div class="flex items-center bg-spotify-card p-1 rounded-xl border border-spotify-border">
          <button onclick="setLayout('list')" id="layout-list" title="Vista Lista" class="w-8 h-8 rounded-lg flex items-center justify-center text-xs text-spotify-subtext hover:text-white transition-all">
            <i class="fa-solid fa-bars"></i>
          </button>
          <button onclick="setLayout('two_cols')" id="layout-two_cols" title="Vista 2 Columnas" class="w-8 h-8 rounded-lg flex items-center justify-center text-xs bg-zinc-800 text-white font-bold transition-all">
            <i class="fa-solid fa-table-columns"></i>
          </button>
          <button onclick="setLayout('grid')" id="layout-grid" title="Vista Cuadrícula" class="w-8 h-8 rounded-lg flex items-center justify-center text-xs text-spotify-subtext hover:text-white transition-all">
            <i class="fa-solid fa-grip"></i>
          </button>
        </div>

        <!-- BUSCADOR -->
        <div class="relative">
          <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-xs text-zinc-400"></i>
          <input type="text" id="search-filter" oninput="filterContent()" placeholder="Filtrar canciones o artistas..." class="bg-spotify-card border border-spotify-border focus:border-spotify-green text-xs rounded-xl pl-8 pr-4 py-2 text-white placeholder-zinc-500 outline-none w-44 md:w-56 transition-all">
        </div>

        <!-- BOTÓN REFRESCAR -->
        <button onclick="fetchAllData()" title="Refrescar datos" class="w-9 h-9 rounded-xl bg-spotify-card border border-spotify-border hover:border-spotify-green flex items-center justify-center text-xs text-zinc-300 hover:text-white transition-all">
          <i id="refresh-icon" class="fa-solid fa-rotate-right"></i>
        </button>
      </div>
    </div>

    <!-- PANEL DE SELECCIÓN DE FECHAS PERSONALIZADAS (DESPLEGABLE) -->
    <div id="custom-date-panel" class="hidden mb-6 p-4 rounded-xl bg-spotify-card border border-spotify-border flex flex-wrap items-center gap-4 text-xs">
      <div class="flex items-center gap-2">
        <span class="text-spotify-subtext font-medium">Desde:</span>
        <input type="date" id="date-start" class="bg-zinc-900 border border-zinc-700 text-white rounded-lg px-2.5 py-1.5 outline-none focus:border-spotify-green">
      </div>
      <div class="flex items-center gap-2">
        <span class="text-spotify-subtext font-medium">Hasta:</span>
        <input type="date" id="date-end" class="bg-zinc-900 border border-zinc-700 text-white rounded-lg px-2.5 py-1.5 outline-none focus:border-spotify-green">
      </div>
      <button onclick="applyCustomDates()" class="px-4 py-1.5 rounded-lg bg-spotify-green text-black font-bold hover:bg-spotify-greenHover transition-all">
        Consultar Período
      </button>
      <span class="text-[11px] text-zinc-500 italic">* Datos calculados con exactitud de minutos desde tu historial local.</span>
    </div>

    <!-- SECCIÓN TABS DE VISTA -->
    <div class="flex border-b border-spotify-border mb-8 gap-8 text-sm font-semibold">
      <button onclick="switchTab('tracks')" id="tab-tracks" class="pb-3 border-b-2 border-spotify-green text-white flex items-center gap-2 transition-all">
        <i class="fa-solid fa-music text-spotify-green"></i> Top Canciones
      </button>
      <button onclick="switchTab('artists')" id="tab-artists" class="pb-3 border-b-2 border-transparent text-spotify-subtext hover:text-white flex items-center gap-2 transition-all">
        <i class="fa-solid fa-users"></i> Top Artistas
      </button>
      <button onclick="switchTab('recent')" id="tab-recent" class="pb-3 border-b-2 border-transparent text-spotify-subtext hover:text-white flex items-center gap-2 transition-all">
        <i class="fa-solid fa-clock-rotate-left"></i> Escuchado Reciente
      </button>
      <button onclick="switchTab('playlists')" id="tab-playlists" class="pb-3 border-b-2 border-transparent text-spotify-subtext hover:text-white flex items-center gap-2 transition-all">
        <i class="fa-solid fa-list-ul"></i> Tus Playlists
      </button>
    </div>

    <!-- SPINNER CARGANDO -->
    <div id="loading" class="flex flex-col items-center justify-center py-20 gap-4">
      <div class="w-12 h-12 border-4 border-spotify-green/20 border-t-spotify-green rounded-full animate-spin"></div>
      <p class="text-sm text-spotify-subtext font-medium">Consultando Spotify...</p>
    </div>

    <!-- VISTA 1: TOP TRACKS -->
    <section id="view-tracks" class="hidden">
      <div id="tracks-container" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
    </section>

    <!-- VISTA 2: TOP ARTISTS -->
    <section id="view-artists" class="hidden">
      <div id="artists-container" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"></div>
    </section>

    <!-- VISTA 3: ESCUCHADO RECIENTE -->
    <section id="view-recent" class="hidden">
      <div id="recent-container" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
    </section>

    <!-- VISTA 4: PLAYLISTS -->
    <section id="view-playlists" class="hidden">
      <div id="playlists-container" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"></div>
    </section>

  </main>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    let currentTimeRange = 'short_term';
    let currentTab = 'tracks';
    let currentLayout = localStorage.getItem('spotify_dashboard_layout') || 'two_cols';
    let customDates = { start: null, end: null };
    let lastSongTitle = null;

    let rawData = {
      tracks: [],
      artists: [],
      recent: [],
      playlists: []
    };

    // MAPEO DE CLASES CSS SEGÚN LAYOUT
    const layoutClasses = {
      tracks: {
        list: 'grid grid-cols-1 gap-2',
        two_cols: 'grid grid-cols-1 md:grid-cols-2 gap-3',
        grid: 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
      },
      artists: {
        list: 'grid grid-cols-1 gap-2',
        two_cols: 'grid grid-cols-1 md:grid-cols-2 gap-3',
        grid: 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
      },
      recent: {
        list: 'grid grid-cols-1 gap-2',
        two_cols: 'grid grid-cols-1 md:grid-cols-2 gap-3',
        grid: 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
      },
      playlists: {
        list: 'grid grid-cols-1 gap-2',
        two_cols: 'grid grid-cols-1 md:grid-cols-2 gap-3',
        grid: 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
      }
    };

    function setLayout(layout) {
      currentLayout = layout;
      localStorage.setItem('spotify_dashboard_layout', layout);

      ['list', 'two_cols', 'grid'].forEach(l => {
        const btn = document.getElementById(`layout-${l}`);
        if (l === layout) {
          btn.className = "w-8 h-8 rounded-lg flex items-center justify-center text-xs bg-zinc-800 text-white font-bold transition-all border border-zinc-700";
        } else {
          btn.className = "w-8 h-8 rounded-lg flex items-center justify-center text-xs text-spotify-subtext hover:text-white transition-all";
        }
      });

      // Actualizar clases de contenedores
      document.getElementById('tracks-container').className = layoutClasses.tracks[layout];
      document.getElementById('artists-container').className = layoutClasses.artists[layout];
      document.getElementById('recent-container').className = layoutClasses.recent[layout];
      document.getElementById('playlists-container').className = layoutClasses.playlists[layout];

      // Re-renderizar para ajustar diseño de tarjetas
      renderTracks(rawData.tracks);
      renderArtists(rawData.artists);
      renderRecent(rawData.recent);
      renderPlaylists(rawData.playlists);
    }

    async function fetchAllData() {
      const loader = document.getElementById('loading');
      const refreshIcon = document.getElementById('refresh-icon');
      loader.classList.remove('hidden');
      refreshIcon.classList.add('animate-spin');

      try {
        // Cargar perfil
        fetch('/api/profile').then(r => r.json()).then(user => {
          document.getElementById('user-name').innerText = user.display_name || 'Usuario';
          document.getElementById('user-name').href = user.profile_url || '#';
          document.getElementById('user-link').href = user.profile_url || '#';
          document.getElementById('user-followers').innerText = `${user.followers} seguidores`;
          if (user.avatar_url) {
            const img = document.getElementById('user-avatar');
            img.src = user.avatar_url;
            img.classList.remove('hidden');
            document.getElementById('user-avatar-placeholder').classList.add('hidden');
          }
        });

        let tracksData = [];
        let artistsData = [];

        // Si es 1 semana o rango personalizado -> consultar endpoint de historial local
        if (currentTimeRange === 'week_7d' || currentTimeRange === 'custom') {
          let url = '/api/custom-stats';
          if (currentTimeRange === 'week_7d') {
            const d = new Date();
            d.setDate(d.getDate() - 7);
            url += `?start_date=${encodeURIComponent(d.toISOString())}`;
          } else if (currentTimeRange === 'custom' && customDates.start) {
            url += `?start_date=${encodeURIComponent(new Date(customDates.start).toISOString())}`;
            if (customDates.end) {
              const endDate = new Date(customDates.end);
              endDate.setHours(23, 59, 59);
              url += `&end_date=${encodeURIComponent(endDate.toISOString())}`;
            }
          }

          const statsRes = await fetch(url).then(r => r.json());
          tracksData = statsRes.top_canciones || [];
          artistsData = statsRes.top_artistas || [];
        } else {
          // Rangos estándar Spotify API
          const [tRes, aRes] = await Promise.all([
            fetch(`/api/top-tracks?time_range=${currentTimeRange}&limit=30`).then(r => r.json()),
            fetch(`/api/top-artists?time_range=${currentTimeRange}&limit=30`).then(r => r.json())
          ]);
          tracksData = tRes;
          artistsData = aRes;
        }

        const [recentRes, playlistsRes] = await Promise.all([
          fetch('/api/recently-played?limit=30').then(r => r.json()),
          fetch('/api/playlists?limit=30').then(r => r.json())
        ]);

        rawData.tracks = tracksData;
        rawData.artists = artistsData;
        rawData.recent = recentRes;
        rawData.playlists = playlistsRes;

        renderTracks(rawData.tracks);
        renderArtists(rawData.artists);
        renderRecent(rawData.recent);
        renderPlaylists(rawData.playlists);

      } catch (err) {
        console.error("Error fetching data:", err);
      } finally {
        loader.classList.add('hidden');
        refreshIcon.classList.remove('animate-spin');
        switchTab(currentTab);
      }
    }

    function renderTracks(tracks) {
      const container = document.getElementById('tracks-container');
      container.innerHTML = '';
      if (!tracks || tracks.length === 0) {
        container.innerHTML = '<p class="text-zinc-500 text-sm col-span-full text-center py-10">No se encontraron canciones en este rango.</p>';
        return;
      }
      tracks.forEach(track => {
        const cover = track.cover_url || 'https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?w=100';
        const card = document.createElement('div');
        
        // Renderizado según modo de vista
        if (currentLayout === 'grid') {
          card.className = "flex flex-col p-3 rounded-2xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group relative";
          card.innerHTML = `
            <span class="absolute top-2 left-2 text-xs font-black w-6 h-6 rounded-full flex items-center justify-center ${track.puesto <= 3 ? 'bg-spotify-green text-black' : 'bg-black/60 text-zinc-400 border border-zinc-700'}">
              ${track.puesto}
            </span>
            <div class="w-full aspect-square rounded-xl overflow-hidden shadow-md mb-2 relative">
              <img src="${cover}" alt="Cover" class="w-full h-full object-cover">
              <a href="${track.spotify_url}" target="_blank" class="absolute bottom-2 right-2 w-9 h-9 rounded-full bg-spotify-green text-black opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center shadow-lg hover:scale-105">
                <i class="fa-solid fa-play text-xs pl-0.5"></i>
              </a>
            </div>
            <a href="${track.spotify_url}" target="_blank" class="font-bold text-xs text-white hover:text-spotify-green transition-colors truncate block">
              ${track.cancion}
            </a>
            <p class="text-[11px] text-spotify-subtext truncate mt-0.5">${track.artistas}</p>
            <span class="text-[10px] text-zinc-500 mt-1">${track.duracion || ''}</span>
          `;
        } else {
          // Lista o 2 Columnas
          card.className = "flex items-center justify-between p-3 rounded-xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group";
          card.innerHTML = `
            <div class="flex items-center gap-3 min-w-0">
              <span class="text-sm font-bold w-6 text-center ${track.puesto <= 3 ? 'text-spotify-green' : 'text-zinc-500'}">${track.puesto}</span>
              <img src="${cover}" alt="Cover" class="w-12 h-12 rounded-lg object-cover shadow flex-shrink-0">
              <div class="min-w-0">
                <a href="${track.spotify_url}" target="_blank" class="font-bold text-sm text-white hover:text-spotify-green transition-colors truncate block">
                  ${track.cancion}
                </a>
                <p class="text-xs text-spotify-subtext truncate">${track.artistas}</p>
                <p class="text-[10px] text-zinc-500 truncate mt-0.5">${track.album || ''} ${track.fecha_lanzamiento ? `• ${track.fecha_lanzamiento.split('-')[0]}` : ''}</p>
              </div>
            </div>
            <div class="flex items-center gap-3 pl-3 flex-shrink-0">
              <span class="text-xs text-zinc-400 font-medium">${track.duracion || ''}</span>
              <a href="${track.spotify_url}" target="_blank" class="w-9 h-9 rounded-full bg-spotify-green text-black opacity-0 group-hover:opacity-100 transform scale-90 group-hover:scale-100 transition-all flex items-center justify-center shadow-lg hover:bg-spotify-greenHover">
                <i class="fa-solid fa-play text-xs pl-0.5"></i>
              </a>
            </div>
          `;
        }
        container.appendChild(card);
      });
    }

    function renderArtists(artists) {
      const container = document.getElementById('artists-container');
      container.innerHTML = '';
      if (!artists || artists.length === 0) {
        container.innerHTML = '<p class="text-zinc-500 text-sm col-span-full text-center py-10">No se encontraron artistas en este rango.</p>';
        return;
      }
      artists.forEach(artist => {
        const photo = artist.foto_url || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=200';
        const card = document.createElement('a');
        card.href = artist.spotify_url;
        card.target = "_blank";
        
        if (currentLayout === 'list') {
          card.className = "flex items-center justify-between p-3 rounded-xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group";
          card.innerHTML = `
            <div class="flex items-center gap-3 min-w-0">
              <span class="text-sm font-bold w-6 text-center ${artist.puesto <= 3 ? 'text-spotify-green' : 'text-zinc-500'}">#${artist.puesto}</span>
              <img src="${photo}" alt="${artist.artista}" class="w-11 h-11 rounded-full object-cover shadow flex-shrink-0">
              <div class="min-w-0">
                <h3 class="font-bold text-sm text-white group-hover:text-spotify-green transition-colors truncate">${artist.artista}</h3>
                <span class="text-[11px] text-spotify-subtext">Artista</span>
              </div>
            </div>
            <i class="fa-solid fa-chevron-right text-xs text-zinc-600 group-hover:text-white transition-colors pr-2"></i>
          `;
        } else if (currentLayout === 'two_cols') {
          card.className = "flex items-center gap-4 p-3.5 rounded-2xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group";
          card.innerHTML = `
            <span class="text-sm font-bold w-5 text-center ${artist.puesto <= 3 ? 'text-spotify-green' : 'text-zinc-500'}">#${artist.puesto}</span>
            <img src="${photo}" alt="${artist.artista}" class="w-14 h-14 rounded-full object-cover shadow-lg flex-shrink-0 group-hover:scale-105 transition-transform">
            <div class="min-w-0 flex-1">
              <h3 class="font-bold text-sm text-white group-hover:text-spotify-green transition-colors truncate">${artist.artista}</h3>
              <span class="text-xs text-spotify-subtext block mt-0.5">Artista</span>
            </div>
            <i class="fa-solid fa-chevron-right text-xs text-zinc-600 group-hover:text-white transition-colors pr-2"></i>
          `;
        } else {
          // Cuadrícula (Grid)
          card.className = "flex flex-col items-center p-4 rounded-2xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group text-center relative";
          card.innerHTML = `
            <span class="absolute top-3 left-3 text-xs font-extrabold w-6 h-6 rounded-full flex items-center justify-center ${artist.puesto <= 3 ? 'bg-spotify-green text-black shadow-md shadow-spotify-green/30' : 'bg-black/60 text-zinc-400 border border-zinc-700'}">
              #${artist.puesto}
            </span>
            <div class="w-24 h-24 sm:w-28 sm:h-28 rounded-full overflow-hidden my-2 shadow-lg group-hover:scale-105 transition-transform">
              <img src="${photo}" alt="${artist.artista}" class="w-full h-full object-cover">
            </div>
            <h3 class="font-bold text-sm text-white group-hover:text-spotify-green transition-colors mt-1 line-clamp-1">${artist.artista}</h3>
            <span class="text-[11px] text-spotify-subtext mt-0.5">Artista</span>
          `;
        }
        container.appendChild(card);
      });
    }

    function renderRecent(recent) {
      const container = document.getElementById('recent-container');
      container.innerHTML = '';
      if (!recent || recent.length === 0) {
        container.innerHTML = '<p class="text-zinc-500 text-sm col-span-full text-center py-10">No hay actividad reciente registrada.</p>';
        return;
      }
      recent.forEach((item, index) => {
        const cover = item.cover_url || 'https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?w=100';
        const playedDate = new Date(item.reproducido_el);
        const timeAgo = formatTimeAgo(playedDate);
        const card = document.createElement('div');
        
        if (currentLayout === 'grid') {
          card.className = "flex flex-col p-3 rounded-2xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group";
          card.innerHTML = `
            <div class="w-full aspect-square rounded-xl overflow-hidden shadow-md mb-2">
              <img src="${cover}" alt="Cover" class="w-full h-full object-cover">
            </div>
            <a href="${item.spotify_url}" target="_blank" class="font-bold text-xs text-white hover:text-spotify-green transition-colors truncate block">
              ${item.cancion}
            </a>
            <p class="text-[11px] text-spotify-subtext truncate mt-0.5">${item.artistas}</p>
            <span class="text-[10px] text-spotify-green font-semibold mt-1">${timeAgo}</span>
          `;
        } else {
          card.className = "flex items-center justify-between p-3 rounded-xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group";
          card.innerHTML = `
            <div class="flex items-center gap-3 min-w-0">
              <img src="${cover}" alt="Cover" class="w-12 h-12 rounded-lg object-cover shadow flex-shrink-0">
              <div class="min-w-0">
                <a href="${item.spotify_url}" target="_blank" class="font-bold text-sm text-white hover:text-spotify-green transition-colors truncate block">
                  ${item.cancion}
                </a>
                <p class="text-xs text-spotify-subtext truncate">${item.artistas}</p>
                <p class="text-[10px] text-zinc-500 truncate mt-0.5">${item.album || ''}</p>
              </div>
            </div>
            <div class="text-right flex-shrink-0 pl-3">
              <span class="text-[11px] text-spotify-green font-medium block">${timeAgo}</span>
              <span class="text-[9px] text-zinc-500">${playedDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
          `;
        }
        container.appendChild(card);
      });
    }

    function renderPlaylists(playlists) {
      const container = document.getElementById('playlists-container');
      container.innerHTML = '';
      if (!playlists || playlists.length === 0) {
        container.innerHTML = '<p class="text-zinc-500 text-sm col-span-full text-center py-10">No se encontraron playlists.</p>';
        return;
      }
      playlists.forEach(pl => {
        const cover = pl.cover_url || 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=200';
        const card = document.createElement('a');
        card.href = pl.spotify_url;
        card.target = "_blank";

        if (currentLayout === 'list') {
          card.className = "flex items-center justify-between p-3 rounded-xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group";
          card.innerHTML = `
            <div class="flex items-center gap-3 min-w-0">
              <img src="${cover}" alt="${pl.nombre}" class="w-12 h-12 rounded-lg object-cover shadow flex-shrink-0">
              <div class="min-w-0">
                <h3 class="font-bold text-sm text-white group-hover:text-spotify-green transition-colors truncate">${pl.nombre}</h3>
                <span class="text-xs text-spotify-subtext">${pl.total_canciones} canciones</span>
              </div>
            </div>
            <i class="fa-solid fa-arrow-up-right-from-square text-xs text-zinc-600 group-hover:text-white transition-colors pr-2"></i>
          `;
        } else {
          card.className = "flex flex-col p-4 rounded-2xl bg-spotify-card hover:bg-spotify-cardHover border border-spotify-border hover:border-zinc-700 transition-all group text-left";
          card.innerHTML = `
            <div class="w-full aspect-square rounded-xl overflow-hidden shadow-lg mb-3 group-hover:scale-102 transition-transform">
              <img src="${cover}" alt="${pl.nombre}" class="w-full h-full object-cover">
            </div>
            <h3 class="font-bold text-sm text-white group-hover:text-spotify-green transition-colors line-clamp-1">${pl.nombre}</h3>
            <span class="text-xs text-spotify-subtext mt-1">${pl.total_canciones} canciones</span>
          `;
        }
        container.appendChild(card);
      });
    }

    function setTimeRange(range) {
      currentTimeRange = range;
      document.getElementById('custom-date-panel').classList.add('hidden');

      const btnMap = {
        'week_7d': 'btn-week',
        'short_term': 'btn-short',
        'medium_term': 'btn-medium',
        'long_term': 'btn-long',
        'custom': 'btn-custom'
      };

      Object.entries(btnMap).forEach(([k, btnId]) => {
        const btn = document.getElementById(btnId);
        if (k === range) {
          btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all bg-spotify-green text-black shadow-md";
        } else {
          btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold text-spotify-subtext hover:text-white transition-all";
        }
      });

      fetchAllData();
    }

    function toggleCustomDates() {
      const panel = document.getElementById('custom-date-panel');
      panel.classList.toggle('hidden');
      if (!panel.classList.contains('hidden')) {
        // Inicializar fechas por defecto (hace 7 días a hoy)
        const today = new Date().toISOString().split('T')[0];
        const past = new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0];
        document.getElementById('date-start').value = past;
        document.getElementById('date-end').value = today;
      }
    }

    function applyCustomDates() {
      const s = document.getElementById('date-start').value;
      const e = document.getElementById('date-end').value;
      if (!s) return alert("Selecciona una fecha de inicio");
      customDates.start = s;
      customDates.end = e || null;
      setTimeRange('custom');
    }

    function switchTab(tab) {
      currentTab = tab;
      const tabs = ['tracks', 'artists', 'recent', 'playlists'];
      tabs.forEach(t => {
        const view = document.getElementById(`view-${t}`);
        const tabBtn = document.getElementById(`tab-${t}`);
        if (t === tab) {
          view.classList.remove('hidden');
          tabBtn.className = "pb-3 border-b-2 border-spotify-green text-white flex items-center gap-2 transition-all";
        } else {
          view.classList.add('hidden');
          tabBtn.className = "pb-3 border-b-2 border-transparent text-spotify-subtext hover:text-white flex items-center gap-2 transition-all";
        }
      });
      if (tab === 'recent') {
        refreshRecent();
      }
    }

    function filterContent() {
      const q = document.getElementById('search-filter').value.toLowerCase().trim();
      if (!q) {
        renderTracks(rawData.tracks);
        renderArtists(rawData.artists);
        renderRecent(rawData.recent);
        renderPlaylists(rawData.playlists);
        return;
      }
      if (currentTab === 'tracks') {
        const filtered = rawData.tracks.filter(t => t.cancion.toLowerCase().includes(q) || t.artistas.toLowerCase().includes(q));
        renderTracks(filtered);
      } else if (currentTab === 'artists') {
        const filtered = rawData.artists.filter(a => a.artista.toLowerCase().includes(q));
        renderArtists(filtered);
      } else if (currentTab === 'recent') {
        const filtered = rawData.recent.filter(r => r.cancion.toLowerCase().includes(q) || r.artistas.toLowerCase().includes(q));
        renderRecent(filtered);
      } else if (currentTab === 'playlists') {
        const filtered = rawData.playlists.filter(p => p.nombre.toLowerCase().includes(q));
        renderPlaylists(filtered);
      }
    }

    function formatTimeAgo(date) {
      const diffSec = Math.floor((new Date() - date) / 1000);
      if (diffSec < 60) return "Justo ahora";
      const diffMin = Math.floor(diffSec / 60);
      if (diffMin < 60) return `Hace ${diffMin} min`;
      const diffHour = Math.floor(diffMin / 60);
      if (diffHour < 24) return `Hace ${diffHour}h`;
      const diffDays = Math.floor(diffHour / 24);
      return `Hace ${diffDays}d`;
    }

    async function refreshRecent() {
      try {
        const res = await fetch('/api/recently-played?limit=30');
        const items = await res.json();
        if (Array.isArray(items)) {
          rawData.recent = items;
          if (currentTab === 'recent') {
            renderRecent(rawData.recent);
          }
        }
      } catch (e) {
        console.error("Error refreshing recent:", e);
      }
    }

    // Consultar reproducción en vivo
    async function updateCurrentlyPlaying() {
      try {
        const res = await fetch('/api/currently-playing');
        const data = await res.json();
        
        const badge = document.getElementById('np-badge');
        const pulse = document.getElementById('np-pulse');
        const dot = document.getElementById('np-dot');
        const cover = document.getElementById('np-cover');
        const song = document.getElementById('np-song');
        const artists = document.getElementById('np-artists');
        const device = document.getElementById('np-device');
        const progBox = document.getElementById('np-progress-box');
        const progBar = document.getElementById('np-progress-bar');
        const timeCurr = document.getElementById('np-time-curr');
        const timeTotal = document.getElementById('np-time-total');

        if (data.is_playing) {
          if (data.cancion && data.cancion !== lastSongTitle) {
            lastSongTitle = data.cancion;
            refreshRecent();
          }

          pulse.classList.remove('hidden');
          dot.classList.remove('hidden');
          badge.className = "text-[10px] uppercase tracking-wider font-extrabold text-spotify-green flex items-center gap-1.5";
          badge.innerHTML = '<i class="fa-solid fa-headphones-simple animate-pulse"></i> <span>Escuchando ahora</span>';
          device.innerText = data.dispositivo ? `• En ${data.dispositivo}` : '';
          if (data.cover_url) cover.src = data.cover_url;
          song.innerText = data.cancion;
          song.href = data.spotify_url || '#';
          artists.innerText = `${data.artistas} • ${data.album}`;
          
          progBox.classList.remove('hidden');
          timeCurr.innerText = data.progreso;
          timeTotal.innerText = data.duracion;
          const pct = data.duration_ms > 0 ? (data.progress_ms / data.duration_ms) * 100 : 0;
          progBar.style.width = `${pct}%`;
        } else {
          pulse.classList.add('hidden');
          dot.classList.add('hidden');
          badge.className = "text-[10px] uppercase tracking-wider font-extrabold text-zinc-400 flex items-center gap-1.5";
          badge.innerHTML = '<i class="fa-solid fa-circle text-[7px] text-zinc-500"></i> <span>Sin reproducción activa</span>';
          device.innerText = '';
          song.innerText = 'Pon algo de música en Spotify';
          song.href = '#';
          artists.innerText = 'El reproductor se actualizará en vivo aquí';
          progBox.classList.add('hidden');
        }
      } catch (e) {
        console.error("Error polling currently-playing:", e);
      }
    }

    // Inicializar al cargar
    setLayout(currentLayout);
    fetchAllData();
    updateCurrentlyPlaying();
    setInterval(updateCurrentlyPlaying, 3000);
    setInterval(refreshRecent, 15000);
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/currently-playing")
def api_currently_playing():
    return server.get_currently_playing()

@app.get("/api/profile")
def api_profile():
    return server.get_user_profile()

@app.get("/api/top-tracks")
def api_top_tracks(time_range: str = "medium_term", limit: int = 20):
    return server.get_top_tracks(time_range=time_range, limit=limit)

@app.get("/api/top-artists")
def api_top_artists(time_range: str = "medium_term", limit: int = 20):
    return server.get_top_artists(time_range=time_range, limit=limit)

@app.get("/api/recently-played")
def api_recently_played(limit: int = 20):
    items = server.get_recently_played(limit=limit)
    # Guardar en SQLite local automáticamente
    try:
        database.save_recent_tracks(items)
    except Exception as e:
        print("Error saving to history DB:", e)
    return items

@app.get("/api/custom-stats")
def api_custom_stats(start_date: str | None = None, end_date: str | None = None):
    return database.get_stats_by_date_range(start_iso=start_date, end_iso=end_date)

@app.get("/api/playlists")
def api_playlists(limit: int = 20):
    return server.get_user_playlists(limit=limit)

@app.get("/api/summary")
def api_summary():
    return server.get_music_profile_summary()

if __name__ == "__main__":
    print("Iniciando Spotify Stats Dashboard en http://localhost:5000 ...")
    uvicorn.run(app, host="127.0.0.1", port=5000)
