from typing import Generator, Any

import pytest
import os
from dotenv import load_dotenv

from sangsangstudio.clock import Clock, SystemClock
from sangsangstudio.repositories import (
    MySQLConnector, MySQLRepository)


load_dotenv()


@pytest.fixture
def mysql_host():
    return os.getenv("MYSQL_HOST")


@pytest.fixture
def mysql_password():
    return os.getenv("MYSQL_PASSWORD")


@pytest.fixture
def mysql_port():
    return int(os.getenv("MYSQL_PORT", default=3306))


@pytest.fixture
def mysql_user():
    return os.getenv("MYSQL_USER")


@pytest.fixture
def mysql_database():
    return os.getenv("MYSQL_DATABASE")


@pytest.fixture
def mysql_connector(mysql_user, mysql_host, mysql_password, mysql_port, mysql_database):
    connector = MySQLConnector(
        user=mysql_user,
        database=mysql_database,
        host=mysql_host,
        port=mysql_port,
        password=mysql_password)
    return connector


@pytest.fixture
def repository(mysql_connector, clock) -> Generator[MySQLRepository, Any, None]:
    repository = MySQLRepository(mysql_connector, clock)
    repository.create_tables()
    yield repository
    repository.drop_tables()


@pytest.fixture
def clock() -> Clock:
    return SystemClock()
