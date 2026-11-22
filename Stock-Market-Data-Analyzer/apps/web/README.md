# Optional Next.js frontend

Install **Node.js 20.9+**. First run the backend from project root:

```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Then, in a second terminal from `apps/web`:

```bash
npm install
npm run dev
```

Visit <http://127.0.0.1:3000>. The local Next.js rewrite proxies browser `/api/*` paths to FastAPI. This starter is for local development only, without authentication or public hosting. Node.js packages require an internet connection on first install.
