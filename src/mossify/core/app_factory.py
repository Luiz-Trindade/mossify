from fastapi import FastAPI


def create_fastapi_app(
    title: str = "Mossify API",
    version: str = "0.1.0",
    **fastapi_kwargs,
) -> FastAPI:
    app = FastAPI(title=title, version=version, **fastapi_kwargs)

    @app.get("/")
    async def root():
        return {"message": "🌿 Welcome to Mossify!"}

    return app
