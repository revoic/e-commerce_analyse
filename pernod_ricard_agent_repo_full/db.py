# db.py - Database management with JSON fallback
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import os
import socket
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import Optional
import json
from datetime import datetime, timezone

try:
    import streamlit as st
except Exception:
    st = None

# ==============================================================================
# DATABASE URL CONFIGURATION
# ==============================================================================

def _get_raw_url() -> Optional[str]:
    """Get DATABASE_URL from environment or Streamlit secrets."""
    url = os.getenv("DATABASE_URL")
    if (not url) and st is not None and "DATABASE_URL" in st.secrets:
        url = st.secrets["DATABASE_URL"]
    return url


def _enforce_ssl_and_ipv4(url: str) -> str:
    """Enforce SSL and resolve IPv4 for better connection stability."""
    u = urlparse(url)
    q = dict(parse_qsl(u.query or "", keep_blank_values=True))
    
    # Force SSL
    q.setdefault("sslmode", "require")
    
    # Try to resolve IPv4 for better stability
    host = u.hostname
    if host:
        try:
            infos = socket.getaddrinfo(host, None, socket.AF_INET)
            if infos:
                ipv4 = infos[0][4][0]
                q["hostaddr"] = ipv4
        except Exception:
            pass
    
    new_query = urlencode(q)
    scheme = "postgresql"
    new_url = urlunparse((
        scheme,
        u.netloc,
        u.path,
        u.params,
        new_query,
        u.fragment
    ))
    return new_url


# ==============================================================================
# DATABASE ENGINE (OPTIONAL)
# ==============================================================================

DATABASE_URL = None
engine = None
USE_DATABASE = False

raw_url = _get_raw_url()
if raw_url:
    try:
        DATABASE_URL = _enforce_ssl_and_ipv4(raw_url)
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            poolclass=NullPool,  # Better for serverless
            connect_args={"connect_timeout": 10},
            echo=False,
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        USE_DATABASE = True
        print("✅ Database connection established")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("   Falling back to JSON mode")
        USE_DATABASE = False
        engine = None
else:
    print("ℹ️ No DATABASE_URL found, using JSON fallback mode")
    USE_DATABASE = False


# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

def init_db():
    """Initialize database schema from models.sql"""
    if not USE_DATABASE or not engine:
        print("⚠️ No database available, skipping initialization")
        return
    
    try:
        with engine.begin() as conn:
            # Read and execute models.sql
            sql_file = os.path.join(os.path.dirname(__file__), 'models.sql')
            if os.path.exists(sql_file):
                with open(sql_file, encoding="utf-8") as f:
                    sql = f.read()
                conn.execute(text(sql))
                print("✅ Database schema initialized")
            else:
                print(f"⚠️ models.sql not found at {sql_file}")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


# ==============================================================================
# HELPER FUNCTIONS - COMPANIES
# ==============================================================================

def get_or_create_company(name: str, domain: Optional[str] = None, 
                          newsroom_url: Optional[str] = None,
                          linkedin_url: Optional[str] = None,
                          config: Optional[dict] = None) -> Optional[str]:
    """
    Get existing company or create new one.
    Returns company_id (uuid as string) or None if no database.
    """
    if not USE_DATABASE or not engine:
        return None
    
    try:
        with engine.begin() as conn:
            # Check if exists
            result = conn.execute(
                text("""
                    SELECT id FROM companies 
                    WHERE LOWER(name) = LOWER(:name)
                    LIMIT 1
                """),
                {"name": name}
            ).fetchone()
            
            if result:
                return str(result[0])
            
            # Create new
            config_json = json.dumps(config or {})
            result = conn.execute(
                text("""
                    INSERT INTO companies (name, domain, newsroom_url, linkedin_url, config)
                    VALUES (:name, :domain, :newsroom_url, :linkedin_url, :config::jsonb)
                    RETURNING id
                """),
                {
                    "name": name,
                    "domain": domain,
                    "newsroom_url": newsroom_url,
                    "linkedin_url": linkedin_url,
                    "config": config_json
                }
            ).fetchone()
            
            return str(result[0])
    except Exception as e:
        print(f"❌ get_or_create_company failed: {e}")
        return None


def get_company(company_id: str) -> Optional[dict]:
    """Get company by ID."""
    if not USE_DATABASE or not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM companies WHERE id = :id"),
                {"id": company_id}
            ).fetchone()
            
            if result:
                return {
                    "id": str(result[0]),
                    "name": result[1],
                    "domain": result[2],
                    "newsroom_url": result[3],
                    "linkedin_url": result[4],
                    "config": result[5],
                    "created_at": result[6],
                    "updated_at": result[7]
                }
    except Exception as e:
        print(f"❌ get_company failed: {e}")
    
    return None


