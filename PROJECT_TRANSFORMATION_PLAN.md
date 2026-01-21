# 🚀 E-Commerce Intelligence Tool - Transformation Plan

**Projekt:** Pernod Ricard Agent → Universal E-Commerce Intelligence Tool  
**Version:** 2.0  
**Datum:** 19. Januar 2026  
**Status:** Ready for Implementation  

---

## 📋 Executive Summary

### **Projektziel**
Transformation des hardcoded Pernod Ricard Monitoring Tools in eine **generische Multi-Company E-Commerce Intelligence Plattform** mit 100% Fakten-Treue durch ein **7-Layer Anti-Halluzination System**.

### **Key Changes**
- ✅ **Multi-Company Support:** Beliebige Firmennamen analysierbar
- ✅ **Anti-Halluzination:** 7-schichtiges Validierungssystem
- ✅ **Dual-Mode:** Funktioniert mit DB (PostgreSQL) oder ohne (JSON)
- ✅ **Multi-User:** Mehrere gleichzeitige Analysen möglich
- ✅ **History:** Analyse-Historie mit Suchfunktion
- ✅ **EU/DE Fokus:** Spezialisiert auf europäische E-Commerce Märkte

### **Scope**
Phase 1-5.3: Production-Ready MVP mit vollständiger Validierung

**Geschätzter Aufwand:** 64-84 Stunden (8-11 Arbeitstage)

---

## ✅ Finalisierte Entscheidungen

| # | Bereich | Entscheidung | Begründung |
|---|---------|--------------|------------|
| 1 | **Datenbank** | Dual-Mode (PostgreSQL + JSON Fallback) | Flexibilität, kostenlos nutzbar |
| 2 | **Multi-User** | Ja | Mehrere simultane Analysen möglich |
| 3 | **Beispiel-Daten** | Behalten mit Warning-Banner | Demo-Zwecke, nicht aktuell |
| 4 | **History** | Ja (in DB gespeichert) | Wiederverwendung, Vergleiche |
| 5 | **LLM Model** | gpt-4o-mini (konfigurierbar) | Cost-effective, schnell, upgradefähig |
| 6 | **Regionen** | Hardcoded EU/DE mit Info-Banner | Spezialisierung, klarer Fokus |
| 7 | **Deployment** | Direct via Streamlit Cloud | Kein Dev Branch, schnelles Testing |
| 8 | **Projekt-Name** | "ecommerce_intel" | Generisch, beschreibend |
| 9 | **Export** | CSV + JSON | Wie aktuell, ausreichend |
| 10 | **Error Handling** | Weiterlaufen + Details | Graceful degradation, debugging |
| 11 | **Job Processing** | Synchron mit Progress Bar | Einfacher, keine Redis/Celery |
| 12 | **Human Review** | Nein | User kann Quellen selbst prüfen |
| 13 | **Secrets** | GitHub Secrets + Streamlit | Wie bisher, kein .env |

---

## 🎯 Hauptfeatures

### **1. Multi-Company Intelligence**
- Firmeneingabe via UI (Text Input)
- Auto-Discovery von Newsroom, LinkedIn, etc.
- Domain-Guessing aus Firmennamen
- Dynamische Google News Queries

### **2. 7-Layer Anti-Halluzination System**

#### **Layer 1: Source Verification**
- Hash-basierte Integritätsprüfung
- Volltext-Speicherung
- URL-Verifizierung (optional)

#### **Layer 2: Citation Enforcement ⭐ KRITISCH**
- Pflichtfeld `verbatim_quote` für jedes Signal
- Fuzzy-Matching gegen Quelltext
- Automatische Ablehnung ohne valides Zitat
- Nummerische Werte müssen im Zitat nachweisbar sein

#### **Layer 3: Schema Validation**
- Pydantic Models mit strikter Validierung
- Pflichtfelder: verbatim_quote, source_title, source_url
- Confidence nicht > 0.95 (unrealistisch)
- Metric + Unit bei numeric_value

#### **Layer 4: Confidence Filtering**
- Multi-Tier: Verified (≥0.90), High (≥0.80), Medium (≥0.70)
- Automatische Filterung: Nur ≥0.70 in Reports
- Confidence-Badges in UI (🟢🟡🟠)
- Statistiken über aussortierte Signals

#### **Layer 5: Cross-Reference Validation**
- Sucht nach gleichen Fakten in mehreren Quellen
- Confidence-Boost bei Corroboration (2+ Quellen)
- Confidence-Penalty bei Single-Source

