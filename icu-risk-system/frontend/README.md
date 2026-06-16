# ICU Risk Prediction - Frontend

Next.js 14 frontend for the ICU Risk Prediction System.

## Setup

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` environment variable to point to your backend (default: http://localhost:8000).

## Pages

- `/` - Home / landing page
- `/dashboard` - Patient list with search
- `/patient/[id]` - Patient detail with risk gauge, charts, alerts
