# Jak spustit META Přehledy (TASY)

## 1. Lokálně na počítači (hned)

V terminálu v kořeni projektu (tam, kde je `app.py`):

```bash
cd "/Users/alex08/Desktop/Cursor Git"
pip install -r requirements.txt
python3 app.py
```

Pak v prohlížeči otevři: **http://127.0.0.1:5000**

- Přihlášení: heslo **pneuboss2025** (nebo nastav proměnnou `APP_PASSWORD`)
- Data se ukládají do složky `data/database.db` (SQLite)

---

## 2. Na Vercelu (online)

1. **Push na GitHub** (pokud jsi něco měnil):
   ```bash
   cd "/Users/alex08/Desktop/Cursor Git"
   git add app.py requirements.txt templates/ vercel.json public/
   git add "JAK_SPUSTIT.md"
   git commit -m "Vercel: Postgres, vercel.json, public/"
   git push origin main
   ```

2. **Na Vercelu** (vercel.com → projekt TASY):
   - **Storage** → vytvoř **Postgres** databázi a propoj ji s projektem (Vercel doplní `POSTGRES_URL`).
   - **Settings → Environment Variables** přidej:
     - `SECRET_KEY` – náhodný řetězec (např. z randomkeygen.com)
     - `APP_PASSWORD` – heslo pro přístup k aplikaci

3. **Redeploy** (Deployments → u posledního buildu „Redeploy“), nebo počkej na automatický deploy po pushi.

Aplikace pak poběží na URL typu `https://tasy-xxx.vercel.app`.
