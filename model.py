import orjson
from pydantic import BaseModel


def dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class Model(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = dumps
