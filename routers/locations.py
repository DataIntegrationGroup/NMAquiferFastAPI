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
import io
import json
from uuid import UUID

import plotly
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import LimitOffsetPage, Page
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, HTMLResponse, StreamingResponse
from starlette.status import HTTP_200_OK
from starlette.templating import Jinja2Templates

import models
import schemas
from crud import (
    public_release_filter,
    read_waterlevels_manual_query,
    read_waterlevels_pressure_query,
    read_well,
    read_ose_pod, read_waterlevels_acoustic_query,
)
from dependencies import get_db
import plotly.graph_objects as go

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/geojson", response_model=schemas.LocationFeatureCollection)
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

    content = {
        "features": [togeojson(l) for l in locations],
    }
    return content


@router.get("", response_model=Page[schemas.Location])
@router.get(
    "/limit-offset",
    response_model=LimitOffsetPage[schemas.Location],
    include_in_schema=False,
)
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


def safe_json(d):
    for k, v in d.items():
        if isinstance(v, UUID):
            d[k] = str(v)
        if isinstance(v, dict):
            safe_json(v)


@router.get("/pointid/{pointid}/download")
def read_location_pointid(pointid: str, db: Session = Depends(get_db)):
    loc = get_location(pointid, db)
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)
        return loc
    else:
        well = read_well(pointid, db)
        pod, pod_url = read_ose_pod(well.OSEWellID)

        stream = io.StringIO()
        loc = schemas.Location.from_orm(loc)
        well = schemas.Well.from_orm(well)

        payload = {
            "location": loc.dict(),
            "well": well.dict(),
            "pod": {
                "properties": pod["features"][0]["attributes"],
                "source_url": pod_url,
            },
        }

        safe_json(payload)
        json.dump(payload, stream, indent=2)

        response = StreamingResponse(
            iter([stream.getvalue()]), media_type="application/json"
        )
        response.headers["Content-Disposition"] = f"attachment; filename={pointid}.json"
        return response


@router.get("/pointid/{pointid}", response_model=schemas.Location)
def read_location_pointid(pointid: str, db: Session = Depends(get_db)):
    # q = db.query(models.Location)
    # q = q.filter(models.Location.PointID == pointid)
    # q = public_release_filter(q)
    # loc = q.first()
    loc = get_location(pointid, db)
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
def read_location_pointid_geojson(pointid: str, db: Session = Depends(get_db)):
    loc = get_location(pointid, db)
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)

    return loc


# Views ==========================================================
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


# templates = Jinja2Templates(directory="templates")


@router.get("/view/{pointid}", response_class=HTMLResponse)
def location_view(request: Request, pointid: str, db: Session = Depends(get_db)):
    # q = db.query(models.Location)
    # q = q.filter(models.Location.PointID == pointid)
    # q = public_release_filter(q)
    # loc = q.first()
    loc = get_location(pointid, db)

    if loc is not None:
        loc = schemas.Location.from_orm(loc)
    else:
        loc = schemas.Location(
            PointID=pointid,
            LocationId=UUID("00000000-0000-0000-0000-000000000000"),
            PublicRelease=True,
        )

    well = read_well(pointid, db)
    # wells = _read_pods(pointid, db)
    #
    # # well = None
    # # pods = []
    # pod_url = ''
    # if wells:
    #     well = wells[0]
    #     pod_url = well.pod_url

    fig = go.Figure()
    manual_waterlevels = read_waterlevels_manual_query(pointid, db).all()
    mxs = [w.DateMeasured for w in manual_waterlevels]
    mys = [w.DepthToWaterBGS for w in manual_waterlevels]

    fig.add_trace(go.Scatter(x=mxs, y=mys, mode="markers", name="Manual WL"))

    continuous_waterlevels = read_waterlevels_pressure_query(
        pointid, db, as_dict=True
    ).all()
    if not continuous_waterlevels:
        continuous_waterlevels = read_waterlevels_acoustic_query(pointid, db, as_dict=True
                                                                 ).all()

    pxs = [w.DateMeasured for w in continuous_waterlevels]
    pys = [w.DepthToWaterBGS for w in continuous_waterlevels]
    fig.add_trace(go.Scatter(x=pxs, y=pys, mode="lines", name="Continuous WL"))

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
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
            "pod_url": well.pod_url,
            # "pods": pods,
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
