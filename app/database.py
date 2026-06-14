from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Створюємо асинхронний engine для зв'язку з Postgres
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Фабрика для створення асинхронних сесій (роботи з запитами)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Базовий клас, від якого будуть наслідуватися всі наші таблиці
class Base(DeclarativeBase):
    pass

# Функція-залежність для FastAPI, яка видає підключення на кожен запит
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session