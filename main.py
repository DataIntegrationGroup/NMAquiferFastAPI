# ===============================================================================
# Copyright 2023 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import json

import redis as redis
from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from fastapi_pagination import add_pagination
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from sqlalchemy.orm import Session

import models
import schemas
from app import app


from dependencies import get_db
from routers import locations, wells, waterlevels, ngwmn, collab_net
from starlette.templating import Jinja2Templates

# ===============================================================================
# views


from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

#
# @app.get("/map/locations")
# def map_locations(db: Session = Depends(get_db)):
#     q = db.query(models.Location)
#     q = public_release_filter(q)
#     locations = q.all()
#
#     def togeojson(l):
#         return {
#             "type": "Feature",
#             "properties": {"name": l.PointID},
#             "geometry": l.geometry,
#         }
#
#     content = {
#         "type": "FeatureCollection",
#         "features": [togeojson(l) for l in locations],
#     }
#
#     content = jsonable_encoder(content)
#     return JSONResponse(content=content)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


@app.get("/mapboxtoken")
def mapboxtoken():
    return {
        "token": "pk.eyJ1IjoiamFrZXJvc3N3ZGkiLCJhIjoiY2s3M3ZneGl4MGhkMDNrcjlocmNuNWg4bCJ9.4r1DRDQ_ja0fV2nnmlVT0A"
    }


@app.get("/map", response_class=HTMLResponse)
def map_view(request: Request, db: Session = Depends(get_db)):

    return templates.TemplateResponse(
        "map_view.html",
        {
            "request": request,
            # "center": {"lat": 34.5, "lon": -106.0},
            # "zoom": 7,
            # "data_url": "/locations/fc",
        },
    )


# end views
# ===============================================================================


# ===============================================================================
# routes
app.include_router(locations.router)
app.include_router(wells.router)
app.include_router(waterlevels.router)
app.include_router(ngwmn.router)
app.include_router(collab_net.router)
add_pagination(app)


@app.on_event("startup")
async def startup_event():
    # db = redis.from_url("redis://localhost:6379")
    # print('ddd', db)
    pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
    db = redis.Redis(connection_pool=pool)
    FastAPICache.init(RedisBackend(db), prefix="fastapi-cache")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

# ============= EOF =============================================
