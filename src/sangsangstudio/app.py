import sys
from abc import ABC, abstractmethod

from falcon import App, Request, Response, HTTP_OK
from jinja2 import Environment, FileSystemLoader
from waitress import serve

from sangsangstudio.factories import DevelopmentAppFactory
from sangsangstudio.services import PostService
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
        res.status = HTTP_OK
        res.content_type = "text/html"
        res.text = self.view.render("home.html")


class BlogResource:
    def __init__(self, view: TemplateView, post_service: PostService):
        self.view = view
        self.post_service = post_service

    def on_get(self, req: Request, res: Response):
        pass


def create_app():
    with DevelopmentAppFactory() as factory:
        app = App()
        view = Jinja2TemplateView(TEMPLATES_DIR)
        home_resource = HomeResource(view)
        blog_resource = BlogResource(view, factory.post_service())
        app.add_route("/", home_resource)
        app.add_route("/blog", blog_resource)
        app.add_static_route("/static", STATIC_DIR)
        return app


def run_server(app, host: str = "localhost", port: int = 8080):
    print(f"Serving at http://{host}:{port}", flush=True)
    serve(app=app, host=host, port=port)


def main(args: list[str]):
    app = create_app()
    run_server(app)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