#### **Layer 6: LLM Fact-Checking Pass**
- Zweiter LLM-Call zur Verifizierung
- Status: verified / partially_correct / incorrect / cannot_verify
- Automatische Confidence-Anpassung
- Ablehnung von "incorrect" Signals

#### **Layer 7: Transparent Reporting**
- Jede Aussage mit [n] Quellenangabe
- Vollständige Quellenliste
- Validierungs-Statistiken im Bericht
- Abschnitt "Datenqualität & Einschränkungen"

**Erwartete Rejection-Rate:** 40-60% (gewollt - Qualität über Quantität)

### **3. User Interface**

#### **Hauptseite - Company Input**
```
┌─────────────────────────────────────┐
│  Sidebar                            │
│  ┌───────────────────────────────┐  │
│  │ 🔍 Company Analysis           │  │
│  │                               │  │
│  │ Firmenname: [________]        │  │
│  │                               │  │
│  │ ⚙️ Erweiterte Optionen         │  │
│  │   Domain (optional)           │  │
│  │   Newsroom URL (optional)     │  │
│  │   LinkedIn URL (optional)     │  │
│  │   Lookback Days: [14]         │  │
│  │                               │  │
│  │ [🚀 Analyse starten]          │  │
│  └───────────────────────────────┘  │
│                                     │
│  ℹ️ Fokus: EU/DE E-Commerce         │
│  🤖 Model: gpt-4o-mini              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Main Content                       │
│  ┌───────────────────────────────┐  │
│  │ Welcome Screen                │  │
│  │ (wenn kein Firmenname)        │  │
│  └───────────────────────────────┘  │
│                                     │
│  📚 Letzte Analysen (History)       │
│  • Coca-Cola (vor 2h) ✅           │
│  • Unilever (vor 1 Tag) ✅         │
│  • LVMH (vor 3 Tagen) ✅           │
└─────────────────────────────────────┘
```

#### **Während Analyse - Progress Tracking**
```
┌─────────────────────────────────────┐
│ Analysiere: Coca-Cola               │
│                                     │
│ [████████░░░░░░░░] 60%              │
│ 🧠 Generiere Signale...             │
│                                     │
│ Abgeschlossene Schritte:            │
│ ✅ Quellen entdeckt (45 gefunden)   │
│ ✅ Inhalte extrahiert (38 valid)    │
│ ⏳ Signale werden generiert...      │
│ ⏸️ Bericht wird erstellt            │
└─────────────────────────────────────┘
```

#### **Results Display**
```
┌─────────────────────────────────────┐
│ Coca-Cola — E-Commerce Intelligence │
│                                     │
│ 📊 KPIs                             │
│ • Signale: 12 (8 verified)          │
│ • Quellen: 38 (EU: 28)              │
│ • Rejection Rate: 47%               │
│ • Avg. Confidence: 0.82             │
│                                     │
│ 📝 Bericht                          │
│ [Executive Summary...]              │
│                                     │
│ 🔍 Signale (filterable)             │
│ ┌─────────────────────────────┐    │
│ │ 🟢 E-Commerce Umsatz DE      │    │
│ │ Confidence: 0.92             │    │
│ │ Zitat: "Umsatz stieg um..." │    │
│ │ ✅ Verified                  │    │
│ │ 📚 2 weitere Quellen         │    │
│ └─────────────────────────────┘    │
│                                     │
│ 📚 Quellen (38)                     │
│ [Liste mit Links...]                │
└─────────────────────────────────────┘
```

---

## 🗂️ Neue Dateistruktur

