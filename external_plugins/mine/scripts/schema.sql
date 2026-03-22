-- tested with: claude code v2.1.81
-- mine schema v2
-- Claude Code conversation history mining database
-- PRAGMA journal_mode=WAL set by mine.py at connection time

PRAGMA foreign_keys = ON;

-- ============================================================
-- META: schema versioning
-- ============================================================
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', '2');
INSERT OR IGNORE INTO meta (key, value) VALUES ('created_at', datetime('now'));

-- ============================================================
-- SESSIONS: one row per JSONL file (main session or subagent)
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    slug TEXT,
    project_dir TEXT,
    cwd TEXT,
    project_name TEXT,
    git_branch TEXT,
    model TEXT,
    version TEXT,
    permission_mode TEXT,
    start_time TEXT,
    end_time TEXT,
    duration_wall_seconds INTEGER,
    duration_active_seconds INTEGER,
    message_count INTEGER DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    assistant_message_count INTEGER DEFAULT 0,
    tool_use_count INTEGER DEFAULT 0,
    thinking_block_count INTEGER DEFAULT 0,
    user_prompt_count INTEGER DEFAULT 0,
    api_call_count INTEGER DEFAULT 0,
    compaction_count INTEGER DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_cache_creation_tokens INTEGER DEFAULT 0,
    total_cache_read_tokens INTEGER DEFAULT 0,
    is_subagent BOOLEAN DEFAULT FALSE,
    parent_session_id TEXT,
    agent_id TEXT,
    first_user_prompt TEXT,
    file_path TEXT,
    file_size_bytes INTEGER,
    file_mtime TEXT,
    parsed_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- MESSAGES: every user and assistant message
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    uuid TEXT,
    parent_uuid TEXT,
    type TEXT NOT NULL,
    role TEXT,
    model TEXT,
    content_preview TEXT,
    has_tool_use BOOLEAN DEFAULT FALSE,
    has_thinking BOOLEAN DEFAULT FALSE,
    stop_reason TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_creation_tokens INTEGER,
    cache_read_tokens INTEGER,
    service_tier TEXT,
    inference_geo TEXT,
    request_id TEXT,
    is_sidechain BOOLEAN DEFAULT FALSE,
    agent_id TEXT,
    user_type TEXT,
    line_number INTEGER,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- ============================================================
-- TOOL_CALLS: every tool invocation from assistant messages
-- ============================================================
CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_uuid TEXT,
    tool_use_id TEXT,
    tool_name TEXT NOT NULL,
    input_summary TEXT,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- ============================================================
-- SUBAGENTS: subagent lifecycle tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS subagents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_session_id TEXT NOT NULL,
    agent_id TEXT,
    agent_type TEXT,
    transcript_path TEXT,
    start_time TEXT,
    end_time TEXT,
    duration_seconds INTEGER,
    message_count INTEGER DEFAULT 0,
    tool_use_count INTEGER DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

-- ============================================================
-- ERRORS: tool failures (from PostToolUseFailure or JSONL)
-- ============================================================
CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT,
    input_summary TEXT,
    error_message TEXT,
    is_interrupt BOOLEAN DEFAULT FALSE,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- ============================================================
-- PROJECT_PATHS: tracks every location a project has lived
-- ============================================================
CREATE TABLE IF NOT EXISTS project_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    project_dir TEXT NOT NULL,
    cwd TEXT,
    first_seen TEXT,
    last_seen TEXT,
    session_count INTEGER DEFAULT 1,
    UNIQUE(project_name, project_dir)
);

-- ============================================================
-- PARSE_LOG: incremental tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS parse_log (
    file_path TEXT PRIMARY KEY,
    file_size INTEGER,
    file_mtime TEXT,
    session_id TEXT,
    parsed_at TEXT DEFAULT (datetime('now')),
    parse_duration_ms INTEGER,
    line_count INTEGER,
    error_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ok'
);

-- ============================================================
-- FTS5: full-text search across prompts and responses
-- ============================================================
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content_preview,
    content='messages',
    content_rowid='id'
);

-- triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content_preview) VALUES (new.id, new.content_preview);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content_preview) VALUES('delete', old.id, old.content_preview);
END;
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content_preview) VALUES('delete', old.id, old.content_preview);
    INSERT INTO messages_fts(rowid, content_preview) VALUES (new.id, new.content_preview);
END;

-- ============================================================
-- MODEL PRICING: historical per-model pricing for accurate cost calculation
-- ============================================================
CREATE TABLE IF NOT EXISTS model_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_pattern TEXT NOT NULL,
    input_per_mtok REAL NOT NULL,
    output_per_mtok REAL NOT NULL,
    cache_read_per_mtok REAL NOT NULL,
    cache_write_per_mtok REAL NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source TEXT,
    UNIQUE(model_pattern, effective_from)
);

