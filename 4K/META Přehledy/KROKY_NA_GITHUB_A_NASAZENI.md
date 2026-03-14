# Další kroky: GitHub a nasazení META Přehledy

V repozitáři je teď **jen aplikace META Přehledy** (25 souborů). Data, uploady a vzorové CSV nejsou součástí commitu.

---

## 1. Vytvořte repozitář na GitHubu

1. Jděte na [github.com](https://github.com) a přihlaste se.
2. Klikněte na **„New repository“** (nebo **„+“ → „New repository“**).
3. Zadejte název, např. **`meta-prehledy`**.
4. Nechte **„Public“** (nebo zvolte Private).
5. **Nevybírejte** „Add a README“ ani „Add .gitignore“ – repozitář má zůstat prázdný.
6. Klikněte na **„Create repository“**.

---

## 2. Propojte lokální repozitář s GitHubem a pushněte

V terminálu (ve složce **Cursor Git**, tedy kořen repozitáře) spusťte (nahraďte `VAS_GITHUB_UCET` svým uživatelským jménem na GitHubu):

```bash
cd "/Users/alex08/Desktop/Cursor Git"

git remote add origin https://github.com/VAS_GITHUB_UCET/meta-prehledy.git
git branch -M main
git push -u origin main
```

Pokud používáte SSH:

```bash
git remote add origin git@github.com:VAS_GITHUB_UCET/meta-prehledy.git
git push -u origin main
```

Při prvním pushi vás GitHub může vyzvat k přihlášení (token nebo SSH klíč).

---

## 3. Nasazení na Railway nebo Render

### Railway

1. Jděte na [railway.app](https://railway.app) a přihlaste se (např. přes GitHub).
2. **New Project** → **Deploy from GitHub repo**.
3. Vyberte repozitář **meta-prehledy**.
4. **Root Directory:** zadejte `4K/META Přehledy` (protože aplikace je v podadresáři).
5. V **Variables** přidejte:
   - `SECRET_KEY` = náhodný řetězec (např. z [randomkeygen.com](https://randomkeygen.com))
   - `APP_PASSWORD` = vaše přihlašovací heslo k aplikaci
6. Railway aplikaci nasadí a zobrazí URL (např. `https://meta-prehledy.up.railway.app`).

### Render

1. Jděte na [render.com](https://render.com) a přihlaste se (např. přes GitHub).
2. **New** → **Web Service**.
3. Připojte repozitář **meta-prehledy**.
4. **Root Directory:** `4K/META Přehledy`.
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `gunicorn -b 0.0.0.0:$PORT app:app`
7. V **Environment** přidejte `SECRET_KEY` a `APP_PASSWORD` (stejně jako u Railway).
8. Vytvořte službu; Render vám dá URL.

---

## 4. Přidávání dat každý měsíc

1. Otevřete nasazenou aplikaci v prohlížeči.
2. Přihlaste se heslem (`APP_PASSWORD`).
3. Přejděte na **Upload** a nahrajte CSV exporty z Meta Business Suite za daný měsíc.

Hotovo. Data se ukládají do databáze na serveru (na free tieru může být SQLite; u Railway/Render zkontrolujte, zda je disk trvalý, nebo po čase přejděte na Postgres).
