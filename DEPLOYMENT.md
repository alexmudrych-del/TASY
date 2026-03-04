# Návod k nasazení aplikace META Přehledy

## Možnosti nasazení

### 1. Railway (Doporučeno - nejjednodušší)

1. Vytvořte účet na [Railway.app](https://railway.app)
2. Klikněte na "New Project" → "Deploy from GitHub repo"
3. Připojte tento GitHub repozitář
4. Railway automaticky detekuje Python aplikaci
5. Přidejte environment variable:
   - `SECRET_KEY`: náhodný řetězec (např. vygenerujte na https://randomkeygen.com)
   - `PASSWORD_HASH`: heslo pro přístup (nebo použijte default)
6. Railway automaticky nasadí aplikaci
7. Získejte URL (např. `https://meta-prehledy.railway.app`)

### 2. Heroku

1. Vytvořte účet na [Heroku](https://heroku.com)
2. Nainstalujte Heroku CLI
3. V terminálu:
```bash
heroku login
heroku create meta-prehledy
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set PASSWORD_HASH="your-password-hash"
git push heroku main
```

### 3. PythonAnywhere (Zdarma pro začátek)

1. Vytvořte účet na [PythonAnywhere](https://www.pythonanywhere.com)
2. Nahrajte soubory přes Files tab
3. V Console vytvořte virtual environment:
```bash
mkvirtualenv --python=/usr/bin/python3.9 meta-prehledy
pip install -r requirements.txt
```
4. V Web tab nastavte:
   - Source code: `/home/username/meta-prehledy`
   - WSGI file: upravte na `from app import app`
   - Reload web app

### 4. Vlastní server (VPS)

1. Na serveru nainstalujte Python 3.9+
2. Naklonujte repozitář
3. Vytvořte virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
4. Nastavte environment variables:
```bash
export SECRET_KEY="your-secret-key"
export PASSWORD_HASH="your-password-hash"
```
5. Spusťte pomocí gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
6. Pro trvalé spuštění použijte systemd service nebo supervisor

## Změna hesla

Heslo můžete změnit v `app.py` na řádku:
```python
app.config['PASSWORD_HASH'] = generate_password_hash('nove-heslo')
```

Nebo nastavte environment variable `PASSWORD_HASH` s hashem hesla.

## Bezpečnost

- **DŮLEŽITÉ**: Změňte default heslo `pneuboss2025` v produkci!
- Použijte silné heslo
- Nastavte `SECRET_KEY` na náhodný řetězec
- Pro produkci použijte HTTPS (Railway/Heroku to mají automaticky)

## Testování lokálně

```bash
python3 app.py
```

Aplikace poběží na `http://localhost:5000`

## Poznámky

- Databáze SQLite je uložena v `data/database.db`
- Pro produkci zvažte použití PostgreSQL (Railway/Heroku to podporují)
- CSV soubory můžete nahrávat přes webové rozhraní `/upload`
