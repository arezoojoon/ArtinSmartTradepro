import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
                is_superuser=True,
            )
            session.add(user)
            await session.commit()
            logger.info(f"Superuser {settings.FIRST_SUPERUSER} created")
        else:
            logger.info(f"Superuser {settings.FIRST_SUPERUSER} already exists")

if __name__ == "__main__":
    asyncio.run(init_db())
