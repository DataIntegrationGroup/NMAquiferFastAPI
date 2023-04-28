# ===============================================================================
# Copyright 2023 ross
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
from uuid import UUID

import plotly
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import LimitOffsetPage, Page
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, HTMLResponse
from starlette.status import HTTP_200_OK
from starlette.templating import Jinja2Templates

import models
import schemas
from crud import (
    public_release_filter,
    _read_pods,
    read_waterlevels_manual_query,
    read_waterlevels_pressure_query,
)
from dependencies import get_db
import plotly.graph_objects as go

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/geojson", response_model=list[schemas.LocationGeoJSON])
def read_locations_geojson(db: Session = Depends(get_db)):
    q = db.query(models.Location)
    q = public_release_filter(q)
    locations = q.all()

    def togeojson(l):
        return {
            "type": "Feature",
            "properties": {"name": l.PointID},
            "geometry": l.geometry,
        }

    # content = {
    #     "type": "FeatureCollection",
    #     "features": [togeojson(l) for l in locations],
    # }

    # content = jsonable_encoder(content)
    # return JSONResponse(content=content)
    return [togeojson(l) for l in locations]


@router.get("", response_model=Page[schemas.Location])
@router.get("/limit-offset", response_model=LimitOffsetPage[schemas.Location])
def read_locations(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Location)
    if pointid:
        q = q.filter(models.Location.PointID.like(f"%{pointid}%"))

    q = q.order_by(models.Location.LocationId)
    q = public_release_filter(q)
    return paginate(q)


@router.get("/{location_id}", response_model=schemas.Location)
def read_location(location_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(models.Location)
        .filter(models.Location.LocationId == location_id)
        .first()
    )


@router.get("/pointid/{pointid}", response_model=schemas.Location)
def read_location_pointid(pointid: str, db: Session = Depends(get_db)):
    q = db.query(models.Location)
    q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    loc = q.first()
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)

    return loc


@router.get("/pointid/{pointid}/jsonld", response_model=schemas.LocationJSONLD)
def read_location_pointid_jsonld(
    request: Request, pointid: str, db: Session = Depends(get_db)
):
    loc = get_location(pointid, db)
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)

    loc.request_url = request.url
    loc.request_base_url = request.base_url

    return loc


@router.get("/pointid/{pointid}/geojson", response_model=schemas.LocationGeoJSON)
def read_location_pointid_jsonld(pointid: str, db: Session = Depends(get_db)):
    loc = get_location(pointid, db)
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)

    return loc


# Views ==========================================================
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))
# templates = Jinja2Templates(directory="templates")


@router.get("/view/{pointid}", response_class=HTMLResponse)
def location_view(request: Request, pointid: str, db: Session = Depends(get_db)):
    q = db.query(models.Location)
    q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    loc = q.first()
    loc = schemas.Location.from_orm(loc)

    wells = _read_pods(pointid, db)

    well = None
    pods = []
    if wells:
        well = wells[0]
        pods = well.pods

    fig = go.Figure()
    manual_waterlevels = read_waterlevels_manual_query(pointid, db).all()
    mxs = [w.DateMeasured for w in manual_waterlevels]
    mys = [w.DepthToWaterBGS for w in manual_waterlevels]

    fig.add_trace(go.Scatter(x=mxs, y=mys, mode="markers", name="Manual Water Levels"))

    pressure_waterlevels = read_waterlevels_pressure_query(
        pointid, db, as_dict=True
    ).all()
    pxs = [w.DateMeasured for w in pressure_waterlevels]
    pys = [w.DepthToWaterBGS for w in pressure_waterlevels]
    fig.add_trace(
        go.Scatter(x=pxs, y=pys, mode="lines", name="Continuous Water Levels")
    )

    fig.update_layout(
        xaxis={"title": "Date Measured"},
        yaxis={"title": "Depth to Water BGS (ft)", "autorange": "reversed"},
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return templates.TemplateResponse(
        "location_view.html",
        {
            "request": request,
            "location": loc.dict() if loc else {},
            "well": well,
            "pods": pods,
            "graphJSON": graphJSON,
        },
    )


# End Views ======================================================


def get_location(pointid, db):
    q = db.query(models.Location)
    q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    return q.first()


# ============= EOF =============================================
