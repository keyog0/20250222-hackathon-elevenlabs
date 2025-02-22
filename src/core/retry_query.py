from sqlalchemy.orm.query import Query as _Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, StatementError
from asyncio import sleep as async_sleep
from time import sleep
from loguru import logger


class RetryingQuery(_Query):
    __max_retry_count__ = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        attempts = 0
        while True:
            attempts += 1
            try:
                return super().__iter__()
            except OperationalError as ex:
                if "server closed the connection unexpectedly" not in str(ex):
                    raise
                if attempts <= self.__max_retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    logger.error(
                        "/!\ Database connection error: retrying Strategy => sleeping for {}s"
                        " and will retry (attempt #{} of {}) \n Detailed query impacted: {}".format(
                            sleep_for, attempts, self.__max_retry_count__, ex
                        )
                    )
                    sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as ex:
                if "reconnect until invalid transaction is rolled back" not in str(ex):
                    raise
                self.session.rollback()


class AsyncRetryingQuery:
    __max_retry_count__ = 3

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def execute(self, query):
        attempts = 0
        while True:
            attempts += 1
            try:
                return await self.async_session.execute(query)
            except OperationalError as ex:
                if "server closed the connection unexpectedly" not in str(ex):
                    raise
                if attempts <= self.__max_retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    logger.error(
                        "/!\ Database connection error: retrying Strategy => sleeping for {}s"
                        " and will retry (attempt #{} of {}) \n Detailed query impacted: {}".format(
                            sleep_for, attempts, self.__max_retry_count__, ex
                        )
                    )
                    await async_sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as ex:
                if "reconnect until invalid transaction is rolled back" not in str(ex):
                    raise
                await self.async_session.rollback()
