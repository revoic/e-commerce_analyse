-- E-Commerce Intelligence Tool Database Schema
-- Version 2.0 - Multi-Company Support

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ==============================================================================
-- COMPANIES: Multi-Company Support
-- ==============================================================================
CREATE TABLE IF NOT EXISTS companies (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  domain text,
  newsroom_url text,
  linkedin_url text,
  config jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  CONSTRAINT companies_name_domain_unique UNIQUE(name, domain)
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_created ON companies(created_at DESC);

-- ==============================================================================
-- ANALYSES: Job Tracking & History
-- ==============================================================================
CREATE TABLE IF NOT EXISTS analyses (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES companies(id) ON DELETE CASCADE,
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  progress jsonb DEFAULT '{}'::jsonb,
  lookback_days int DEFAULT 14,
  max_sources int DEFAULT 50,
  started_at timestamptz,
  completed_at timestamptz,
  error_message text,
  result_json jsonb,
  validation_stats jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analyses_company ON analyses(company_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at DESC);

-- ==============================================================================
-- SOURCES: Linked to Analysis
-- ==============================================================================
CREATE TABLE IF NOT EXISTS sources (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id uuid REFERENCES analyses(id) ON DELETE CASCADE,
  url text NOT NULL,
  title text,
  source_type text,
  published_at timestamptz,
  language text,
  raw_text text NOT NULL,
  text_hash text NOT NULL,
  fetch_timestamp timestamptz DEFAULT now(),
  http_status_code int,
  is_eu_source boolean DEFAULT false,
  has_ecommerce_keywords boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT sources_analysis_hash_unique UNIQUE(analysis_id, text_hash)
);

CREATE INDEX IF NOT EXISTS idx_sources_analysis ON sources(analysis_id);
CREATE INDEX IF NOT EXISTS idx_sources_hash ON sources(text_hash);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_eu ON sources(is_eu_source) WHERE is_eu_source = true;
CREATE INDEX IF NOT EXISTS idx_sources_ecom ON sources(has_ecommerce_keywords) WHERE has_ecommerce_keywords = true;

-- Full-text search index (German)
CREATE INDEX IF NOT EXISTS idx_sources_text_search ON sources USING gin(to_tsvector('german', raw_text));

-- ==============================================================================
-- SIGNALS: Validated Extractions
-- ==============================================================================
CREATE TABLE IF NOT EXISTS signals (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id uuid REFERENCES analyses(id) ON DELETE CASCADE,
  source_id uuid REFERENCES sources(id),
  type text NOT NULL,
  value jsonb NOT NULL,
  verbatim_quote text NOT NULL,
  source_title text,
  source_url text,
  confidence numeric CHECK (confidence >= 0 AND confidence <= 1),
  fact_check_status text CHECK (fact_check_status IN ('verified', 'partially_correct', 'incorrect', 'cannot_verify')),
  corroboration_count int DEFAULT 0,
  corroborating_sources jsonb DEFAULT '[]'::jsonb,
  validation_status text DEFAULT 'pending',
  rejection_reason text,
  detected_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_signals_analysis ON signals(analysis_id);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(type);
CREATE INDEX IF NOT EXISTS idx_signals_validation ON signals(validation_status);
CREATE INDEX IF NOT EXISTS idx_signals_fact_check ON signals(fact_check_status);

-- Full-text search on quotes
CREATE INDEX IF NOT EXISTS idx_signals_quote_search ON signals USING gin(to_tsvector('german', verbatim_quote));

-- ==============================================================================
-- LEGACY SUPPORT: Keep old company/source tables for backward compatibility
-- ==============================================================================

-- Old company table (keep for now, but deprecated)
CREATE TABLE IF NOT EXISTS company (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  domain text,
  notes jsonb,
  created_at timestamptz DEFAULT now()
);

-- Old source table (keep for now, but deprecated)
CREATE TABLE IF NOT EXISTS source (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES company(id),
  url text,
  title text,
  published_at timestamptz,
  language text,
  raw_text text,
  hash text UNIQUE,
  embedding vector(1536)
);

-- Old signal table (keep for now, but deprecated)
CREATE TABLE IF NOT EXISTS signal (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES company(id),
  type text,
  value jsonb,
  confidence numeric,
  source_ids uuid[],
  detected_at timestamptz DEFAULT now()
);

-- ==============================================================================
-- HELPER FUNCTIONS
-- ==============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for companies table
DROP TRIGGER IF EXISTS companies_updated_at ON companies;
CREATE TRIGGER companies_updated_at
  BEFORE UPDATE ON companies
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- ==============================================================================
-- VIEWS FOR CONVENIENCE
-- ==============================================================================

-- Latest analyses per company
CREATE OR REPLACE VIEW latest_analyses AS
SELECT DISTINCT ON (company_id)
  a.*,
  c.name as company_name,
  c.domain as company_domain
FROM analyses a
JOIN companies c ON c.id = a.company_id
ORDER BY company_id, created_at DESC;

-- Analyses with signal counts
CREATE OR REPLACE VIEW analyses_summary AS
SELECT
  a.id,
  a.company_id,
  c.name as company_name,
  a.status,
  a.created_at,
  a.completed_at,
  COUNT(DISTINCT s.id) as source_count,
  COUNT(DISTINCT sig.id) as signal_count,
  AVG(sig.confidence) as avg_confidence,
  a.validation_stats
FROM analyses a
JOIN companies c ON c.id = a.company_id
LEFT JOIN sources s ON s.analysis_id = a.id
LEFT JOIN signals sig ON sig.analysis_id = a.id
GROUP BY a.id, a.company_id, c.name, a.status, a.created_at, a.completed_at, a.validation_stats;

-- ==============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ==============================================================================

COMMENT ON TABLE companies IS 'Companies that can be analyzed';
COMMENT ON TABLE analyses IS 'Individual analysis runs for companies with job tracking';
COMMENT ON TABLE sources IS 'Scraped sources (news, linkedin, etc.) for each analysis';
COMMENT ON TABLE signals IS 'Validated, fact-checked signals extracted from sources';

COMMENT ON COLUMN signals.verbatim_quote IS 'MANDATORY: Exact quote from source text for verification';
COMMENT ON COLUMN signals.fact_check_status IS 'Result of LLM fact-checking pass';
COMMENT ON COLUMN signals.corroboration_count IS 'Number of additional sources confirming this signal';
COMMENT ON COLUMN signals.validation_status IS 'Overall validation status (pending/verified/rejected)';
