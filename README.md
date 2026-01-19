# 🛒 E-Commerce Intelligence Tool

AI-powered intelligence gathering for E-Commerce insights with focus on EU/DE markets.

## 🎯 Features

- 🌐 **Multi-Company Support**: Analyze any company
- 🇪🇺 **EU/DE Focus**: Specialized on European markets
- 🛒 **E-Commerce Intelligence**: Tracks marketplace, retail media, D2C activities
- 🔍 **Multi-Source Discovery**: Google News (14 EU editions), LinkedIn, Company Newsrooms
- 🛡️ **7-Layer Validation**: Anti-hallucination system for 100% fact-based reports
- 📊 **Interactive Dashboard**: Streamlit-based UI with analysis history
- 💾 **Dual-Mode**: Works with PostgreSQL or JSON fallback

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/revoic/e-commerce_analyse.git
cd e-commerce_analyse
```

### 2. Install Dependencies

```bash
pip install -r pernod_ricard_agent_repo_full/requirements.txt
```

### 3. Set API Key

Create Streamlit secrets file:

```bash
mkdir -p ~/.streamlit
echo 'OPENAI_API_KEY = "sk-proj-YOUR-KEY-HERE"' > ~/.streamlit/secrets.toml
```

### 4. Run App

```bash
cd pernod_ricard_agent_repo_full
streamlit run app.py
```

## 📋 Configuration

### Required Secrets

- `OPENAI_API_KEY`: OpenAI API key (required)

### Optional Secrets

- `DATABASE_URL`: PostgreSQL connection string (optional, uses JSON fallback if not provided)
- `OPENAI_MODEL`: Model to use (default: `gpt-4o-mini`)

## 🗄️ Database Setup (Optional)

If you want to use PostgreSQL for history and multi-user support:

1. Create a database (e.g., via [Supabase](https://supabase.com) free tier)
2. Run the schema:

```bash
psql $DATABASE_URL < pernod_ricard_agent_repo_full/models.sql
```

3. Add `DATABASE_URL` to your secrets

## 🌍 Deployment

### Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from repository
4. Add secrets in Advanced Settings:
   ```toml
   OPENAI_API_KEY = "sk-proj-..."
   DATABASE_URL = "postgresql://..." # optional
   ```

## 📖 Documentation

- [Transformation Plan](PROJECT_TRANSFORMATION_PLAN.md) - Complete project documentation
- [Database Schema](pernod_ricard_agent_repo_full/models.sql) - PostgreSQL tables

## 🏗️ Architecture

```
pernod_ricard_agent_repo_full/
├── app.py                    # Streamlit UI
├── db.py                     # Database (with JSON fallback)
├── models.sql                # PostgreSQL schema
├── core/                     # Business logic
│   ├── scraper.py           # Multi-source intelligence gathering
│   ├── extractor.py         # LLM-based signal extraction
│   └── analysis_engine.py   # Orchestration
├── validators/               # 7-layer validation system
│   ├── citation_validator.py
│   ├── confidence_filter.py
│   └── cross_reference.py
├── models/                   # Pydantic data models
├── utils/                    # Utilities
└── tests/                    # Test suite
```

## 🔒 Anti-Hallucination System

7-layer validation ensures fact-based reports:

1. **Source Verification**: Hash-based integrity checks
2. **Citation Enforcement**: Mandatory verbatim quotes
3. **Schema Validation**: Pydantic models with strict rules
4. **Confidence Filtering**: Only ≥0.70 confidence signals
5. **Cross-Reference**: Multi-source corroboration
6. **LLM Fact-Check**: Second verification pass
7. **Transparent Reporting**: Every claim cited

**Expected rejection rate:** 40-60% (quality over quantity!)

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Database**: PostgreSQL (optional)
- **LLM**: OpenAI (gpt-4o-mini / gpt-4o)
- **Scraping**: httpx, BeautifulSoup, feedparser
- **Validation**: Pydantic

## 📊 Example Usage

```python
from core.scraper import discover_company_sources

# Discover sources for any company
sources = discover_company_sources("Zalando", {
    "lookback_days": 14,
    "max_per_source": 10
})

print(f"Found {len(sources)} sources")
```

## 🧪 Testing

```bash
pytest pernod_ricard_agent_repo_full/tests/
```

## 📝 License

Proprietary - Revoic Project

## 🤝 Contributing

Internal project - contact team for access.

## 📧 Contact

For questions or issues, contact the Revoic team.

---

**Version:** 2.0  
**Status:** Production Ready (MVP)  
**Last Updated:** January 2026
