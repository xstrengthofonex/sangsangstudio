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

# ["post_id", "author_id", "created_on", "status", "title"]

class MySQLRepository(Repository):
    USERS_COLUMNS = "id, username, password_hash"
    SESSION_COLUMNS = "id, session_key, user_id, created_on"
    POST_COLUMNS = "id, author_id, created_on, status, title"
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

    def create_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(self.create_users_table_statement())
            cursor.execute(self.create_sessions_table_statement())
            cursor.execute(self.create_posts_table_statement())

    def drop_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
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
        return (f"INSERT INTO users ({self.excluding(self.USERS_COLUMNS, 'id')}) "
                f"VALUES (%s, %s);")

    def save_user(self, user: User):
        self.save(user, self.insert_user_statement(), (
            user.username, user.password_hash))

    def find_one(self, statement: str, params: tuple) -> tuple | None:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(statement, params)
            return cursor.fetchone()

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
        return (f"INSERT INTO sessions ({self.excluding(self.SESSION_COLUMNS, 'id')}) "
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
        return (f"INSERT INTO posts ({self.excluding(self.POST_COLUMNS, 'id')}) "
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
        row = self.find_one(self.select_post_by_id_statement(), (post_id,))
        return self.row_to_post(row) if row else None

    def update_post(self, post: Post):
        pass



# class MySQLRepository(Repository):
#     USER_FIELDS = ["id", "username", "password_hash"]
#     POST_FIELDS = ["post_id", "author_id", "created_on", "status", "title"]
#     SESSION_FIELDS = ["session_id", "created_on", "user_id"]
#     CONTENT_FIELDS = ["content_id", "post_id", "type", "order_no", "text", "src"]
# 
#     def __init__(self, connector: MySQLConnector, clock: Clock):
#         self.clock = clock
#         self.connector = connector
# 
#     def create_tables(self):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             "CREATE TABLE IF NOT EXISTS users ("
#             "  id INT(11) NOT NULL AUTO_INCREMENT, "
#             "  username VARCHAR(255), "
#             "  password_hash BINARY(60), "
#             "  PRIMARY KEY (id))")
#         cursor.execute(
#             "CREATE TABLE IF NOT EXISTS sessions ("
#             "   session_id VARCHAR(36), "
#             "   user_id INT(11), "
#             "   created_on TIMESTAMP(6), "
#             "   PRIMARY KEY (session_id), "
#             "   FOREIGN KEY (user_id) REFERENCES users(id))")
#         cursor.execute(
#             "CREATE TABLE IF NOT EXISTS posts ("
#             "   post_id INT(11) NOT NULL AUTO_INCREMENT, "
#             "   author_id INT(11), "
#             "   created_on TIMESTAMP(6), "
#             "   status INT(4), "
#             "   title VARCHAR(255), "
#             "   PRIMARY KEY (post_id), "
#             "   FOREIGN KEY (author_id) REFERENCES users(id))")
#         cursor.execute(
#             "CREATE TABLE IF NOT EXISTS contents ("
#             "  content_id INT(11) NOT NULL AUTO_INCREMENT, "
#             "  post_id INT(11), "
#             "  type INT(6), "
#             "  order_no INT(6), "
#             "  text VARCHAR(255), "
#             "  src VARCHAR(255), "
#             "  PRIMARY KEY (content_id), "
#             "  FOREIGN KEY (post_id) REFERENCES posts(post_id))")
#         cnx.close()
# 
#     def drop_tables(self):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute("DROP TABLE IF EXISTS contents")
#         cursor.execute("DROP TABLE IF EXISTS posts")
#         cursor.execute("DROP TABLE IF EXISTS sessions")
#         cursor.execute("DROP TABLE IF EXISTS users")
#         cnx.close()
# 
#     def save_user(self, user: User):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             f"INSERT INTO users ({self.user_fields_str(excluding=['id'])}) VALUES (%s, %s)",
#             (user.username, user.password_hash))
#         user.id = cursor.lastrowid
#         cnx.commit()
#         cnx.close()
# 
#     def update_user(self, user: User):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             "UPDATE users SET username = %s WHERE id = %s",
#             (user.username, user.id))
#         cnx.commit()
#         cnx.close()
# 
#     def delete_user(self, user_id: int):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             "DELETE FROM users WHERE id = %s", (user_id, ))
#         cnx.commit()
#         cnx.close()
# 
#     def find_user_by_id(self, user_id: int) -> User | None:
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             f"SELECT {self.user_fields_str()} "
#             f"FROM users WHERE id = %s", (user_id,))
#         row = cursor.fetchone()
#         cnx.close()
#         return self.row_to_user(row) if row else None
# 
#     def find_user_by_username(self, username: str) -> User | None:
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             f"SELECT {self.user_fields_str()} "
#             f"FROM users WHERE username = %s", (username,))
#         row = cursor.fetchone()
#         cnx.close()
#         return self.row_to_user(row) if row else None
# 
#     def save_session(self, session: Session):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             f"INSERT INTO sessions ({self.session_fields_str()}) VALUES (%s, %s, %s)",
#             (session.id, session.created_on.strftime("%Y-%m-%d %H:%M:%S.%f"), session.user.id))
#         cnx.commit()
#         cnx.close()
# 
#     def find_session_by_id(self, session_id: str) -> Session | None:
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             "SELECT "
#             f"{self.session_fields_str(excluding=['user_id'])}, "
#             f"{self.user_fields_str()} "
#             "FROM sessions "
#             "INNER JOIN users ON sessions.user_id = users.id "
#             "WHERE sessions.session_id = %s", (session_id, ))
#         row = cursor.fetchone()
#         cnx.close()
#         return self.row_to_session(row) if row else None
# 
#     def find_session_by_user_id(self, user_id: int) -> Session | None:
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             "SELECT "
#             f"{self.session_fields_str(excluding=['user_id'])}, "
#             f"{self.user_fields_str()} "
#             "FROM sessions "
#             "INNER JOIN users ON sessions.user_id = users.id "
#             "WHERE sessions.user_id = %s", (user_id, ))
#         row = cursor.fetchone()
#         cursor.close()
#         cnx.close()
#         return self.row_to_session(row) if row else None
# 
#     def delete_session(self, session_id: str):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
#         cnx.commit()
#         cnx.close()
# 
#     def save_post(self, post: Post):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             f"INSERT INTO posts ({self.post_fields_str()}) VALUES (%s, %s, %s, %s, %s)",
#             (post.id, post.author.id, post.created_on.strftime("%Y-%m-%d %H:%M:%S.%f"),
#              post.status.value, post.title))
#         post.id = cursor.lastrowid
#         cnx.commit()
#         cnx.close()
# 
#     def find_post_by_id(self, post_id: int) -> Post | None:
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         cursor.execute(
#             f"SELECT {self.post_fields_str(excluding=['author_id'])}, "
#             f"{self.user_fields_str()} FROM posts "
#             "INNER JOIN users ON posts.author_id = users.id "
#             "WHERE posts.post_id = %s", (post_id, ))
#         row = cursor.fetchone()
#         if not row:
#             return None
#         contents = self.find_contents_for_post(post_id, cursor)
#         cnx.close()
#         return self.row_to_post(row, contents)
# 
#     def find_contents_for_post(self, post_id: int, cursor: MySQLCursorAbstract) -> list[Content]:
#         cursor.execute(
#             f"SELECT {self.content_field_str(excluding=['post_id'])} "
#             f"FROM contents WHERE post_id = %s", (post_id,))
#         rows = cursor.fetchall()
#         return [self.row_to_content(r) for r in rows]
# 
#     @staticmethod
#     def remove_contents(post: Post, cursor: MySQLCursorAbstract):
#         cursor.execute(
#             "DELETE FROM contents WHERE post_id = %s",
#             (post.id,))
# 
#     def add_contents(self, post: Post, cursor: MySQLCursorAbstract):
#         for content in post.contents:
#             cursor.execute(
#                 f"INSERT INTO contents "
#                 f"({self.content_field_str(excluding=['content_id'])}) "
#                 f"VALUES (%s, %s, %s, %s, %s)",
#                 (post.id, content.type.value, content.order, content.text, content.src))
#             content.id = cursor.lastrowid
# 
#     def update_post(self, post: Post):
#         cnx = self.connector.connect()
#         cursor = cnx.cursor()
#         if post.contents:
#             self.remove_contents(post, cursor)
#             self.add_contents(post, cursor)
#         cnx.commit()
#         cnx.close()
# 
#     @staticmethod
#     def attach_prefix_to_fields(fields: list[str], prefix: str = "") -> list[str]:
#         return [f"{prefix}.{f}" if prefix else f for f in fields]
# 
#     @staticmethod
#     def remove_exclusions(fields: list[str], excluding: list[str] | None = None) -> list[str]:
#         if not excluding:
#             return fields
#         return [f for f in fields if f not in excluding]
# 
#     def user_fields_str(self, excluding: list[str] = None) -> str:
#         return self.create_field_str(excluding, self.USER_FIELDS, "users")
# 
#     def session_fields_str(self, excluding: list[str] = None) -> str:
#         return self.create_field_str(excluding, self.SESSION_FIELDS, "sessions")
# 
#     def post_fields_str(self, excluding: list[str] = None) -> str:
#         return self.create_field_str(excluding, self.POST_FIELDS, "posts")
# 
#     def content_field_str(self, excluding: list[str] = None) -> str:
#         return self.create_field_str(excluding, self.CONTENT_FIELDS, "contents")
# 
#     def create_field_str(self, excluding: list[str], fields: list[str], prefix: str) -> str:
#         return ", ".join(self.attach_prefix_to_fields(
#             self.remove_exclusions(fields, excluding), prefix))
# 
#     @staticmethod
#     def row_to_user(row: tuple) -> User:
#         user_id, username, password_hash = row
#         return User(
#             id=user_id,
#             username=username,
#             password_hash=password_hash)
# 
#     def row_to_session(self, row: tuple) -> Session:
#         session_id, created_on, *rest = row
#         return Session(
#             id=session_id,
#             created_on=self.clock.add_timezone(created_on),
#             user=self.row_to_user(rest))
# 
#     def row_to_post(self, row: tuple, contents: list[Content]) -> Post:
#         post_id, created_on, status, title, *rest = row
#         return Post(
#             id=post_id,
#             created_on=self.clock.add_timezone(created_on),
#             status=PostStatus(status),
#             title=title,
#             contents=contents,
#             author=self.row_to_user(rest))
# 
#     @staticmethod
#     def row_to_content(row: tuple) -> Content:
#         content_id, content_type, order, text, src = row
#         return Content(
#             id=content_id,
#             type=ContentType(content_type),
#             order=order,
#             text=text,
#             src=src)