```
ecommerce_intel/                    # Umbenannt von pernod_ricard_agent_repo_full
│
├── app.py                          # Komplett überarbeitet: Multi-Company UI
├── db.py                           # Angepasst: DB + JSON Fallback
├── models.sql                      # Erweitert: companies, analyses Tabellen
├── requirements.txt                # Neue Dependencies
├── README.md                       # Neu geschrieben
├── .gitignore                      # Bleibt
├── Dockerfile                      # Angepasst
│
├── core/                           # NEU: Business Logic
│   ├── __init__.py
│   ├── scraper.py                  # CompanyIntelligenceScraper Klasse
│   ├── extractor.py                # Generisch + Validation
│   ├── report_generator.py         # Dynamische Reports
│   └── analysis_engine.py          # Orchestrierung mit Progress
│
├── validators/                     # NEU: 7-Layer Validation
│   ├── __init__.py
│   ├── citation_validator.py       # Layer 2: Zitat-Prüfung (KRITISCH)
│   ├── confidence_filter.py        # Layer 4: Confidence Thresholds
│   ├── cross_reference.py          # Layer 5: Multi-Source Check
│   └── llm_fact_checker.py         # Layer 6: LLM Fact-Check
│
├── models/                         # NEU: Data Models
│   ├── __init__.py
│   └── signal_models.py            # Pydantic mit strikter Validation
│
├── prompts/                        # Erweitert
│   ├── extract_prompt.txt          # Anti-Hallucination Rules
│   └── report_prompt.txt           # NEU: Report Template
│
├── utils/                          # NEU: Helpers
│   ├── __init__.py
│   ├── text_utils.py               # Normalisierung, Cleaning
│   └── url_utils.py                # Domain-Guessing, URL-Parsing
│
├── scripts/                        
│   ├── init_db.py                  # NEU: DB Initialization
│   └── test_company.py             # NEU: Quick Testing Script
│
├── tests/                          # Erweitert
│   ├── __init__.py
│   ├── test_citation_validator.py  # NEU
│   ├── test_confidence_filter.py   # NEU
│   ├── test_cross_reference.py     # NEU
│   ├── test_scraper.py             # NEU
│   └── test_extractor.py           # Erweitert
│
└── data/                           # Bleibt
    ├── pernod_ricard_example.json  # Umbenannt mit Warning-Banner
    └── .gitkeep

# GELÖSCHT/VERSCHOBEN:
❌ scraper.py (alt)                 → core/scraper.py
❌ extractor.py (alt)                → core/extractor.py
❌ scripts/build_json.py             → core/analysis_engine.py
❌ scripts/run_agent.py              → obsolete
```

---

## 📐 Datenbank-Schema

### **Neue Tabellen**

```sql
-- Companies: Multi-Company Support
CREATE TABLE IF NOT EXISTS companies (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  domain text,
  newsroom_url text,
  linkedin_url text,
  config jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(name, domain)
);

-- Analyses: Job-Tracking & History
CREATE TABLE IF NOT EXISTS analyses (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES companies(id) ON DELETE CASCADE,
  status text DEFAULT 'pending',  -- pending, running, completed, failed
  progress jsonb DEFAULT '{}',
  lookback_days int DEFAULT 14,
  max_sources int DEFAULT 50,
  started_at timestamptz,
  completed_at timestamptz,
  error_message text,
  result_json jsonb,  -- Cached results for fast display
  validation_stats jsonb,  -- Rejection rate, confidence distribution
  created_at timestamptz DEFAULT now(),
  INDEX idx_company_created (company_id, created_at DESC)
);

-- Sources: Linked to analysis
CREATE TABLE IF NOT EXISTS sources (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id uuid REFERENCES analyses(id) ON DELETE CASCADE,
  url text NOT NULL,
  title text,
  source_type text,  -- newsroom, gnews, linkedin
  published_at timestamptz,
  language text,
  raw_text text NOT NULL,
  text_hash text NOT NULL,
  fetch_timestamp timestamptz DEFAULT now(),
  http_status_code int,
  is_eu_source boolean DEFAULT false,
  has_ecommerce_keywords boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  UNIQUE(analysis_id, text_hash)
);
CREATE INDEX idx_sources_analysis ON sources(analysis_id);
CREATE INDEX idx_sources_text_search ON sources USING gin(to_tsvector('german', raw_text));

-- Signals: Linked to analysis
CREATE TABLE IF NOT EXISTS signals (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id uuid REFERENCES analyses(id) ON DELETE CASCADE,
  source_id uuid REFERENCES sources(id),
  type text,
  value jsonb,
  verbatim_quote text NOT NULL,  -- NEW: Required!
  confidence numeric CHECK (confidence >= 0 AND confidence <= 1),
  fact_check_status text,  -- verified, partially_correct, incorrect, cannot_verify
  corroboration_count int DEFAULT 0,
  detected_at timestamptz DEFAULT now()
);
CREATE INDEX idx_signals_analysis ON signals(analysis_id);
CREATE INDEX idx_signals_confidence ON signals(confidence DESC);
```

---

## 🔧 Technische Spezifikationen

### **Dependencies (requirements.txt)**

