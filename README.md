# Where I Shine – Planet Lines API (V1) for Railway

FastAPI + Flatlib service that returns natal planet positions and a concise summary.
V2 will add full astrocartography line generation (AC/DC/MC/IC polylines).

## Endpoints
- `GET /health`
- `POST /astro_eval` with body:
```
{
  "birthdate_iso": "1983-07-04",
  "birthtime_24": "12:10",
  "latitude": 48.3069,
  "longitude": 14.2858,
  "timezone_name": "Europe/Vienna",
  "birthplace_text": "Linz, Austria"
}
```
**Response**: `astro_eval_summary`, `natal_planets[]`, `astro_lines[]` (placeholder).

## Deploy on Railway (EU)
1) Push this folder to a new GitHub repo.
2) Railway → New Project → Deploy from GitHub → select repo.
3) Region: EU (Amsterdam). Wait for build & get URL.
4) Test: `GET https://<your>.railway.app/health`

## n8n
HTTP Request (POST) → `https://<your>.railway.app/astro_eval` with the JSON above.
Use `{{$json.astro_eval_summary}}` in your email text.