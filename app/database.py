from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

async_engine = create_async_engine(
    url="mysql+aiomysql://root:123456@localhost:3306/message_push?charset=utf8",
    echo=True,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with async_session() as session:
        yield session
