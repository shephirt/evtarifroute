/**
 * Thin fetch wrapper for the backend API. Same-origin in production (served
 * by FastAPI); proxied via Vite dev server config during `npm run dev`.
 */
async function postJSON(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const detail =
      (data && (data.detail || JSON.stringify(data))) || `Request failed (${res.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}

export function radiusAnalysis(payload) {
  return postJSON("/api/radius-analysis", payload);
}

export function routeAnalysis(payload) {
  return postJSON("/api/route-analysis", payload);
}

export function tariffRecommendation(payload) {
  return postJSON("/api/tariff-recommendation", payload);
}

export async function geocodeSuggest(query) {
  const res = await fetch(`/api/geocode/suggest?q=${encodeURIComponent(query)}`);
  if (!res.ok) return [];
  const data = await res.json().catch(() => null);
  return data?.suggestions ?? [];
}
