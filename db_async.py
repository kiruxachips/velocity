# db_async.py
import asyncio
from contextlib import asynccontextmanager
import aiomysql
import config  # <-- вместо повторного load_dotenv

_pool_lock = asyncio.Lock()
_DB_POOL = None


async def _create_pool():
    return await aiomysql.create_pool(
        host=config.DB_HOST,
        port=int(config.DB_PORT or 3306),
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        db=config.DB_NAME,
        charset=getattr(config, "DB_CHARSET", "utf8mb4"),
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
                missing = [k for k in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME") if not getattr(config, k)]
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
