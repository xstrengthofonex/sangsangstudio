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
    ContentType, Entity)


class Repository(metaclass=ABCMeta):
    @abstractmethod
    def save_user(self, user: User):
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
    def find_session_by_key(self, session_id: str) -> Session | None:
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
    def save_content(self, content: Content):
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
    USERS_COLUMNS = "id, username, password_hash"
    SESSION_COLUMNS = "id, session_key, user_id, created_on"
    POST_COLUMNS = "id, author_id, created_on, status, title"
    CONTENT_COLUMNS = "id, post_id, type, sequence, text, src"
    TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, connector: MySQLConnector, clock: Clock):
        self.clock = clock
        self.connector = connector

    def connect(self):
        return self.connector.connect()

    @staticmethod
    def create_users_table_statement() -> str:
        return ("CREATE TABLE IF NOT EXISTS users ("
                "id INT(11) NOT NULL AUTO_INCREMENT, "
                "username VARCHAR(50), "
                "password_hash BINARY(60), "
                "PRIMARY KEY (id));")

    @staticmethod
    def drop_users_table_statement() -> str:
        return "DROP TABLE IF EXISTS users;"

    @staticmethod
    def create_sessions_table_statement() -> str:
        return ("CREATE TABLE IF NOT EXISTS sessions ("
                "id INT(11) NOT NULL AUTO_INCREMENT, "
                "session_key VARCHAR(36), "
                "user_id INT(11), "
                "created_on TIMESTAMP(6),"
                "PRIMARY KEY (id),"
                "FOREIGN KEY (user_id) REFERENCES users(id));")

    @staticmethod
    def drop_sessions_table_statement() -> str:
        return "DROP TABLE IF EXISTS sessions;"

    @staticmethod
    def create_posts_table_statement() -> str:
        return ("CREATE TABLE IF NOT EXISTS posts ("
                "id INT(11) NOT NULL AUTO_INCREMENT, "
                "author_id INT(11), "
                "created_on TIMESTAMP(6), "
                "status INT(4),"
                "title VARCHAR(255), "
                "PRIMARY KEY (id), "
                "FOREIGN KEY (author_id) REFERENCES users(id));")

    @staticmethod
    def drop_posts_table_statement() -> str:
        return "DROP TABLE IF EXISTS posts;"

    @staticmethod
    def create_contents_table_statement() -> str:
        return ("CREATE TABLE IF NOT EXISTS contents ("
                "id INT(11) NOT NULL AUTO_INCREMENT, "
                "post_id INT(11), "
                "type INT(4), "
                "sequence INT(6), "
                "text VARCHAR(1000), "
                "src VARCHAR(255), "
                "PRIMARY KEY (id), "
                "FOREIGN KEY (post_id) REFERENCES posts(id))")

    @staticmethod
    def drop_contents_table_statement() -> str:
        return "DROP TABLE IF EXISTS contents"

    def create_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(self.create_users_table_statement())
            cursor.execute(self.create_sessions_table_statement())
            cursor.execute(self.create_posts_table_statement())
            cursor.execute(self.create_contents_table_statement())

    def drop_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(self.drop_contents_table_statement())
            cursor.execute(self.drop_posts_table_statement())
            cursor.execute(self.drop_sessions_table_statement())
            cursor.execute(self.drop_users_table_statement())

    def save(self, entity: Entity, statement: str, params: tuple):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(statement, params)
            entity.id = cursor.lastrowid
            conn.commit()

    @staticmethod
    def excluding(fields: str, value: str) -> str:
        return fields.strip(f"{value}, ")

    def insert_user_statement(self):
        return (f"INSERT INTO users "
                f"({self.excluding(self.USERS_COLUMNS, 'id')}) "
                f"VALUES (%s, %s);")

    def save_user(self, user: User):
        self.save(user, self.insert_user_statement(), (
            user.username, user.password_hash))

    @staticmethod
    def _find_one(statement: str, params: tuple, cursor: MySQLCursorAbstract) -> tuple | None:
        cursor.execute(statement, params)
        return cursor.fetchone()

    def find_one(self, statement: str, params: tuple, cursor: MySQLCursorAbstract | None = None) -> tuple | None:
        if cursor:
            return self._find_one(statement, params, cursor)
        with self.connect() as conn:
            return self._find_one(statement, params, conn.cursor())

    def select_user_by_id_statement(self) -> str:
        return f"SELECT {self.USERS_COLUMNS} FROM users WHERE id = %s;"

    @staticmethod
    def row_to_user(row: tuple) -> User:
        user_id, username, password_hash = row
        return User(id=user_id, username=username, password_hash=password_hash)

    def find_user_by_id(self, user_id: int) -> User | None:
        row = self.find_one(self.select_user_by_id_statement(), (user_id,))
        return self.row_to_user(row) if row else None

    def select_user_by_username_statement(self) -> str:
        return f"SELECT {self.USERS_COLUMNS} FROM users WHERE username = %s;"

    def find_user_by_username(self, username: str) -> User | None:
        row = self.find_one(self.select_user_by_username_statement(), (username,))
        return self.row_to_user(row) if row else None

    def insert_session_statement(self) -> str:
        return (f"INSERT INTO sessions "
                f"({self.excluding(self.SESSION_COLUMNS, 'id')}) "
                f"VALUES (%s, %s, %s)")

    def save_session(self, session: Session):
        self.save(session, self.insert_session_statement(), (
            session.key, session.user.id, session.created_on.strftime(self.TIMESTAMP_FMT)))

    @staticmethod
    def with_prefix(fields: str, prefix: str) -> str:
        return ", ".join([f"{prefix}.{f}" for f in fields.split(", ")])

    def select_session_by_key_statement(self) -> str:
        return (f"SELECT {self.with_prefix(self.SESSION_COLUMNS, 'sessions')}, "
                f"{self.with_prefix(self.USERS_COLUMNS, 'users')} "
                "FROM sessions "
                "INNER JOIN users ON sessions.user_id = users.id "
                "WHERE session_key = %s;")

    def select_session_by_user_id_statement(self) -> str:
        return (f"SELECT {self.with_prefix(self.SESSION_COLUMNS, 'sessions')}, "
                f"{self.with_prefix(self.USERS_COLUMNS, 'users')} "
                "FROM sessions "
                "INNER JOIN users ON sessions.user_id = users.id "
                "WHERE user_id = %s;")

    def row_to_session(self, row: tuple) -> Session:
        session_id, key, _, created_on, *rest = row
        return Session(
            id=session_id,
            key=key,
            user=self.row_to_user(rest),
            created_on=self.clock.add_timezone(created_on))

    def find_session_by_key(self, key: str) -> Session | None:
        row = self.find_one(self.select_session_by_key_statement(), (key,))
        return self.row_to_session(row) if row else None

    def find_session_by_user_id(self, user_id: int) -> Session | None:
        row = self.find_one(self.select_session_by_user_id_statement(), (user_id,))
        return self.row_to_session(row) if row else None

    def delete(self, table: str, column: str, params: tuple):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table} WHERE {column} = %s", params)
            conn.commit()

    def delete_session(self, session_id: str):
        self.delete("sessions", "session_key", (session_id,))

    def insert_post_statement(self) -> str:
        return (f"INSERT INTO posts "
                f"({self.excluding(self.POST_COLUMNS, 'id')}) "
                f"VALUES (%s, %s, %s, %s);")

    def save_post(self, post: Post):
        self.save(post, self.insert_post_statement(), (
            post.author.id, post.created_on.strftime(self.TIMESTAMP_FMT),
            post.status.value, post.title))

    def select_post_by_id_statement(self) -> str:
        return (f"SELECT {self.with_prefix(self.POST_COLUMNS, 'posts')}, "
                f"{self.with_prefix(self.USERS_COLUMNS, 'users')} "
                "FROM posts "
                "INNER JOIN users ON posts.author_id = users.id "
                "WHERE posts.id = %s;")

    def row_to_post(self, row: tuple) -> Post:
        post_id, _, created_on, status, title, *rest = row
        return Post(
            id=post_id,
            author=self.row_to_user(rest),
            created_on=self.clock.add_timezone(created_on),
            status=PostStatus(status),
            title=title)

    def find_post_by_id(self, post_id: int) -> Post | None:
        with self.connect() as conn:
            cursor = conn.cursor()
            row = self.find_one(self.select_post_by_id_statement(), (post_id,), cursor)
            if not row:
                return None
            post = self.row_to_post(row)
            post.contents = self.find_contents_for_post(post_id, cursor)
            return post

    def insert_content_statement(self) -> str:
        return (f"INSERT INTO contents "
                f"({self.excluding(self.CONTENT_COLUMNS, 'id')}) "
                f"VALUES (%s, %s, %s, %s, %s);")

    @staticmethod
    def _find_all(statement: str, params: tuple, cursor: MySQLCursorAbstract) -> list[tuple]:
        cursor.execute(statement, params)
        return cursor.fetchall()

    def find_all(self, statement: str, params: tuple, cursor: MySQLCursorAbstract | None = None) -> list[tuple]:
        if cursor:
            return self._find_all(statement, params, cursor)
        with self.connect() as conn:
            return self._find_all(statement, params, conn.cursor())

    def select_content_by_post_id(self) -> str:
        return f"SELECT {self.CONTENT_COLUMNS} FROM contents WHERE post_id = %s ORDER BY sequence;"

    def find_contents_for_post(self, post_id: int, cursor: MySQLCursorAbstract | None = None) -> list[Content]:
        rows = self.find_all(self.select_content_by_post_id(), (post_id,), cursor)
        return [self.row_to_content(r) for r in rows]

    @staticmethod
    def row_to_content(row: tuple) -> Content:
        content_id, post_id, content_type, sequence, text, src = row
        return Content(
            id=content_id,
            post_id=post_id,
            type=ContentType(content_type),
            sequence=sequence,
            text=text,
            src=src)

    def save_content(self, content: Content):
        self.save(content, self.insert_content_statement(),
                  (content.post_id, content.type.value, content.sequence,
                   content.text, content.src))

