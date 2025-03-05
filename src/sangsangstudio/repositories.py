from abc import ABCMeta, abstractmethod

import mysql.connector
from mysql.connector.abstracts import MySQLCursorAbstract

from sangsangstudio.clock import Clock
from sangsangstudio.entities import (
    User,
    Session,
    Post,
    PostStatus,
    Content,
    ContentType)


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

    @abstractmethod
    def save_post(self, post: Post):
        pass

    @abstractmethod
    def find_post_by_id(self, post_id: int) -> Post | None:
        pass

    @abstractmethod
    def update_post(self, post: Post):
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
    USER_FIELDS = ["id", "username", "password_hash"]
    POST_FIELDS = ["post_id", "author_id", "created_on", "status", "title"]
    SESSION_FIELDS = ["session_id", "created_on", "user_id"]
    CONTENT_FIELDS = ["content_id", "post_id", "type", "text"]

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
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS posts ("
            "   post_id INT(11) NOT NULL AUTO_INCREMENT, "
            "   author_id INT(11), "
            "   created_on TIMESTAMP(6), "
            "   status INT(4), "
            "   title VARCHAR(255), "
            "   PRIMARY KEY (post_id), "
            "   FOREIGN KEY (author_id) REFERENCES users(id))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS contents ("
            "  content_id INT(11) NOT NULL AUTO_INCREMENT, "
            "  post_id INT(11), "
            "  type INT(6), "
            "  text VARCHAR(255), "
            "  PRIMARY KEY (content_id), "
            "  FOREIGN KEY (post_id) REFERENCES posts(post_id))")
        cnx.close()

    def drop_tables(self):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS contents")
        cursor.execute("DROP TABLE IF EXISTS posts")
        cursor.execute("DROP TABLE IF EXISTS sessions")
        cursor.execute("DROP TABLE IF EXISTS users")
        cnx.close()

    def save_user(self, user: User):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            f"INSERT INTO users ({self.user_fields_str(excluding=['id'])}) VALUES (%s, %s)",
            (user.username, user.password_hash))
        user.id = cursor.lastrowid
        cnx.commit()
        cnx.close()

    def update_user(self, user: User):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE users SET username = %s WHERE id = %s",
            (user.username, user.id))
        cnx.commit()
        cnx.close()

    def delete_user(self, user_id: int):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "DELETE FROM users WHERE id = %s", (user_id, ))
        cnx.commit()
        cnx.close()

    def find_user_by_id(self, user_id: int) -> User | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            f"SELECT {self.user_fields_str()} "
            f"FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cnx.close()
        return self.row_to_user(row) if row else None

    def find_user_by_username(self, username: str) -> User | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            f"SELECT {self.user_fields_str()} "
            f"FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cnx.close()
        return self.row_to_user(row) if row else None

    def save_session(self, session: Session):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            f"INSERT INTO sessions ({self.session_fields_str()}) VALUES (%s, %s, %s)",
            (session.id, session.created_on.strftime("%Y-%m-%d %H:%M:%S.%f"), session.user.id))
        cnx.commit()
        cnx.close()

    def find_session_by_id(self, session_id: str) -> Session | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT "
            f"{self.session_fields_str(excluding=['user_id'])}, "
            f"{self.user_fields_str()} "
            "FROM sessions "
            "INNER JOIN users ON sessions.user_id = users.id "
            "WHERE sessions.session_id = %s", (session_id, ))
        row = cursor.fetchone()
        cnx.close()
        return self.row_to_session(row) if row else None

    def find_session_by_user_id(self, user_id: int) -> Session | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT "
            f"{self.session_fields_str(excluding=['user_id'])}, "
            f"{self.user_fields_str()} "
            "FROM sessions "
            "INNER JOIN users ON sessions.user_id = users.id "
            "WHERE sessions.user_id = %s", (user_id, ))
        row = cursor.fetchone()
        cursor.close()
        cnx.close()
        return self.row_to_session(row) if row else None

    def delete_session(self, session_id: str):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        cnx.commit()
        cnx.close()

    def save_post(self, post: Post):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            f"INSERT INTO posts ({self.post_fields_str()}) VALUES (%s, %s, %s, %s, %s)",
            (post.id, post.author.id, post.created_on.strftime("%Y-%m-%d %H:%M:%S.%f"),
             post.status.value, post.title))
        post.id = cursor.lastrowid
        cnx.commit()
        cnx.close()

    def find_post_by_id(self, post_id: int) -> Post | None:
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(
            f"SELECT {self.post_fields_str(excluding=['author_id'])}, "
            f"{self.user_fields_str()} FROM posts "
            "INNER JOIN users ON posts.author_id = users.id "
            "WHERE posts.post_id = %s", (post_id, ))
        row = cursor.fetchone()
        if not row:
            return None
        contents = self.find_contents_for_post(post_id, cursor)
        cursor.close()
        cnx.close()
        return self.row_to_post(row, contents)

    def find_contents_for_post(self, post_id: int, cursor: MySQLCursorAbstract) -> list[Content]:
        cursor.execute(
            f"SELECT {self.content_field_str(excluding=['post_id'])} "
            f"FROM contents WHERE post_id = %s", (post_id,))
        rows = cursor.fetchmany()
        cursor.close()
        return [self.row_to_content(r) for r in rows]

    @staticmethod
    def remove_contents(post: Post, cursor: MySQLCursorAbstract):
        cursor.execute(
            "DELETE FROM contents WHERE post_id = %s",
            (post.id,))

    def add_contents(self, post: Post, cursor: MySQLCursorAbstract):
        for content in post.contents:
            cursor.execute(
                f"INSERT INTO contents "
                f"({self.content_field_str(excluding=['content_id'])}) "
                f"VALUES (%s, %s, %s)",
                (post.id, content.type.value, content.text))
            content.id = cursor.lastrowid

    def update_post(self, post: Post):
        cnx = self.connector.connect()
        cursor = cnx.cursor()
        if post.contents:
            self.remove_contents(post, cursor)
            self.add_contents(post, cursor)
        cnx.commit()
        cnx.close()

    @staticmethod
    def attach_prefix_to_fields(fields: list[str], prefix: str = "") -> list[str]:
        return [f"{prefix}.{f}" if prefix else f for f in fields]

    @staticmethod
    def remove_exclusions(fields: list[str], excluding: list[str] | None = None) -> list[str]:
        if not excluding:
            return fields
        return [f for f in fields if f not in excluding]

    def user_fields_str(self, excluding: list[str] = None) -> str:
        return self.create_field_str(excluding, self.USER_FIELDS, "users")

    def session_fields_str(self, excluding: list[str] = None) -> str:
        return self.create_field_str(excluding, self.SESSION_FIELDS, "sessions")

    def post_fields_str(self, excluding: list[str] = None) -> str:
        return self.create_field_str(excluding, self.POST_FIELDS, "posts")

    def content_field_str(self, excluding: list[str] = None) -> str:
        return self.create_field_str(excluding, self.CONTENT_FIELDS, "contents")

    def create_field_str(self, excluding, fields, prefix):
        return ", ".join(self.attach_prefix_to_fields(
            self.remove_exclusions(fields, excluding), prefix))

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

    def row_to_post(self, row: tuple, contents: list[Content]) -> Post:
        post_id, created_on, status, title, *rest = row
        return Post(
            id=post_id,
            created_on=self.clock.add_timezone(created_on),
            status=PostStatus(status),
            title=title,
            contents=contents,
            author=self.row_to_user(rest))

    @staticmethod
    def row_to_content(row: tuple) -> Content:
        content_id, content_type, text = row
        return Content(id=content_id, type=ContentType(content_type), text=text)



