import axios from "axios";

const API_BASE = "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

async function tryRefresh(): Promise<string | null> {
  try {
    const res = await axios.post(
      `${API_BASE}/auth/refresh`,
      {},
      { withCredentials: true },
    );
    const token: string = res.data.access_token;
    if (token) {
      setAccessToken(token);
      return token;
    }
    return null;
  } catch {
    return null;
  }
}

let refreshInFlight: Promise<string | null> | null = null;

type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | null = null;

/** Register a callback fired when the session can no longer be refreshed (expired/invalid). */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as { _retried?: boolean } | undefined;
    const url = String(error.config?.url ?? "");
    const isAuthUrl = url.includes("/auth/login") || url.includes("/auth/refresh");
    if (
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      !isAuthUrl
    ) {
      original._retried = true;
      if (!refreshInFlight) {
        refreshInFlight = tryRefresh().finally(() => {
          refreshInFlight = null;
        });
      }
      const token = await refreshInFlight;
      if (token) {
        error.config.headers.Authorization = `Bearer ${token}`;
        return api(error.config);
      }
    }
    // Unrecoverable auth failure (refresh failed or the refreshed token was also
    // rejected) — let the app sign out instead of limping along on 401 responses.
    if (error.response?.status === 401 && !isAuthUrl) {
      unauthorizedHandler?.();
    }
    return Promise.reject(error);
  },
);