-- seed pricing data (idempotent via INSERT OR IGNORE)
INSERT OR IGNORE INTO model_pricing (model_pattern, input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, effective_from, source) VALUES
    ('claude-opus-4-6%', 5.00, 25.00, 0.50, 6.25, '2024-01-01', 'anthropic.com/pricing 2025-05'),
    ('claude-opus-4-5%', 5.00, 25.00, 0.50, 6.25, '2025-02-01', 'anthropic.com/pricing 2025-02'),
    ('claude-opus-4-1%', 15.00, 75.00, 1.50, 18.75, '2025-01-01', 'anthropic.com/pricing 2025-01'),
    ('claude-opus-4-0%', 15.00, 75.00, 1.50, 18.75, '2025-01-01', 'anthropic.com/pricing 2025-01'),
    ('claude-sonnet-4-6%', 3.00, 15.00, 0.30, 3.75, '2024-01-01', 'anthropic.com/pricing 2025-05'),
    ('claude-sonnet-4-5%', 3.00, 15.00, 0.30, 3.75, '2025-06-01', 'anthropic.com/pricing 2025-06'),
    ('claude-sonnet-4-1%', 3.00, 15.00, 0.30, 3.75, '2025-04-01', 'anthropic.com/pricing 2025-04'),
    ('claude-sonnet-4-0%', 3.00, 15.00, 0.30, 3.75, '2025-01-01', 'anthropic.com/pricing 2025-01'),
    ('claude-3-7-sonnet%', 3.00, 15.00, 0.30, 3.75, '2025-01-01', 'anthropic.com/pricing 2025-01'),
    ('claude-3-5-sonnet%', 3.00, 15.00, 0.30, 3.75, '2024-06-01', 'anthropic.com/pricing 2024-06'),
    ('claude-haiku-4-5%', 1.00, 5.00, 0.10, 1.25, '2025-10-01', 'anthropic.com/pricing 2025-10'),
    ('claude-3-5-haiku%', 0.80, 4.00, 0.08, 1.00, '2024-10-01', 'anthropic.com/pricing 2024-10'),
    ('claude-3-haiku%', 0.25, 1.25, 0.03, 0.30, '2024-03-01', 'anthropic.com/pricing 2024-03');

-- ============================================================
-- COSTS VIEW: auto-computed USD per session
-- ============================================================
DROP VIEW IF EXISTS session_costs;
CREATE VIEW IF NOT EXISTS session_costs AS
WITH matched_pricing AS (
    SELECT
        s.id AS session_id,
        mp.input_per_mtok,
        mp.output_per_mtok,
        mp.cache_read_per_mtok,
        mp.cache_write_per_mtok,
        ROW_NUMBER() OVER (
            PARTITION BY s.id
            ORDER BY mp.effective_from DESC
        ) AS rn
    FROM sessions s
    JOIN model_pricing mp ON s.model LIKE mp.model_pattern
        AND mp.effective_from <= COALESCE(s.start_time, '9999-12-31')
        AND (mp.effective_to IS NULL OR mp.effective_to > COALESCE(s.start_time, '0000-01-01'))
)
SELECT
    s.id,
    s.is_subagent,
    s.project_name,
    s.model,
    s.start_time,
    s.total_input_tokens,
    s.total_output_tokens,
    s.total_cache_creation_tokens,
    s.total_cache_read_tokens,
    COALESCE(
        COALESCE(s.total_input_tokens, 0) * COALESCE(mp.input_per_mtok, 0) / 1e6
        + COALESCE(s.total_cache_read_tokens, 0) * COALESCE(mp.cache_read_per_mtok, 0) / 1e6
        + COALESCE(s.total_cache_creation_tokens, 0) * COALESCE(mp.cache_write_per_mtok, 0) / 1e6
        + COALESCE(s.total_output_tokens, 0) * COALESCE(mp.output_per_mtok, 0) / 1e6,
        0
    ) AS estimated_cost_usd
FROM sessions s
LEFT JOIN matched_pricing mp ON s.id = mp.session_id AND mp.rn = 1;

-- ============================================================
-- CONVENIENCE VIEWS
-- ============================================================

-- user session costs (excludes subagents — the most common query pattern)
-- use this instead of "sessions s JOIN session_costs sc ... WHERE is_subagent = 0"
DROP VIEW IF EXISTS user_session_costs;
CREATE VIEW IF NOT EXISTS user_session_costs AS
SELECT
    sc.id,
    sc.project_name,
    sc.model,
    sc.start_time,
    sc.total_input_tokens,
    sc.total_output_tokens,
    sc.total_cache_creation_tokens,
    sc.total_cache_read_tokens,
    sc.estimated_cost_usd,
    s.duration_wall_seconds,
    s.duration_active_seconds,
    s.message_count,
    s.user_message_count,
    s.tool_use_count,
    s.compaction_count,
    s.first_user_prompt,
    s.git_branch,
    s.cwd,
    s.version,
    s.permission_mode
