from abc import ABCMeta, abstractmethod

import mysql.connector

from sangsangstudio.entities import User


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
    def find_user(self, user_id: int) -> User | None:
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
    def __init__(self, connector: MySQLConnector):
        self.connector = connector

    def create_tables(self):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "  id int(11) NOT NULL AUTO_INCREMENT,"
            "  username varchar(255),"
            "  PRIMARY KEY (id))")

    def drop_tables(self):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")

    def save_user(self, user: User):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "INSERT INTO users (id, username) VALUES (%s, %s)",
            (user.id, user.username))
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

    def find_user(self, user_id: int) -> User | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return self.row_to_user(row) if row else None

    @staticmethod
    def row_to_user(row: tuple) -> User:
        user_id, username = row
        return User(id=user_id, username=username)
