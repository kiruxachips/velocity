# db_async.py
import asyncio
from contextlib import asynccontextmanager
import aiomysql
from app.config.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET

_pool_lock = asyncio.Lock()
_DB_POOL = None


async def _create_pool():
    return await aiomysql.create_pool(
        host=DB_HOST,
        port=int(DB_PORT or 3306),
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset=DB_CHARSET,
        autocommit=True,
        connect_timeout=5,
        cursorclass=aiomysql.DictCursor,  # курсоры сразу dict
    )


async def init_pool():
    """
    Безопасно создаёт пул: одновременно запускается только один connect.
    """
    global _DB_POOL
    if _DB_POOL is None:
        async with _pool_lock:
            if _DB_POOL is None:          # двойная проверка
                missing = [k for k in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME") if not globals().get(k)]
                if missing:
                    raise RuntimeError(f"Отсутствуют переменные окружения: {', '.join(missing)}")
                _DB_POOL = await _create_pool()
    return _DB_POOL


async def close_pool():
    global _DB_POOL
    if _DB_POOL is not None:
        _DB_POOL.close()
        await _DB_POOL.wait_closed()
        _DB_POOL = None


@asynccontextmanager
async def get_conn():
    """
    Асинхронный контекст-менеджер — удобнее, чем две вложенных with.
    """
    pool = await init_pool()
    async with pool.acquire() as conn:
        yield conn


async def fetch_user_courses(telegram_id: int):
    """
    Возвращает список курсов, на которые подписан пользователь.
    """
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT c.id, c.title, c.description
                FROM users u
                JOIN enrollments e ON u.id = e.user_id
                JOIN courses c ON e.course_id = c.id
                WHERE u.telegram_id = %s
                """,
                (telegram_id,),
            )
            return await cur.fetchall()
