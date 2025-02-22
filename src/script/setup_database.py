from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from core.database import Base, engine, get_session_context
from core.models.user import UserModel

# 다른 모델들도 여기서 임포트해야 합니다.


def setup_database():
    try:
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return

    try:
        logger.info("Creating admin user")
        with get_session_context() as session:
            if not session.execute(select(UserModel).where(UserModel.email == "admin")).scalar_one_or_none():
                user = UserModel(
                    email="admin",
                    password="admin",
                    nickname="admin",
                    role="admin",
                    profile_image_url="https://via.placeholder.com/150",
                    is_active=True,
                    name="admin",
                    phone_number="01012345678",
                    birthdate="1990-01-01",
                    gender="male",
                )
                session.add(user)
            session.commit()
        logger.info("Admin user created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return

    logger.info("Database setup completed")


if __name__ == "__main__":
    setup_database()
