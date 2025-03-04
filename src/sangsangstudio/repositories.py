from abc import ABCMeta, abstractmethod
from datetime import datetime
from zoneinfo import ZoneInfo

import mysql.connector

from sangsangstudio.clock import Clock
from sangsangstudio.entities import User, Session


class Repository(metaclass=ABCMeta):
    @abstractmethod
    def save_user(self, user: User):
        pass

    @abstractmethod
    def update_user(self, user: User):
        pass

    @abstractmethod
    def delete_user(self, user_id: int):
        pass

    @abstractmethod
    def find_user_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    def find_user_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    def save_session(self, session: Session):
        pass

    @abstractmethod
    def find_session_by_id(self, session_id: str) -> Session | None:
        pass

    @abstractmethod
    def find_session_by_user_id(self, user_id: int) -> Session | None:
        pass

    @abstractmethod
    def delete_session(self, session_id: str):
        pass


class MySQLConnector:
    def __init__(self, user: str, host: str, port: int, password: str, database: str):
        self.database = database
        self.password = password
        self.port = port
        self.host = host
        self.user = user

    def connect(self):
        return mysql.connector.connect(
            user=self.user,
            database=self.database,
            password=self.password,
            host=self.host,
            port=self.port)


class MySQLRepository(Repository):
    def __init__(self, connector: MySQLConnector, clock: Clock):
        self.clock = clock
        self.connector = connector

    def create_tables(self):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "  id INT(11) NOT NULL AUTO_INCREMENT, "
            "  username VARCHAR(255), "
            "  password_hash BINARY(60), "
            "  PRIMARY KEY (id))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "   session_id VARCHAR(36), "
            "   user_id INT(11), "
            "   created_on TIMESTAMP(6), "
            "   PRIMARY KEY (session_id), "
            "   FOREIGN KEY (user_id) REFERENCES users(id))")

    def drop_tables(self):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS sessions")
        cursor.execute("DROP TABLE IF EXISTS users")


    def save_user(self, user: User):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s)",
            (user.id, user.username, user.password_hash))
        user.id = cursor.lastrowid
        cnx.commit()

    def update_user(self, user: User):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE users SET username = %s WHERE id = %s",
            (user.username, user.id))
        cnx.commit()

    def delete_user(self, user_id: int):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id, ))
        cnx.commit()

    def find_user_by_id(self, user_id: int) -> User | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return self.row_to_user(row) if row else None

    def find_user_by_username(self, username: str) -> User | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        return self.row_to_user(row) if row else None

    def save_session(self, session: Session):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id, created_on) VALUES (%s, %s, %s)",
            (session.id, session.user.id, session.created_on.strftime("%Y-%m-%d %H:%M:%S.%f")))
        cnx.commit()

    def find_session_by_id(self, session_id: str) -> Session | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT "
            f"{self.session_fields()} "
            "FROM sessions "
            "INNER JOIN users ON sessions.user_id = users.id "
            "WHERE sessions.session_id = %s", (session_id, ))
        row = cursor.fetchone()
        return self.row_to_session(row) if row else None

    @staticmethod
    def session_fields() -> str:
        return "sessions.session_id, sessions.created_on, users.id, users.username, users.password_hash"

    def find_session_by_user_id(self, user_id: int) -> Session | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT "
            f"{self.session_fields()} "
            "FROM sessions "
            "INNER JOIN users ON sessions.user_id = users.id "
            "WHERE sessions.user_id = %s", (user_id, ))
        row = cursor.fetchone()
        return self.row_to_session(row) if row else None

    def delete_session(self, session_id: str):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        cnx.commit()

    @staticmethod
    def row_to_user(row: tuple) -> User:
        user_id, username, password_hash = row
        return User(
            id=user_id,
            username=username,
            password_hash=password_hash)

    def row_to_session(self, row: tuple) -> Session:
        session_id, created_on, *rest = row
        return Session(
            id=session_id,
            created_on=self.clock.add_timezone(created_on),
            user=self.row_to_user(rest))