```txt
# Existing
requests>=2.31
beautifulsoup4>=4.12
feedparser>=6.0.10
python-dateutil>=2.8.2
python-dotenv>=1.0.1
streamlit>=1.30.0
pandas>=2.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# OpenAI
openai>=1.30.0

# NEW: Validation & Processing
pydantic>=2.5.0
readability-lxml>=0.8.1
httpx>=0.25.0

# NEW: Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Optional: Enhanced features
plotly>=5.18.0  # For charts
```

### **Environment Variables**

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional - Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Optional - Configuration
OPENAI_MODEL=gpt-4o-mini  # Default if not set
APP_TITLE=E-Commerce Intelligence Tool
DEFAULT_LOOKBACK_DAYS=14
MAX_CONCURRENT_ANALYSES=5

# Optional - Features
ENABLE_URL_VERIFICATION=false
MIN_CONFIDENCE_THRESHOLD=0.70
```

### **Streamlit Secrets (secrets.toml)**

```toml
OPENAI_API_KEY = "sk-..."
DATABASE_URL = "postgresql://..."  # Optional
OPENAI_MODEL = "gpt-4o-mini"
```

### **GitHub Secrets**

```
OPENAI_API_KEY
DATABASE_URL (optional)
OPENAI_MODEL (optional)
```

---

## 📅 Implementierungs-Roadmap

### **Sprint 1: Foundation (Tag 1-2, ~12-16h)**

**Ziel:** Basis-Infrastruktur für Multi-Company

#### Aufgaben:
1. ✅ Repository umbenennen → `ecommerce_intel`
2. ✅ Neue Ordnerstruktur anlegen (`core/`, `validators/`, `models/`, `utils/`)
3. ✅ `models.sql` erweitern (companies, analyses Tabellen)
4. ✅ `db.py` anpassen:
   - DB-Connection mit Fallback
   - `init_db()` für neue Tabellen
   - Helper-Funktionen (create_company, create_analysis, etc.)
5. ✅ `utils/url_utils.py`:
   - Domain-Guessing aus Firmennamen
   - URL-Normalisierung
   - EU-URL Detection
6. ✅ `utils/text_utils.py`:
   - Text-Normalisierung
   - Hash-Funktionen
   - Cleaning-Helpers
7. ✅ `requirements.txt` aktualisieren

**Deliverable:** Infrastruktur steht, DB läuft

---

### **Sprint 2: Core Scraper Logic (Tag 2-3, ~14-18h)**

**Ziel:** Generischer Scraper für beliebige Firmen

#### Aufgaben:
1. ✅ `core/scraper.py` - `CompanyIntelligenceScraper` Klasse:
   - `__init__(company_name, config)`
   - `discover_all_sources()` Orchestrator
   - `_discover_google_news()` - EU Editionen + E-Commerce Queries
   - `_discover_linkedin_via_gnews()` - site:linkedin.com
   - `_discover_linkedin_direct()` - Wenn URL gegeben
   - `_auto_discover_newsroom()` - Try common patterns
   - `_scrape_newsroom_index()` - Parse newsroom pages
   - `enrich_sources()` - Fetch & extract full text
   - `_build_ecommerce_queries()` - Dynamic query templates
2. ✅ `core/scraper.py` - Error Handling:
   - Graceful degradation (1 Source-Type fails → continue)
   - Detailed error messages
   - Rate limiting (exponential backoff)
3. ✅ Tests: `tests/test_scraper.py`
   - Test domain guessing
   - Test query building
   - Test newsroom auto-discovery

**Deliverable:** Scraper funktioniert für beliebige Firmen

---

### **Sprint 3: Validation Layer (Tag 3-4, ~16-20h)**

**Ziel:** Anti-Halluzination System implementieren

#### Aufgaben:
1. ✅ `models/signal_models.py`:
   - `SignalValue` Pydantic Model
   - `Signal` Pydantic Model (mit verbatim_quote!)
   - `ExtractionResult` Model
   - Strikte Validators
2. ✅ `validators/citation_validator.py` ⭐ **KRITISCH**:
   - `CitationValidator` Klasse
   - `validate_signal()` - Prüft einzelnes Signal
   - `_fuzzy_contains()` - Fuzzy-Matching gegen Quelltext
   - `_validate_number_in_text()` - Zahlen-Verifizierung
   - `validate_all_signals()` - Batch-Processing
   - Logging rejected signals
3. ✅ `validators/confidence_filter.py`:
   - `ConfidenceFilter` Klasse
   - Multi-Tier thresholds (0.70, 0.80, 0.90)
   - `filter_signals()` - Kategorisierung
   - `get_report_signals()` - Mit Badges
4. ✅ `validators/cross_reference.py`:
   - `CrossReferenceValidator` Klasse
   - `find_corroborating_sources()` - Sucht Bestätigungen
   - `validate_signals_cross_reference()` - Confidence-Adjustments
5. ✅ `validators/llm_fact_checker.py`:
   - `LLMFactChecker` Klasse
   - Second LLM pass für Verifizierung
   - Status: verified / partially_correct / incorrect / cannot_verify
   - Confidence adjustments basierend auf Fact-Check
6. ✅ Tests:
   - `tests/test_citation_validator.py` - Fake quotes detection
   - `tests/test_confidence_filter.py` - Threshold filtering
   - `tests/test_cross_reference.py` - Corroboration logic

**Deliverable:** Vollständige 7-Layer Validation funktioniert

---

### **Sprint 4: Extraction & Reporting (Tag 4-5, ~14-18h)**

**Ziel:** LLM Integration mit Validation

#### Aufgaben:
1. ✅ `prompts/extract_prompt.txt`:
   - Anti-Hallucination System Prompt
   - Strikte Regeln (KEINE ERFINDUNGEN!)
   - Pflicht: verbatim_quote
   - Beispiele (gut/schlecht)
2. ✅ `prompts/report_prompt.txt`:
   - Template für transparente Reports
   - Citation-Requirements [n]
   - Confidence-Level Handling
   - Datenqualitäts-Abschnitt
3. ✅ `core/extractor.py`:
   - `extract_signals_with_grounding()` - Mit Prompt-Template
   - Company-name als Parameter
   - Numbered sources im Prompt
   - Schema-Validation (Pydantic)
4. ✅ `core/report_generator.py`:
   - `generate_transparent_report()` - Mit Citations
   - Signal-Digest Vorbereitung
   - Source-Citations Liste
   - Validation-Stats Appendix
5. ✅ `core/analysis_engine.py`:
   - `FactBasedAnalysisEngine` Klasse
   - `run_validated_analysis()` - Orchestriert alle Layer
   - Progress-Tracking
   - Error-Handling mit Details
   - Validation-Statistics Collection

**Deliverable:** End-to-End Pipeline funktioniert mit Validation

---

### **Sprint 5: Frontend (Tag 5-6, ~16-20h)**

**Ziel:** Neue UI mit Multi-Company Support

#### Aufgaben:
1. ✅ `app.py` - Komplett überarbeitet:
   - **Sidebar:**
     - Company Name Input (required)
     - Optional: Domain, Newsroom, LinkedIn
     - Lookback Days Slider
     - "Analyse starten" Button
     - EU/DE Fokus Info-Banner
     - Model-Anzeige
   - **Main Content:**
     - Welcome Screen (wenn kein Name)
     - Progress Tracking während Analyse
     - Results Display nach Completion
     - Analysis History (DB mode)
2. ✅ Progress Tracking Component:
   - Progress Bar (0-100%)
   - Status Text ("Entdecke Quellen...")
   - Completed Steps Checklist
   - Error Display
3. ✅ Results Display:
   - KPI Metrics (Signale, Quellen, Rejection Rate, etc.)
   - Bericht (Markdown)
   - Signals mit Expandable Cards:
     - Headline, Fact, Metric/Value
     - Verbatim Quote (prominent)
     - Source Link
     - Confidence Badge (🟢🟡🟠)
     - Fact-Check Status (✅⚠️❓❌)
     - Corroboration Count
     - Corroborating Sources (expandable)
   - Filter:
     - Nach Type
     - Nach Confidence
     - Nach Fact-Check Status
     - Volltextsuche
   - Quellen-Liste (mit Links)
   - Export (CSV + JSON)
4. ✅ Analysis History (DB mode):
   - Liste letzte Analysen
   - Firmenname, Datum, Status, Signal Count
   - Click to load
   - "Wiederholen" Button
   - Delete Button
5. ✅ Validation Stats Dashboard:
   - Funnel-Visualisierung (wenn plotly verfügbar)
   - Confidence Distribution
   - Signal Types Breakdown
6. ✅ Example Data Banner:
   - Warning wenn Pernod Ricard Beispiel-Daten
   - "DEMO-DATEN" Hinweis
   - "Nicht aktuell"
7. ✅ No-DB Fallback Mode:
   - Funktioniert ohne DATABASE_URL
   - Speichert in `data/{company_slug}_{date}.json`
   - Limited History (letzte 10 im data/ Ordner)

**Deliverable:** Vollständige, benutzerfreundliche UI

---

### **Sprint 6: Testing & Polish (Tag 6-7, ~12-16h)**

**Ziel:** Production-Ready Quality

#### Aufgaben:
1. ✅ Unit Tests vervollständigen:
   - `tests/test_extractor.py` erweitern
   - Coverage-Report generieren
   - Edge Cases testen
2. ✅ Integration Tests:
   - `tests/test_end_to_end.py` - Vollständige Pipeline
   - Test mit bekannten Firmen (Coca-Cola, Unilever)
   - Test Error-Szenarien
3. ✅ Manual Testing Checklist:
   - [ ] 10 verschiedene Firmen (verschiedene Branchen)
   - [ ] Edge Cases:
     - Unbekannte Firma (keine News)
     - Firma mit Sonderzeichen
     - Sehr langer Firmenname
     - Firma mit/ohne Newsroom
   - [ ] Fact-Checking: 20 Stichproben manuell gegen Quellen prüfen
   - [ ] UI/UX auf Desktop + Mobile
4. ✅ Error Handling Improvements:
   - Detaillierte Fehlermeldungen
   - Recovery-Suggestions
   - Debug-Info (Traceback in Expander)
5. ✅ Performance Optimierung:
   - Caching aktivieren (Streamlit @st.cache_data)
   - DB-Queries optimieren
   - Parallele Requests wo möglich
6. ✅ Dokumentation:
   - README.md neu schreiben
   - DEPLOYMENT.md erstellen
   - API-Docs (Docstrings)
   - Beispiel-Screenshots
7. ✅ Logging:
   - Strukturiertes Logging setup
   - Log-Levels korrekt
   - Sensitive Data (API Keys) nicht loggen
8. ✅ Security Review:
   - SQL Injection Prevention (parameterized queries)
   - XSS Prevention (Streamlit macht automatisch)
   - API Key nicht exposen

**Deliverable:** Production-Ready, getestet, dokumentiert

---

## 🧪 Testing-Strategie

### **Unit Tests (pytest)**

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov=validators --cov-report=html

# Specific test
pytest tests/test_citation_validator.py -v
```