# ==============================================================================
# HELPER FUNCTIONS - ANALYSES
# ==============================================================================

def create_analysis(company_id: str, lookback_days: int = 14, 
                    max_sources: int = 50) -> Optional[str]:
    """
    Create new analysis run.
    Returns analysis_id (uuid as string) or None if no database.
    """
    if not USE_DATABASE or not engine:
        return None
    
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO analyses (company_id, status, lookback_days, max_sources, started_at)
                    VALUES (:company_id, 'running', :lookback_days, :max_sources, :now)
                    RETURNING id
                """),
                {
                    "company_id": company_id,
                    "lookback_days": lookback_days,
                    "max_sources": max_sources,
                    "now": datetime.now(timezone.utc)
                }
            ).fetchone()
            
            return str(result[0])
    except Exception as e:
        print(f"❌ create_analysis failed: {e}")
        return None


def update_analysis_progress(analysis_id: str, progress: dict):
    """Update analysis progress."""
    if not USE_DATABASE or not engine:
        return
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE analyses 
                    SET progress = :progress::jsonb
                    WHERE id = :id
                """),
                {
                    "id": analysis_id,
                    "progress": json.dumps(progress)
                }
            )
    except Exception as e:
        print(f"❌ update_analysis_progress failed: {e}")


def complete_analysis(analysis_id: str, result_json: dict, 
                      validation_stats: dict):
    """Mark analysis as completed."""
    if not USE_DATABASE or not engine:
        return
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE analyses 
                    SET status = 'completed',
                        completed_at = :now,
                        result_json = :result::jsonb,
                        validation_stats = :stats::jsonb
                    WHERE id = :id
                """),
                {
                    "id": analysis_id,
                    "now": datetime.now(timezone.utc),
                    "result": json.dumps(result_json),
                    "stats": json.dumps(validation_stats)
                }
            )
    except Exception as e:
        print(f"❌ complete_analysis failed: {e}")


def fail_analysis(analysis_id: str, error_message: str):
    """Mark analysis as failed."""
    if not USE_DATABASE or not engine:
        return
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE analyses 
                    SET status = 'failed',
                        completed_at = :now,
                        error_message = :error
                    WHERE id = :id
                """),
                {
                    "id": analysis_id,
                    "now": datetime.now(timezone.utc),
                    "error": error_message
                }
            )
    except Exception as e:
        print(f"❌ fail_analysis failed: {e}")


def get_analysis(analysis_id: str) -> Optional[dict]:
    """Get analysis by ID."""
    if not USE_DATABASE or not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM analyses WHERE id = :id"),
                {"id": analysis_id}
            ).fetchone()
            
            if result:
                return {
                    "id": str(result[0]),
                    "company_id": str(result[1]) if result[1] else None,
                    "status": result[2],
                    "progress": result[3],
                    "lookback_days": result[4],
                    "max_sources": result[5],
                    "started_at": result[6],
                    "completed_at": result[7],
                    "error_message": result[8],
                    "result_json": result[9],
                    "validation_stats": result[10],
                    "created_at": result[11]
                }
    except Exception as e:
        print(f"❌ get_analysis failed: {e}")
    
    return None


def get_latest_analyses(limit: int = 10) -> list:
    """Get latest analyses across all companies."""
    if not USE_DATABASE or not engine:
        return []
    
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT 
                        a.id,
                        a.company_id,
                        c.name as company_name,
                        a.status,
                        a.created_at,
                        a.completed_at,
                        (SELECT COUNT(*) FROM signals WHERE analysis_id = a.id) as signal_count
                    FROM analyses a
                    JOIN companies c ON c.id = a.company_id
                    ORDER BY a.created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            return [
                {
                    "id": str(row[0]),
                    "company_id": str(row[1]),
                    "company_name": row[2],
                    "status": row[3],
                    "created_at": row[4],
                    "completed_at": row[5],
                    "signal_count": row[6]
                }
                for row in results
            ]
    except Exception as e:
        print(f"❌ get_latest_analyses failed: {e}")
        return []


# ==============================================================================
# MAIN (for testing)
# ==============================================================================

if __name__ == '__main__':
    if USE_DATABASE:
        print("Initializing database...")
        init_db()
        print("✅ Done")
    else:
        print("❌ No database connection available")
