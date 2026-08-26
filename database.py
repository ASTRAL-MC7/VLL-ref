import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    dsn = DATABASE_URL
    # Neon URLs usually include sslmode=require, which asyncpg understands
    # directly. If your DSN has no sslmode, force ssl so Neon accepts it.
    ssl_arg = "require" if "sslmode" not in dsn else None
    _pool = await asyncpg.create_pool(dsn=dsn, ssl=ssl_arg, min_size=1, max_size=10)
    await _create_tables()
    return _pool


def pool() -> asyncpg.Pool:
    assert _pool is not None, "DB pool not initialized yet"
    return _pool


async def _create_tables():
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                vcoin INTEGER NOT NULL DEFAULT 0,
                ref_count INTEGER NOT NULL DEFAULT 0,
                referred_by BIGINT,
                is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS pending_referrals (
                user_id BIGINT PRIMARY KEY,
                referrer_id BIGINT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                content_type TEXT,
                file_id TEXT,
                text_content TEXT
            );
            """
        )


# ---------------- users ----------------

async def get_user(user_id: int):
    async with _pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)


async def is_verified(user_id: int) -> bool:
    row = await get_user(user_id)
    return bool(row and row["is_verified"])


async def stash_pending_referral(user_id: int, referrer_id: int):
    """Remember who invited this (not-yet-verified) user, applied on verification."""
    if user_id == referrer_id:
        return
    async with _pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        if existing:  # already registered before, don't overwrite/re-credit
            return
        await conn.execute(
            """
            INSERT INTO pending_referrals (user_id, referrer_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id, referrer_id,
        )


async def register_and_verify(user_id: int, username: str, first_name: str) -> bool:
    """
    Marks user verified. Creates the row if needed, credits the +1 vcoin
    registration bonus (only once), and applies a pending referral if any.
    Returns True if this was a first-time registration.
    """
    async with _pool.acquire() as conn:
        async with conn.transaction():
            existing = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
            if existing and existing["is_verified"]:
                return False  # nothing to do, already fully registered

            if existing:
                await conn.execute(
                    "UPDATE users SET is_verified=TRUE, username=$2, first_name=$3 WHERE user_id=$1",
                    user_id, username, first_name,
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, vcoin, ref_count, is_verified)
                    VALUES ($1, $2, $3, 1, 0, TRUE)
                    """,
                    user_id, username, first_name,
                )

            pending = await conn.fetchrow(
                "SELECT referrer_id FROM pending_referrals WHERE user_id=$1", user_id
            )
            if pending:
                referrer_id = pending["referrer_id"]
                await conn.execute(
                    "UPDATE users SET ref_count = ref_count + 1, vcoin = vcoin + 1 WHERE user_id=$1",
                    referrer_id,
                )
                await conn.execute(
                    "UPDATE users SET referred_by=$2 WHERE user_id=$1", user_id, referrer_id
                )
                await conn.execute("DELETE FROM pending_referrals WHERE user_id=$1", user_id)

            return True


async def get_referrer_id(user_id: int):
    row = await get_user(user_id)
    return row["referred_by"] if row else None


async def add_vcoin(user_id: int, amount: int):
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET vcoin = vcoin + $2 WHERE user_id=$1", user_id, amount
        )


async def add_ref_count(user_id: int, amount: int):
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET ref_count = GREATEST(ref_count + $2, 0) WHERE user_id=$1",
            user_id, amount,
        )


async def count_users() -> int:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS c FROM users WHERE is_verified=TRUE")
        return row["c"]


async def get_top(n: int = 10):
    async with _pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, username, first_name, ref_count
            FROM users
            WHERE is_verified=TRUE
            ORDER BY ref_count DESC, joined_at ASC
            LIMIT $1
            """,
            n,
        )


async def get_rank(user_id: int):
    """Returns (rank, ref_count) for this user, 1-indexed."""
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT rank, ref_count FROM (
                SELECT user_id, ref_count,
                       RANK() OVER (ORDER BY ref_count DESC, joined_at ASC) AS rank
                FROM users
                WHERE is_verified=TRUE
            ) sub
            WHERE user_id=$1
            """,
            user_id,
        )
        if not row:
            return None, 0
        return row["rank"], row["ref_count"]


# ---------------- referral message template ----------------

async def set_ref_message(content_type: str, file_id: str | None, text_content: str | None):
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO settings (key, content_type, file_id, text_content)
            VALUES ('ref_message', $1, $2, $3)
            ON CONFLICT (key) DO UPDATE
                SET content_type=$1, file_id=$2, text_content=$3
            """,
            content_type, file_id, text_content,
        )


async def get_ref_message():
    async with _pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM settings WHERE key='ref_message'")