### **Test Cases**

#### **Citation Validator**
- ✅ Akzeptiert valide Zitate (im Text vorhanden)
- ✅ Rejected fake Zitate (nicht im Text)
- ✅ Fuzzy-Matching funktioniert (Tippfehler OK)
- ✅ Nummerische Werte werden verifiziert
- ✅ Zu kurze Zitate werden abgelehnt

#### **Confidence Filter**
- ✅ Filtert Signals < 0.70 raus
- ✅ Badges werden korrekt zugewiesen
- ✅ Statistiken stimmen

#### **Cross-Reference**
- ✅ Findet Corroborating Sources
- ✅ Confidence wird geboostet
- ✅ Single-Source Penalty funktioniert

#### **End-to-End**
- ✅ Coca-Cola → funktioniert
- ✅ Unbekannte Firma → Graceful Degradation
- ✅ Keine OpenAI Key → Klare Fehlermeldung

### **Manual Testing**

**Test-Firmen:**
1. Coca-Cola (große Firma, viele News)
2. Unilever (Consumer Goods)
3. LVMH (Luxury)
4. Zalando (E-Commerce Pure Play)
5. Lidl (Retail)
6. Deutsche Post DHL (Logistics)
7. Kleine lokale Firma (wenig News)
8. Startup (sehr wenig Daten)
9. B2B Firma (keine Consumer News)
10. Firma mit Umlauten (Müller, Käfer)

