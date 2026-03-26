const SCHEMA_SQL = [
  `CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    mfa_enabled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    ip TEXT,
    user_agent TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`,
  `CREATE TABLE IF NOT EXISTS workflow_requests (
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
  )`,
  `CREATE TABLE IF NOT EXISTS workflow_events (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES workflow_requests(id)
  )`,
  `CREATE TABLE IF NOT EXISTS policy_decisions (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    allowed INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS ops_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS chat_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    route TEXT,
    model TEXT,
    prompt_chars INTEGER NOT NULL,
    response_chars INTEGER NOT NULL,
    created_at TEXT NOT NULL
  )`,
];

async function ensureSchema(env) {
  if (!env?.DB) return false;
  if (globalThis.__acmvp_schema_ready__) return true;
  for (const q of SCHEMA_SQL) {
    await env.DB.prepare(q).run();
  }
  const now = new Date().toISOString();
  await env.DB.prepare(
    `INSERT OR IGNORE INTO users (id, email, password_hash, role, mfa_enabled, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, 0, ?5, ?5)`,
  )
    .bind("u_admin", "admin@acmvp.local", "demo1234", "admin", now)
    .run();
  await env.DB.prepare(
    `INSERT OR IGNORE INTO users (id, email, password_hash, role, mfa_enabled, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, 0, ?5, ?5)`,
  )
    .bind("u_operator", "operator@acmvp.local", "demo1234", "operator", now)
    .run();
  globalThis.__acmvp_schema_ready__ = true;
  return true;
}

export { ensureSchema };
