import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

from sangsangstudio.clock import SystemClock
from sangsangstudio.repositories import MySQLConnector, MySQLRepository
from sangsangstudio.services import PostService, UserService, BcryptPasswordHasher


class AppFactory(ABC):
    @abstractmethod
    def post_service(self) -> PostService:
        pass

    @abstractmethod
    def user_service(self) -> UserService:
        pass


class DevelopmentAppFactory(AppFactory):
    def __init__(self):
        load_dotenv()
        self.mysql_connector = MySQLConnector(
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=os.getenv("MYSQL_HOST"),
            database=os.getenv("MYSQL_DATABASE"),
            port=os.getenv("MYSQL_PORT", 3306))
        self._clock = SystemClock()
        self._repository = MySQLRepository(self.mysql_connector, self._clock)
        self._password_hasher = BcryptPasswordHasher()

    def post_service(self) -> PostService:
        return PostService(
            repository=self._repository,
            clock=self._clock)

    def user_service(self) -> UserService:
        return UserService(
            repository=self._repository,
            clock=self._clock,
            password_hasher=self._password_hasher)

    def __enter__(self):
        self._repository.create_tables()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._repository.drop_tables()