**Fact-Checking:**
- 20 zufällige Signals auswählen
- Verbatim Quote gegen Quelle prüfen
- Nummerische Werte verifizieren
- Kontext korrekt wiedergegeben?

---

## 💰 Kosten-Kalkulation

### **OpenAI API (gpt-4o-mini)**

| Komponente | Calls | Tokens | Kosten |
|------------|-------|--------|--------|
| Signal Extraction | 1-2x | ~5K input + 2K output | $0.02-0.04 |
| Report Generation | 1x | ~15K input + 3K output | $0.04-0.06 |
| Fact-Checking | 1x | ~8K input + 1K output | $0.02-0.03 |
| **Total pro Analyse** | | | **$0.08-0.13** |

**Bei verschiedenen Nutzungslevels:**
- 10 Analysen/Tag = ~$40/Monat
- 50 Analysen/Tag = ~$200/Monat
- 100 Analysen/Tag = ~$400/Monat

### **Datenbank (Supabase Free Tier)**

- ✅ 500 MB Storage
- ✅ Unlimited API Requests
- ✅ 50K Active Users

**Kosten:** $0/Monat (kostenlos)

### **Hosting (Streamlit Cloud)**

- ✅ 1 Public App
- ✅ Unlimited viewers
- ✅ 1 GB RAM
- ✅ GitHub Integration

