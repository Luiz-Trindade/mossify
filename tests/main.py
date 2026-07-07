from mossify import Mossify

app = Mossify(cache_ttl=60)


@app.register_route("/hello")
async def hello(name: str = "World"):
    return {"message": f"Hello {name}!"}


@app.register_route("/hello", methods=["POST"])
async def update_hello(data: dict):
    return {"status": "updated"}


if __name__ == "__main__":
    app.run()
