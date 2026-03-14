# Návod: Jak exportovat data o vývoji followerů z Meta Business Suite

## Kde najít data o vývoji followerů

### Pro Instagram:
1. **Otevřete Meta Business Suite**: https://business.facebook.com
2. **Vyberte Instagram účet** (Pneuboss.cz)
3. **Přejděte do sekce "Insights"** (Přehledy)
4. **V levém menu vyberte "Followers"** (Sledující)
5. **Klikněte na "Export"** (Exportovat) v pravém horním rohu
6. **Vyberte:**
   - **Date Range**: Požadované období (např. poslední rok)
   - **Format**: CSV
   - **Data Type**: "Followers" nebo "Follower Growth"
7. **Stáhněte soubor** - měl by se jmenovat něco jako `Followers.csv` nebo `Follower Growth.csv`

### Pro Facebook:
1. **Otevřete Meta Business Suite**: https://business.facebook.com
2. **Vyberte Facebook stránku** (Pneuboss)
3. **Přejděte do sekce "Insights"** (Přehledy)
4. **V levém menu vyberte "Followers"** (Sledující)
5. **Klikněte na "Export"** (Exportovat)
6. **Vyberte stejné nastavení jako pro Instagram**
7. **Stáhněte soubor**

## Jaký formát dat potřebujeme

CSV soubor by měl obsahovat:
- **Datum** (Date) - každý den
- **Počet followerů** (Followers / Follower Count) - celkový počet
- **Noví followeri** (New Followers) - kolik jich přibylo
- **Ztracení followeri** (Lost Followers) - kolik jich ubylo

## Alternativní cesta (pokud není "Followers" v menu):

1. **Insights → Overview** (Přehledy → Přehled)
2. **Klikněte na "See All"** u sekce Followers
3. **V pravém horním rohu klikněte na "Export"**
4. **Vyberte CSV formát**

## Co dělat po stažení:

1. **Uložte soubor** do složky:
   - Instagram: `Imput IG Pneuboss/Followers.csv`
   - Facebook: `Imput FB Pneuboss/Followers.csv`

2. **Spusťte import** pomocí:
   ```bash
   python3 import_pneuboss_data.py
   ```

3. **Nebo nahrajte soubor** přes webové rozhraní na `/upload`

## Poznámka:

Pokud v Meta Business Suite nevidíte možnost exportovat data o followerech denně, může to být proto, že:
- Účet nemá dostatečná oprávnění
- Data nejsou dostupná pro dané období
- Je potřeba použít Meta Business API (což nechceme)

V takovém případě můžete zkusit:
- Exportovat data měsíčně a pak je rozdělit
- Použít data z "Audience Insights" pokud jsou dostupná
