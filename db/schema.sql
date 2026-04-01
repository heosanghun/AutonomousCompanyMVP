-- Cloudflare D1 schema for AutonomousCompanyMVP backend

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer',
  mfa_enabled INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  ip TEXT,
  user_agent TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS workflow_requests (
  id TEXT PRIMARY KEY,
  request_type TEXT NOT NULL,
  title TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL,
  requested_by TEXT NOT NULL,
  reviewed_by TEXT,
  approved_by TEXT,
  executed_by TEXT,
  audited_by TEXT,
  risk_level TEXT NOT NULL DEFAULT 'medium',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_events (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(request_id) REFERENCES workflow_requests(id)
);

CREATE TABLE IF NOT EXISTS policy_decisions (
  id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  allowed INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ops_events (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- 7. 에이전트 세션 통계 (이미지 11: 사용 통계 분석 대응)
CREATE TABLE IF NOT EXISTS agent_sessions (
  id TEXT PRIMARY KEY,
  request_text TEXT,
  status TEXT DEFAULT 'active', -- active, completed, failed
  start_time TEXT NOT NULL,
  end_time TEXT,
  total_tokens INTEGER DEFAULT 0,
  cost_usd REAL DEFAULT 0.0
);

-- 8. 도구 사용 기록 (이미지 11: 도구 사용 순위 대응)
CREATE TABLE IF NOT EXISTS tool_usage_logs (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  agent_name TEXT,
  tool_name TEXT NOT NULL,
  arguments TEXT,
  status TEXT, -- success, blocked, failed
  created_at TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES agent_sessions(id)
);

-- 9. 실시간 KPI 지표 (이미지 1: 상단 위젯 대응)
CREATE TABLE IF NOT EXISTS system_kpis (
  id TEXT PRIMARY KEY,
  metric_key TEXT UNIQUE, -- total_users, mtd_revenue, etc.
  metric_value REAL,
  updated_at TEXT NOT NULL
);
