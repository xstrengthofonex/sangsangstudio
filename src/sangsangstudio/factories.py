import os
from abc import ABC, abstractmethod

from sangsangstudio.clock import SystemClock
from sangsangstudio.repositories import MySQLConnector, MySQLRepository
from sangsangstudio.services import AuthorService, UserService, BcryptPasswordHasher, CreateUserRequest


class AppFactory(ABC):
    @abstractmethod
    def author_service(self) -> AuthorService:
        pass

    @abstractmethod
    def user_service(self) -> UserService:
        pass


class DevelopmentAppFactory(AppFactory):
    def __init__(self):
        self.mysql_connector = MySQLConnector(
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=os.getenv("MYSQL_HOST"),
            database=os.getenv("MYSQL_DATABASE"),
            port=os.getenv("MYSQL_PORT", 3306))
        self._clock = SystemClock()
        self._repository = MySQLRepository(self.mysql_connector, self._clock)
        self._password_hasher = BcryptPasswordHasher()
        self._user_service = UserService(
            repository=self._repository,
            clock=self._clock,
            password_hasher=self._password_hasher)
        self._author_service = AuthorService(
            repository=self._repository,
            clock=self._clock)

    def author_service(self) -> AuthorService:
        return self._author_service

    def user_service(self) -> UserService:
        return self._user_service

    def _load_sample_data(self):
        self._user_service.create_user(CreateUserRequest(username="vince", password="p1a2s3s4"))

    def __enter__(self):
        self._repository.drop_tables()
        self._repository.create_tables()
        self._load_sample_data()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