**Kosten:** $0/Monat (kostenlos)

### **Total Infrastruktur-Kosten**

**Fix:** $0/Monat (alles Free Tier)  
**Variabel:** OpenAI API (pay-as-you-go)

---

## 🚀 Deployment

### **Initial Setup**

1. **Supabase (optional):**
   ```
   1. Gehe zu supabase.com
   2. "Start your project" (kostenlos)
   3. Erstelle neues Projekt
   4. SQL Editor → models.sql ausführen
   5. Kopiere DATABASE_URL aus Settings
   ```

2. **GitHub Secrets:**
   ```
   Gehe zu: Repo → Settings → Secrets → Actions
   
   Neu:
   - OPENAI_API_KEY = sk-...
   - DATABASE_URL = postgresql://... (optional)
   - OPENAI_MODEL = gpt-4o-mini (optional)
   ```

3. **Streamlit Cloud:**
   ```
   1. Gehe zu share.streamlit.io
   2. "New app" → Select Repo
   3. Main file: app.py
   4. Secrets (Advanced):
      OPENAI_API_KEY = "sk-..."
      DATABASE_URL = "postgresql://..." (optional)
   5. Deploy
   ```

### **Auto-Deployment**

Bei Push auf `main`:
- ✅ Streamlit Cloud detected Änderungen automatisch
- ✅ Rebuild & Redeploy (~2-3 Minuten)
- ✅ Keine Actions nötig

### **Testing vor Production**

```bash
# Lokal testen
streamlit run app.py

# Mit DB
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="sk-..."
streamlit run app.py

# Ohne DB (JSON Fallback)
unset DATABASE_URL
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```

---

## ✅ Success Criteria

### **Funktional**
- ✅ User kann beliebige Firmennamen eingeben
- ✅ Analyse funktioniert für mindestens 8/10 Test-Firmen
- ✅ Rejection-Rate zwischen 40-60%
- ✅ Durchschnittliche Confidence ≥ 0.80
- ✅ Manual Fact-Check: 18/20 Signals korrekt (90%+)
- ✅ History funktioniert (wenn DB vorhanden)
- ✅ JSON-Fallback funktioniert (ohne DB)
- ✅ Export (CSV + JSON) funktioniert

### **Performance**
- ✅ Analyse-Dauer: < 7 Minuten (gpt-4o-mini)
- ✅ UI reagiert flüssig
- ✅ Keine Crashes bei Fehlern

### **Qualität**
- ✅ Code-Coverage ≥ 60%
- ✅ Alle Layer 1-6 Tests bestehen
- ✅ Keine SQL Injection Vulnerabilities
- ✅ Secrets nicht im Code/Logs

### **Usability**
- ✅ Intuitive Bedienung (neue User können ohne Anleitung starten)
- ✅ Klare Fehlermeldungen
- ✅ Progress Tracking funktioniert
- ✅ Mobile-friendly (responsive)

---

## 🔄 Post-Launch Roadmap (Optional)

### **Phase 6: Nice-to-Have Features**

**Quick Wins (1-2 Tage):**
- 📧 Email-Benachrichtigung bei Completion
- 🔄 "Refresh Analysis" Button
- 📊 Plotly Charts (Confidence Distribution, Signal Types)
- 🌐 English UI Toggle

**Medium Effort (3-5 Tage):**
- 🆚 Compare Mode (Firma A vs. Firma B)
- 📅 Scheduled Analyses (wöchentlich)
- 🎨 Custom Branding
- 📄 PDF Export (mit weasyprint)

**Large Effort (1-2 Wochen):**
- 👥 User Authentication & Workspaces
- 🔌 REST API
- 💳 Credits/Usage Tracking
- 🤖 Webhook-Integration
- 🌍 Multi-Language Reports

---

## 📞 Support & Kontakt