FROM session_costs sc
JOIN sessions s ON sc.id = s.id
WHERE sc.is_subagent = 0
  AND sc.model IS NOT NULL AND sc.model != '' AND sc.model != '<synthetic>';

-- project-level cost summary (most useful view for dashboards)
DROP VIEW IF EXISTS project_costs;
CREATE VIEW IF NOT EXISTS project_costs AS
SELECT
    s.project_name,
    COUNT(*) AS sessions,
    SUM(CASE WHEN s.is_subagent = 0 THEN 1 ELSE 0 END) AS main_sessions,
    SUM(CASE WHEN s.is_subagent = 1 THEN 1 ELSE 0 END) AS subagent_sessions,
    SUM(s.total_input_tokens) AS input_tokens,
    SUM(s.total_output_tokens) AS output_tokens,
    SUM(s.total_cache_creation_tokens) AS cache_creation_tokens,
    SUM(s.total_cache_read_tokens) AS cache_read_tokens,
    SUM(sc.estimated_cost_usd) AS estimated_cost_usd,
    MIN(s.start_time) AS first_session,
    MAX(s.start_time) AS last_session,
    SUM(s.tool_use_count) AS tool_calls
FROM sessions s
JOIN session_costs sc ON s.id = sc.id
WHERE s.project_name IS NOT NULL
GROUP BY s.project_name;

-- daily cost summary (for trend analysis — user sessions only)
DROP VIEW IF EXISTS daily_costs;
CREATE VIEW IF NOT EXISTS daily_costs AS
SELECT
    SUBSTR(sc.start_time, 1, 10) AS date,
    COUNT(*) AS sessions,
    SUM(sc.total_input_tokens) AS input_tokens,
    SUM(sc.total_output_tokens) AS output_tokens,
    SUM(sc.total_cache_read_tokens) AS cache_read_tokens,
    SUM(sc.estimated_cost_usd) AS estimated_cost_usd
FROM session_costs sc
WHERE sc.start_time IS NOT NULL AND sc.is_subagent = 0
GROUP BY SUBSTR(sc.start_time, 1, 10);

-- tool usage summary (user sessions only)
DROP VIEW IF EXISTS tool_usage;
CREATE VIEW IF NOT EXISTS tool_usage AS
SELECT
    tc.tool_name,
    COUNT(*) AS total_uses,
    COUNT(DISTINCT tc.session_id) AS sessions_used_in,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT tc.session_id), 1) AS avg_per_session
FROM tool_calls tc
JOIN sessions s ON tc.session_id = s.id
WHERE s.is_subagent = 0
GROUP BY tc.tool_name;

-- top model per project (eliminates correlated subquery in SKILL.md)
DROP VIEW IF EXISTS project_top_model;
CREATE VIEW IF NOT EXISTS project_top_model AS
SELECT project_name, model AS top_model FROM (
    SELECT project_name, model, COUNT(*) n,
           ROW_NUMBER() OVER (PARTITION BY project_name ORDER BY COUNT(*) DESC) rn
    FROM sessions
    WHERE is_subagent = 0
      AND model IS NOT NULL AND model != '' AND model != '<synthetic>'
    GROUP BY project_name, model
) WHERE rn = 1;

-- user tool calls with project context (pre-joins + pre-filters is_subagent)
DROP VIEW IF EXISTS user_tool_calls;
CREATE VIEW IF NOT EXISTS user_tool_calls AS
SELECT tc.id, tc.session_id, tc.tool_name, tc.input_summary, tc.timestamp,
       s.project_name
FROM tool_calls tc
JOIN sessions s ON tc.session_id = s.id
WHERE s.is_subagent = 0;

-- ============================================================
-- DAILY ROLLUPS: pre-computed aggregates for fast dashboard queries
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_rollups (
    date TEXT NOT NULL,
    project_name TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    sessions INTEGER DEFAULT 0,
    main_sessions INTEGER DEFAULT 0,
    subagent_sessions INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    tool_calls INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    active_seconds INTEGER DEFAULT 0,
    estimated_cost_usd REAL DEFAULT 0,
    computed_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (date, project_name, model)
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_name);
CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_model ON sessions(model);
CREATE INDEX IF NOT EXISTS idx_sessions_cwd ON sessions(cwd);
CREATE INDEX IF NOT EXISTS idx_sessions_subagent_start ON sessions(is_subagent, start_time);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_name ON tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_timestamp ON tool_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_errors_session ON errors(session_id);
CREATE INDEX IF NOT EXISTS idx_subagents_parent ON subagents(parent_session_id);
CREATE INDEX IF NOT EXISTS idx_parse_log_session ON parse_log(session_id);
CREATE INDEX IF NOT EXISTS idx_project_paths_name ON project_paths(project_name);
CREATE INDEX IF NOT EXISTS idx_model_pricing_pattern ON model_pricing(model_pattern, effective_from);
