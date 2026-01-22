# 🐛 KRITISCHE BUGS GEFUNDEN

## BUG #1: enrich_sources() filtert ALLE Sources raus
**Location:** `core/scraper.py:475, 494-496`
**Problem:** 
- Zeile 475: `if len(text) < 200: continue` - Überspringt kurze Texte
- Zeile 494-496: Alle Errors → `continue` - Keine Fehlerbehandlung
- Wenn ALLE 160 Sources fehlschlagen → 0 Sources returned!

**Gründe warum Sources feilen:**
- Paywall (403)
- Timeout
- Broken HTML
- Anti-scraping (Cloudflare, etc.)
- Text zu kurz (<200 chars)

**Solution:**
- Fallback: Behalte Sources auch OHNE full-text (nur Title + URL)
- Reduziere Minimum von 200 auf 50 chars
- Besseres Error Logging

---

## BUG #2: Falscher readability Import  
**Location:** `core/scraper.py:506`
**Problem:** `from readability import Document` ❌
**Solution:** `from readability.readability import Document` ✅

---

## BUG #3: Keine Fehler-Propagation
**Location:** `core/scraper.py:157-164, 167-174, 180-188`
**Problem:** Errors werden nur geloggt, aber Analysis läuft weiter
**Result:** Silent failures - User sieht "0 sources" ohne Grund

**Solution:**
- Wenn ALLE Quellen fehlschlagen → Raise Error mit Details
- Zeige User warum (API limit, Network, etc.)

---

## BUG #4: Rate Limiting zu aggressiv
**Location:** `core/scraper.py:492`
**Problem:** `time.sleep(0.5)` für JEDEN Request = 80 Sekunden für 160 Sources!
**Solution:** 
- Parallel requests (ThreadPoolExecutor)
- Oder nur sleep bei gleicher Domain

---

## POTENTIAL BUG #5: Missing error handling in extractor
**Location:** `extractor.py:165-168`
**Problem:** API errors return empty list - no visibility

---

## POTENTIAL BUG #6: Pydantic validation zu strikt
**Location:** `models/signal_models.py`
**Problem:** Validation könnte fehlschlagen wegen Schema-Mismatch

---

# 🔧 FIX PRIORITY

1. **BUG #1 & #2** (CRITICAL) - Enrich Sources funktioniert nicht
2. **BUG #3** (HIGH) - Error visibility
3. **BUG #4** (MEDIUM) - Performance
4. **BUG #5, #6** (LOW) - Nachgelagert
