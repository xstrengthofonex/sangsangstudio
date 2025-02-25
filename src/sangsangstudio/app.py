import sys

from falcon import App
from waitress import serve


def create_app():
    return App()


def run_server(app, host: str = "localhost", port: int = 8080):
    print(f"Serving at http://{host}:{port}", flush=True)
    serve(app=app, host=host, port=port)


def main(args: list[str]):
    app = create_app()
    run_server(app)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
