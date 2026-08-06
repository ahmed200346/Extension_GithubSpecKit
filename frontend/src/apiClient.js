import axios from "axios";

// ============================================================
// Client API avec découverte automatique du port du backend.
// Le serveur FastAPI (start_server.py) bascule automatiquement
// sur un port libre (8001, 8002...) si 8000 est occupé.
// Ce module sonde la plage de ports et utilise le premier qui
// répond au health-check du backend.
// ============================================================

const EXPLICIT_BASE = process.env.REACT_APP_API_BASE || "";
const DEFAULT_BASE = "http://localhost:8000/api/v1";
const START_PORT = 8000;
const END_PORT = 8010;

let apiBase = null;
let pendingDiscovery = null;

function getHostname() {
  if (typeof window !== "undefined" && window.location && window.location.hostname) {
    return window.location.hostname;
  }
  return "localhost";
}

async function discover() {
  const hostname = getHostname();
  for (let port = START_PORT; port <= END_PORT; port++) {
    const origin = `http://${hostname}:${port}`;
    try {
      const res = await axios.get(`${origin}/health`, { timeout: 1000 });
      if (res.status === 200 && res.data && res.data.status === "ok") {
        apiBase = `${origin}/api/v1`;
        console.info(`[SpecKit API] Backend détecté sur http://${hostname}:${port}`);
        return apiBase;
      }
    } catch (err) {
      // Port non utilisé par le backend, on essaie le suivant
    }
  }
  console.warn(
    `[SpecKit API] Aucun backend trouvé sur ${hostname}:${START_PORT}-${END_PORT}, repli sur ${DEFAULT_BASE}`
  );
  return DEFAULT_BASE;
}

export async function getApiBase() {
  if (apiBase) return apiBase;
  if (EXPLICIT_BASE) {
    apiBase = EXPLICIT_BASE;
    return apiBase;
  }
  if (!pendingDiscovery) {
    pendingDiscovery = discover();
  }
  try {
    return await pendingDiscovery;
  } finally {
    // Ne garder le cache que si la découverte a réussi (apiBase renseigné).
    // En cas d'échec, on retentera au prochain appel.
    if (apiBase) pendingDiscovery = null;
  }
}

export async function apiFetch(url, options = {}) {
  const base = await getApiBase();
  return fetch(`${base}${url}`, options);
}

export async function apiRequest(method, url, config = {}) {
  const base = await getApiBase();
  return axios({ method, url: `${base}${url}`, ...config });
}
