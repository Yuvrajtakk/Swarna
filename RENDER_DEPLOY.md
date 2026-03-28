# Render Deployment Guide — Bharat Sanchar AI

## 1. Pre-deploy checklist

- [ ] Delete `pnpm-lock.yaml` from the repo root (conflicts with npm)
- [ ] Ensure `node_modules/` is in `.gitignore`
- [ ] Push these 3 files: `server.js`, `package.json`, `models/Scheme.js`

---

## 2. Render Web Service Settings

| Field              | Value                         |
|--------------------|-------------------------------|
| **Runtime**        | Node                          |
| **Build Command**  | `npm install`                 |
| **Start Command**  | `node server.js`              |
| **Node Version**   | `18` (set in Environment tab) |
| **Root Directory** | *(leave blank — repo root)*   |

---

## 3. Environment Variables (add in Render dashboard)

Go to **Dashboard → Your Service → Environment → Add Environment Variable**

| Key              | Value                            | Required? |
|------------------|----------------------------------|-----------|
| `MONGODB_URI`    | Your Atlas connection string     | ✅ Yes    |
| `OPENAI_API_KEY` | Your OpenAI API key              | ✅ Yes    |
| `TWILIO_SID`     | Your Twilio Account SID          | Optional  |
| `TWILIO_TOKEN`   | Your Twilio Auth Token           | Optional  |
| `TWILIO_PHONE`   | Your Twilio number (+1415...)    | Optional  |
| `NODE_ENV`       | `production`                     | ✅ Yes    |

> ⚠️ **Do NOT add `PORT`** — Render injects it automatically.

---

## 4. Fix Node version on Render

Render reads the `engines` field from `package.json`. The new `package.json`
already specifies `"node": ">=18.0.0 <21.0.0"`.

You can also pin it explicitly in the Render dashboard:
**Settings → Node Version → `18`**

---

## 5. MongoDB Atlas — allow Render IPs

Render uses dynamic IPs, so in **Atlas → Network Access**, either:
- Add `0.0.0.0/0` (allow all — fine for a student project), or
- Use Render's static outbound IPs if on a paid plan.

---

## 6. Verify deployment

After deploy, hit your Render URL in a browser:

```
GET https://your-service.onrender.com/
```

Expected response:
```json
{
  "message": "Bharat Sanchar AI Backend is running 🚀",
  "mongodb": "connected",
  "twilio": "configured",
  "openai": "configured"
}
```

---

## 7. Seed the database (one-time)

After the service is live, run locally with the production URI:

```bash
MONGODB_URI="mongodb+srv://..." node scripts/seedDatabase.js
```

---

## 8. Why the AI SDK was removed

The `@ai-sdk/openai` and `ai` packages had version conflicts causing crashes on
Node 18 when `OPENAI_API_KEY` was missing. The new `server.js` calls the
OpenAI REST API directly using the built-in `fetch` (available in Node ≥ 18),
which is simpler, has zero extra dependencies, and never crashes the process.

---

## 9. Files changed summary

| File           | Change                                              |
|----------------|-----------------------------------------------------|
| `server.js`    | Full rewrite — safe fallbacks, fetch-based OpenAI   |
| `package.json` | Removed `ai`, `@ai-sdk/*`; pinned `engines`; clean  |
| `.env.example` | All required variables documented                   |
