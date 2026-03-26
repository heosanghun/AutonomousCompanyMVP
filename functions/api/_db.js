import { hashPassword } from "./_crypto.js";

const SCHEMA_SQL = [
  `CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    mfa_enabled INTEGER NOT NULL DEFAULT 0,
    mfa_secret TEXT,
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
  try {
    await env.DB.prepare(`ALTER TABLE users ADD COLUMN mfa_secret TEXT`).run();
  } catch (_) {}
  const now = new Date().toISOString();
  const demoHash = await hashPassword("demo1234", String(env?.AUTH_PEPPER || ""));
  await env.DB.prepare(
    `INSERT OR IGNORE INTO users (id, email, password_hash, role, mfa_enabled, mfa_secret, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, 0, NULL, ?5, ?5)`,
  )
    .bind("u_admin", "admin@acmvp.local", demoHash, "admin", now)
    .run();
  await env.DB.prepare(
    `INSERT OR IGNORE INTO users (id, email, password_hash, role, mfa_enabled, mfa_secret, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, 0, NULL, ?5, ?5)`,
  )
    .bind("u_operator", "operator@acmvp.local", demoHash, "operator", now)
    .run();
  const oldUsers = await env.DB.prepare(`SELECT id, password_hash FROM users`).all();
  for (const u of oldUsers.results || []) {
    const ph = String(u.password_hash || "");
    if (!ph.startsWith("sha256$")) {
      const migrated = await hashPassword(ph, String(env?.AUTH_PEPPER || ""));
      await env.DB.prepare(`UPDATE users SET password_hash = ?2, updated_at = ?3 WHERE id = ?1`).bind(u.id, migrated, now).run();
    }
  }
  globalThis.__acmvp_schema_ready__ = true;
  return true;
}

export { ensureSchema };