**Projekt-Owner:** Jannick Müller  
**Repo:** GitHub (Pernod_Ricard_Agent-main → ecommerce_intel)  
**Hosting:** Streamlit Cloud  
**Dokumentation:** Dieses Dokument

---

## 📜 Changelog

### Version 2.0 (planned)
- Multi-Company Support
- 7-Layer Anti-Halluzination System
- Dual-Mode (DB + JSON)
- Analysis History
- Validation Statistics

### Version 1.0 (current)
- Hardcoded Pernod Ricard
- Basic LLM extraction
- Streamlit UI
- EU/DE Focus

---

## ✨ Final Notes

**Qualität vor Quantität:**
- Wir erwarten 40-60% Rejection-Rate
- Das ist **gewollt** - lieber weniger, dafür korrekte Signale
- Validation fängt Halluzinationen zuverlässig ab

**Flexibilität:**
- Tool funktioniert mit und ohne DB
- LLM Model einfach upgradebar
- Erweiterbar ohne Core-Änderungen

**Kosteneffizienz:**
- Komplette Infrastruktur kostenlos (Free Tiers)
- Nur OpenAI API kostet (Pay-as-you-go)
- ~$0.08-0.13 pro Analyse (gpt-4o-mini)

---

**Status:** 🚀 IN PROGRESS  
**Started:** Jan 21, 2026  
**Latest Update:** Sprint 3 COMPLETE  

---

## 📊 Implementation Progress

### ✅ SPRINT 1: Foundation (COMPLETE)
- ✅ Git repository setup
- ✅ `.gitignore` with proper exclusions
- ✅ Project structure created
- ✅ README.md updated
- ✅ Database schema (models.sql)
- ✅ DB connection layer (db.py) with JSON fallback
- ✅ Utility functions (url_utils.py, text_utils.py)

### ✅ SPRINT 2: Multi-Source Discovery (COMPLETE)
- ✅ `CompanyIntelligenceScraper` class
- ✅ Google News integration
- ✅ LinkedIn discovery
- ✅ Newsroom auto-detection
- ✅ E-commerce keyword filtering
- ✅ EU region focus
- ✅ Unit tests (test_scraper.py)
- ✅ Basic UI for source discovery

### ✅ SPRINT 3: Signal Extraction (COMPLETE) 🎉
- ✅ Pydantic signal models (signal_models.py)
- ✅ **Layer 2: Citation Validator** (citation_validator.py)
- ✅ **Layer 4: Confidence Filter** (confidence_filter.py)
- ✅ **Layer 5: Cross-Reference Validator** (cross_reference.py)
- ✅ **Layer 6: LLM Fact-Checker** (llm_fact_checker.py)
- ✅ Improved extraction prompts (extract_signals_v2.txt)
- ✅ Updated extractor (extractor.py)
- ✅ **Analysis Engine orchestration** (core/analysis_engine.py)
- ✅ Complete UI with progress tracking (app.py)

**Files Created/Modified in Sprint 3:**
- NEW: `models/signal_models.py` (87 lines)
- NEW: `validators/citation_validator.py` (176 lines)
- NEW: `validators/confidence_filter.py` (134 lines)
- NEW: `validators/cross_reference.py` (146 lines)
- NEW: `validators/llm_fact_checker.py` (209 lines)
- NEW: `core/analysis_engine.py` (298 lines)
- NEW: `prompts/extract_signals_v2.txt` (73 lines)
- UPDATED: `extractor.py` (233 lines)
- UPDATED: `app.py` (428 lines)

**Total Lines Added:** ~2,100+ lines

### 🚧 SPRINT 4: Report Generation (PENDING)
- ⏳ Report templates
- ⏳ PDF generation
- ⏳ Email notifications
- ⏳ Scheduling

### 🚧 SPRINT 5: Production Polish (PENDING)
- ⏳ Error handling improvements
- ⏳ Performance optimization
- ⏳ Documentation
- ⏳ Final testing

---

## 🎯 Next Steps

1. **Test on Streamlit Cloud** - Deploy und live testen
2. **Iterate based on feedback** - Bugs fixen, UX verbessern
3. **Sprint 4** - Report generation (wenn Sprint 3 stabil)

---

**Current Status:** 🔥 Sprint 3 deployed to GitHub  
**Git Commit:** ea71b3b - "feat: Sprint 3 complete - Signal extraction with 7-layer anti-hallucination"  
**Deployed URL:** https://github.com/revoic/e-commerce_analyse  

🚀 **Ready for live testing!**
