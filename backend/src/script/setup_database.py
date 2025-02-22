from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from src.core.database import Base, engine


def setup_database():
    try:
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return

    logger.info("Database setup completed")


if __name__ == "__main__":
    setup_database()
