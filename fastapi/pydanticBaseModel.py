import json
from typing import Set, Union, List

from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException

from fastapi import Body, status
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse


app = FastAPI()
items = {"foo": {"name": "Fighters", "size": 6}, "bar": {"name": "Tenders", "size": 3}}
some_file_path = "large-video-file.mp4"


class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None
    tags: Set[str] = set()


class ItemOther(BaseModel):
    name: str
    tags: List[str]


class ValidationError(Exception):
    ...


async def create_item(request: Request, response: Response):

    raw_request = await request.body()
    request_data = magic_data_reader(raw_request)
    raw_response = await response.body()
    response_data = magic_data_reader(raw_response)

    return request_data, response_data


async def create_other_item(request: Request):
    raw_body = await request.body()
    try:
        data = json.dumps(raw_body)
    except HTTPException:
        raise HTTPException(status_code=422, detail="HTTPException")
    try:
        item = Item.parse_obj(data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail="ValidationError")
    return item


def magic_data_reader(raw_body: bytes):
    return {
        "size": len(raw_body),
        "content": {
            "name": "Maaaagic",
            "price": 42,
            "description": "Just kiddin', no magic here. ✨",
        },
    }


@app.get("/root")
async def main():
    return FileResponse(some_file_path)


@app.get("/typer")
async def redirect_typer():
    return RedirectResponse("https://typer.tiangolo.com")


@app.get("/items/", response_class=HTMLResponse)
async def read_items():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """


@app.put("/items/{id}")
def update_item(_id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    print(_id)
    return JSONResponse(content=json_compatible_item_data)


@app.put("/items/{item_id}")
async def upsert_item(item_id: str, name: Union[str, None] = Body(default=None),
                      size: Union[int, None] = Body(default=None)):
    if item_id in items:
        item = items[item_id]
        item["name"] = name
        item["size"] = size
        return item
    else:
        item = {"name": name, "size": size}
        items[item_id] = item
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=item)


@app.post("/items/", response_model=Item, summary="Create an item")
async def create_item(item: Item):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    \f
    :param item: User input.
    """
    return item


@app.get("/items/", openapi_extra={"x-aperture-labs-portal": "blue"})
async def read_items():
    return [{"item_id": "portal-gun"}]


@app.post(
    "/items/",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "required": ["name", "price"],
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                            "description": {"type": "string"},
                        },
                    }
                }
            },
            "required": True,
        },
    },
)
def new_function():
    ...


@app.post("/items/new/",
          openapi_extra={"requestBody": {"content": {"application/x-yaml": {"schema": Item.schema()}},"required": True, }, }, )
def new_function():
    ...


