function hexFromBytes(bytes) {
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function bytesFromHex(hex) {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) out[i / 2] = parseInt(hex.slice(i, i + 2), 16);
  return out;
}

async function sha256Hex(input) {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return hexFromBytes(new Uint8Array(digest));
}

function randomHex(nBytes = 16) {
  const u8 = crypto.getRandomValues(new Uint8Array(nBytes));
  return hexFromBytes(u8);
}

async function hashPassword(password, pepper = "") {
  const salt = randomHex(16);
  const digest = await sha256Hex(`${salt}:${password}:${pepper}`);
  return `sha256$${salt}$${digest}`;
}

async function verifyPassword(password, storedHash, pepper = "") {
  const raw = String(storedHash || "");
  if (!raw.includes("$")) return raw === password;
  const [alg, salt, digest] = raw.split("$");
  if (alg !== "sha256" || !salt || !digest) return false;
  const got = await sha256Hex(`${salt}:${password}:${pepper}`);
  return got === digest;
}

const B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

function base32Decode(input) {
  const clean = String(input || "").toUpperCase().replace(/=+$/g, "").replace(/[^A-Z2-7]/g, "");
  let bits = "";
  for (const c of clean) {
    const v = B32.indexOf(c);
    if (v < 0) continue;
    bits += v.toString(2).padStart(5, "0");
  }
  const out = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) out.push(parseInt(bits.slice(i, i + 8), 2));
  return new Uint8Array(out);
}

function generateBase32Secret(length = 32) {
  const rnd = crypto.getRandomValues(new Uint8Array(length));
  let out = "";
  for (let i = 0; i < length; i += 1) out += B32[rnd[i] % B32.length];
  return out;
}

async function hmacSha1(keyBytes, msgBytes) {
  const key = await crypto.subtle.importKey("raw", keyBytes, { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, msgBytes);
  return new Uint8Array(sig);
}

async function totpCode(secret, step = 30, digits = 6, epochMs = Date.now()) {
  const counter = Math.floor(epochMs / 1000 / step);
  const buf = new ArrayBuffer(8);
  const view = new DataView(buf);
  view.setUint32(0, Math.floor(counter / 2 ** 32), false);
  view.setUint32(4, counter >>> 0, false);
  const mac = await hmacSha1(base32Decode(secret), new Uint8Array(buf));
  const off = mac[mac.length - 1] & 0xf;
  const bin = ((mac[off] & 0x7f) << 24) | ((mac[off + 1] & 0xff) << 16) | ((mac[off + 2] & 0xff) << 8) | (mac[off + 3] & 0xff);
  const otp = bin % 10 ** digits;
  return String(otp).padStart(digits, "0");
}

async function verifyTotp(secret, code) {
  const c = String(code || "").trim();
  if (!/^\d{6}$/.test(c)) return false;
  const now = Date.now();
  const windowMs = 30_000;
  const checks = [now - windowMs, now, now + windowMs];
  for (const t of checks) {
    const expected = await totpCode(secret, 30, 6, t);
    if (expected === c) return true;
  }
  return false;
}

export { generateBase32Secret, hashPassword, verifyPassword, verifyTotp };
