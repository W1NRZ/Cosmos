/**
 * Cosmos web UI — communicates with Python via QWebChannel.
 */

(function () {
  "use strict";

  let backend = null;
  let library = [];
  let wallpaperStatus = {};
  let settings = {};
  let currentFilter = "all";
  let pendingSettings = null;

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  /* ── Bootstrap QWebChannel ── */
  function initBridge() {
    return new Promise((resolve) => {
      if (typeof qt === "undefined") {
        console.warn("QWebChannel unavailable — running in preview mode");
        backend = createMockBackend();
        resolve();
        return;
      }
      new QWebChannel(qt.webChannelTransport, (channel) => {
        backend = channel.objects.cosmos;
        resolve();
      });
    });
  }

  function createMockBackend() {
    return {
      getLibrary: () => JSON.stringify([]),
      getSettings: () => JSON.stringify(getDefaultSettings()),
      getWallpaperStatus: () => JSON.stringify({}),
      pickImportFiles: () => JSON.stringify({ ok: false, cancelled: true }),
      applyWallpaper: () => JSON.stringify({ ok: false }),
      removeItem: () => JSON.stringify({ ok: true }),
      renameItem: () => JSON.stringify({ ok: true }),
      saveSettings: (s) => JSON.stringify({ ok: true, settings: JSON.parse(s) }),
      resetSettings: () => JSON.stringify({ ok: true, settings: getDefaultSettings() }),
    };
  }

  function getDefaultSettings() {
    return {
      theme: {
        accent: "#6366f1",
        accentSoft: "rgba(99, 102, 241, 0.18)",
        background: "#0a0a0f",
        surface: "rgba(255, 255, 255, 0.04)",
        surfaceHover: "rgba(255, 255, 255, 0.08)",
        text: "#f4f4f5",
        textMuted: "#a1a1aa",
        border: "rgba(255, 255, 255, 0.08)",
      },
      layout: {
        radiusSm: "8px",
        radiusMd: "14px",
        radiusLg: "20px",
        radiusXl: "28px",
        spacing: "16px",
        gridGap: "18px",
      },
      controls: {
        buttonOpacity: "0.72",
        buttonBlur: "16px",
        cardOpacity: "0.55",
        animationSpeed: "0.35s",
        cornerStyle: "rounded",
      },
    };
  }

  /* ── Settings / CSS variables ── */
  function hexToRgba(hex, alpha) {
    const h = hex.replace("#", "");
    const r = parseInt(h.substring(0, 2), 16);
    const g = parseInt(h.substring(2, 4), 16);
    const b = parseInt(h.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function applySettings(s) {
    settings = s;
    const root = document.documentElement;
    const t = s.theme || {};
    const l = s.layout || {};
    const c = s.controls || {};

    root.style.setProperty("--accent", t.accent || "#6366f1");
    root.style.setProperty("--accent-soft", t.accentSoft || hexToRgba(t.accent || "#6366f1", 0.18));
    root.style.setProperty("--accent-glow", hexToRgba(t.accent || "#6366f1", 0.35));
    root.style.setProperty("--background", t.background || "#0a0a0f");
    root.style.setProperty("--surface", t.surface || "rgba(255,255,255,0.04)");
    root.style.setProperty("--surface-hover", t.surfaceHover || "rgba(255,255,255,0.08)");
    root.style.setProperty("--text", t.text || "#f4f4f5");
    root.style.setProperty("--text-muted", t.textMuted || "#a1a1aa");
    root.style.setProperty("--border", t.border || "rgba(255,255,255,0.08)");

    root.style.setProperty("--radius-sm", l.radiusSm || "8px");
    root.style.setProperty("--radius-md", l.radiusMd || "14px");
    root.style.setProperty("--radius-lg", l.radiusLg || "20px");
    root.style.setProperty("--radius-xl", l.radiusXl || "28px");
    root.style.setProperty("--spacing", l.spacing || "16px");
    root.style.setProperty("--grid-gap", l.gridGap || "18px");

    root.style.setProperty("--btn-opacity", c.buttonOpacity || "0.72");
    root.style.setProperty("--btn-blur", c.buttonBlur || "16px");
    root.style.setProperty("--card-opacity", c.cardOpacity || "0.55");
    root.style.setProperty("--anim-speed", c.animationSpeed || "0.35s");

    document.body.classList.remove("corner-sharp", "corner-soft", "corner-pill", "corner-rounded");
    const style = c.cornerStyle || "rounded";
    if (style !== "rounded") {
      document.body.classList.add(`corner-${style}`);
    }

    syncControlsFromSettings(s);
  }

  function syncControlsFromSettings(s) {
    const t = s.theme || {};
    const l = s.layout || {};
    const c = s.controls || {};

    $("#accentColor").value = t.accent || "#6366f1";
    $("#bgColor").value = t.background || "#0a0a0f";
    $("#textColor").value = t.text || "#f4f4f5";

    setRange("#spacingRange", "#spacingVal", parseInt(l.spacing) || 16, "px");
    setRange("#gridGapRange", "#gridGapVal", parseInt(l.gridGap) || 18, "px");
    setRange("#radiusRange", "#radiusVal", parseInt(l.radiusMd) || 14, "px");
    setRange("#btnOpacityRange", "#btnOpacityVal", Math.round(parseFloat(c.buttonOpacity || 0.72) * 100), "%");
    setRange("#btnBlurRange", "#btnBlurVal", parseInt(c.buttonBlur) || 16, "px");
    setRange("#cardOpacityRange", "#cardOpacityVal", Math.round(parseFloat(c.cardOpacity || 0.55) * 100), "%");
    setRange("#animSpeedRange", "#animSpeedVal", Math.round(parseFloat(c.animationSpeed || 0.35) * 100), "", (v) => `${(v / 100).toFixed(2)}s`);
    $("#cornerStyle").value = c.cornerStyle || "rounded";
  }

  function setRange(inputSel, labelSel, value, suffix, formatter) {
    const input = $(inputSel);
    const label = $(labelSel);
    if (!input || !label) return;
    input.value = value;
    label.textContent = formatter ? formatter(value) : `${value}${suffix}`;
  }

  function collectSettingsFromControls() {
    const accent = $("#accentColor").value;
    const s = JSON.parse(JSON.stringify(settings));
    s.theme.accent = accent;
    s.theme.accentSoft = hexToRgba(accent, 0.18);
    s.theme.background = $("#bgColor").value;
    s.theme.text = $("#textColor").value;

    const spacing = `${$("#spacingRange").value}px`;
    const gridGap = `${$("#gridGapRange").value}px`;
    const radius = `${$("#radiusRange").value}px`;
    s.layout.spacing = spacing;
    s.layout.gridGap = gridGap;
    s.layout.radiusSm = `${Math.max(0, parseInt(radius) - 6)}px`;
    s.layout.radiusMd = radius;
    s.layout.radiusLg = `${parseInt(radius) + 6}px`;
    s.layout.radiusXl = `${parseInt(radius) + 14}px`;

    s.controls.buttonOpacity = `${($("#btnOpacityRange").value / 100).toFixed(2)}`;
    s.controls.buttonBlur = `${$("#btnBlurRange").value}px`;
    s.controls.cardOpacity = `${($("#cardOpacityRange").value / 100).toFixed(2)}`;
    s.controls.animationSpeed = `${($("#animSpeedRange").value / 100).toFixed(2)}s`;
    s.controls.cornerStyle = $("#cornerStyle").value;

    return s;
  }

  /* ── Library rendering ── */
  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  function filteredLibrary() {
    if (currentFilter === "all") return library;
    return library.filter((item) => item.type === currentFilter);
  }

  function renderLibrary() {
    const grid = $("#libraryGrid");
    const empty = $("#emptyState");
    const items = filteredLibrary();

    grid.innerHTML = "";

    if (library.length === 0) {
      empty.classList.remove("hidden");
      grid.classList.add("hidden");
      return;
    }

    empty.classList.add("hidden");
    grid.classList.remove("hidden");

    if (items.length === 0) {
      grid.innerHTML = `<p style="color:var(--text-muted);padding:24px;">No ${currentFilter} backgrounds in your library.</p>`;
      return;
    }

    items.forEach((item, index) => {
      const isActive = wallpaperStatus.activeId === item.id;
      const card = document.createElement("article");
      card.className = `card${isActive ? " active" : ""}`;
      card.style.animationDelay = `${Math.min(index * 0.04, 0.4)}s`;
      card.dataset.id = item.id;

      card.innerHTML = `
        <div class="card-thumb">
          <img src="${item.thumbnailUrl}" alt="${escapeHtml(item.name)}" loading="lazy">
          <span class="card-badge badge-${item.type}">${item.type}</span>
          <div class="card-overlay"><span class="apply-label">Apply wallpaper</span></div>
        </div>
        <div class="card-body">
          <h4 title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</h4>
          <div class="card-actions">
            <button class="btn btn-ghost btn-icon rename-btn" title="Rename" data-id="${item.id}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
            </button>
            <button class="btn btn-ghost btn-icon delete-btn" title="Remove" data-id="${item.id}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>
            </button>
          </div>
        </div>`;

      card.addEventListener("click", (e) => {
        if (e.target.closest(".card-actions")) return;
        applyWallpaper(item.id);
      });

      card.querySelector(".delete-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        removeItem(item.id);
      });

      card.querySelector(".rename-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        renameItem(item.id, item.name);
      });

      grid.appendChild(card);
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function updateStatus() {
    const card = $("#statusCard");
    const label = $("#statusLabel");
    const detail = $("#statusDetail");

    if (wallpaperStatus.activeId) {
      const active = library.find((i) => i.id === wallpaperStatus.activeId);
      card.classList.add("active");
      label.textContent = "Active";
      detail.textContent = active
        ? `${active.name} (${active.type})`
        : wallpaperStatus.activeType || "Wallpaper applied";
    } else {
      card.classList.remove("active");
      label.textContent = "Ready";
      detail.textContent = "No wallpaper active";
    }
  }

  /* ── Backend actions ── */
  async function loadAll() {
    library = JSON.parse(backend.getLibrary());
    settings = JSON.parse(backend.getSettings());
    wallpaperStatus = JSON.parse(backend.getWallpaperStatus());
    applySettings(settings);
    renderLibrary();
    updateStatus();
  }

  function applyWallpaper(id) {
    const result = JSON.parse(backend.applyWallpaper(id));
    if (result.ok) {
      wallpaperStatus = result.status || wallpaperStatus;
      renderLibrary();
      updateStatus();
    }
  }

  function removeItem(id) {
    if (!confirm("Remove this background from your library?")) return;
    JSON.parse(backend.removeItem(id));
    library = JSON.parse(backend.getLibrary());
    wallpaperStatus = JSON.parse(backend.getWallpaperStatus());
    renderLibrary();
    updateStatus();
  }

  function renameItem(id, currentName) {
    const name = prompt("Rename background:", currentName);
    if (!name || name.trim() === currentName) return;
    JSON.parse(backend.renameItem(id, name.trim()));
    library = JSON.parse(backend.getLibrary());
    renderLibrary();
  }

  function importFiles() {
    const result = JSON.parse(backend.pickImportFiles());
    if (result.ok) {
      library = JSON.parse(backend.getLibrary());
      renderLibrary();
    }
  }

  function saveSettings() {
    const collected = collectSettingsFromControls();
    const result = JSON.parse(backend.saveSettings(JSON.stringify(collected)));
    if (result.ok) {
      applySettings(result.settings);
    }
  }

  function resetSettings() {
    const result = JSON.parse(backend.resetSettings());
    if (result.ok) {
      applySettings(result.settings);
    }
  }

  /* ── Toasts ── */
  function showToast(message, level = "info") {
    const stack = $("#toastStack");
    const el = document.createElement("div");
    el.className = `toast ${level}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateX(20px)";
      el.style.transition = `all ${getComputedStyle(document.documentElement).getPropertyValue("--anim-speed")} ease`;
      setTimeout(() => el.remove(), 350);
    }, 3200);
  }

  /* ── Navigation ── */
  function switchView(view) {
    $$(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === view);
    });
    $("#libraryView").classList.toggle("view-active", view === "library");
    $("#customizeView").classList.toggle("view-active", view === "customize");
    $("#viewTitle").textContent = view === "library" ? "Library" : "Customize";
    $("#viewSubtitle").textContent =
      view === "library" ? "Your saved backgrounds" : "Tune the interface to your taste";
  }

  /* ── Event bindings ── */
  function bindEvents() {
    $$(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    $$(".chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        $$(".chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        currentFilter = chip.dataset.filter;
        renderLibrary();
      });
    });

    $("#uploadBtn").addEventListener("click", importFiles);
    $("#emptyUploadBtn").addEventListener("click", importFiles);
    $("#refreshBtn").addEventListener("click", loadAll);
    $("#saveSettingsBtn").addEventListener("click", saveSettings);
    $("#resetSettingsBtn").addEventListener("click", resetSettings);

    const liveControls = [
      "#accentColor", "#bgColor", "#textColor",
      "#spacingRange", "#gridGapRange", "#radiusRange",
      "#btnOpacityRange", "#btnBlurRange", "#cardOpacityRange",
      "#animSpeedRange", "#cornerStyle",
    ];
    liveControls.forEach((sel) => {
      const el = $(sel);
      if (!el) return;
      const handler = () => {
        const collected = collectSettingsFromControls();
        applySettings(collected);
        pendingSettings = collected;
      };
      el.addEventListener("input", handler);
      el.addEventListener("change", handler);
    });

    if (backend && backend.toast) {
      backend.toast.connect((message, level) => showToast(message, level));
    }
    if (backend && backend.libraryChanged) {
      backend.libraryChanged.connect((json) => {
        library = JSON.parse(json);
        renderLibrary();
      });
    }
    if (backend && backend.wallpaperChanged) {
      backend.wallpaperChanged.connect((json) => {
        wallpaperStatus = JSON.parse(json);
        renderLibrary();
        updateStatus();
      });
    }
    if (backend && backend.settingsChanged) {
      backend.settingsChanged.connect((json) => {
        applySettings(JSON.parse(json));
      });
    }
  }

  /* ── Init ── */
  async function init() {
    await initBridge();
    bindEvents();
    await loadAll();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
