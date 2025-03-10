import sys
from abc import ABC, abstractmethod

from falcon import App, Request, Response, HTTP_OK, HTTPFound
from jinja2 import Environment, FileSystemLoader
from waitress import serve

from sangsangstudio.factories import DevelopmentAppFactory, AppFactory
from sangsangstudio.services import PostService, UserService, LoginRequest, SessionDto
from src.sangsangstudio.settings import TEMPLATES_DIR, STATIC_DIR


class TemplateView(ABC):
    @abstractmethod
    def render(self, name: str, *args, **kwargs) -> str:
        pass


class Jinja2TemplateView(TemplateView):
    def __init__(self, path: str):
        self.env = Environment(loader=FileSystemLoader(path))

    def render(self, name: str, *args, **kwargs) -> str:
        t = self.env.get_template(name)
        return t.render(*args, **kwargs)


class HomeResource:
    def __init__(self, view: TemplateView):
        self.view = view

    def on_get(self, req: Request, res: Response):
        session: SessionDto | None = req.env.get("session", None)
        res.status = HTTP_OK
        res.content_type = "text/html"
        res.text = self.view.render("home.html", user=session.user)


class BlogResource:
    def __init__(self, view: TemplateView, post_service: PostService):
        self.view = view
        self.post_service = post_service

    def on_get(self, req: Request, res: Response):
        posts = self.post_service.find_all_posts()
        session: SessionDto | None = req.env.get("session", None)
        res.content_type = "text/html"
        res.status = HTTP_OK
        res.text = self.view.render("blog.html", posts=posts, user=session.user)

    def on_get_posts_new(self, req: Request, res: Response):
        session: SessionDto | None = req.env.get("session", None)
        res.content_type = "text/html"
        res.status = HTTP_OK
        res.text = self.view.render("blog_posts_new.html", user=session.user)


class UsersResource:
    def __init__(self, view: TemplateView, user_service: UserService):
        self.user_service = user_service
        self.view = view


class AuthenticationMiddleware:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def process_request(self, req: Request, res: Response):
        # Only for development
        session = self.user_service.login(
            LoginRequest(username="vince", password="p1a2s3s4"))
        res.set_cookie("session", session.key)
        req.env["session"] = session


def create_app(factory: AppFactory):
    app = App(middleware=[AuthenticationMiddleware(factory.user_service())])
    view = Jinja2TemplateView(TEMPLATES_DIR)
    home_resource = HomeResource(view)
    blog_resource = BlogResource(view, factory.post_service())
    users_resource = UsersResource(view, factory.user_service())
    app.add_route("/", home_resource)
    app.add_route("/blog", blog_resource)
    app.add_route("/blog/posts/new", blog_resource, suffix="posts_new")
    app.add_static_route("/static", STATIC_DIR)
    return app


def run_server(app, host: str = "localhost", port: int = 8080):
    print(f"Serving at http://{host}:{port}", flush=True)
    serve(app=app, host=host, port=port)


def main(args: list[str]):
    with DevelopmentAppFactory() as factory:
        app = create_app(factory)
        run_server(app)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
