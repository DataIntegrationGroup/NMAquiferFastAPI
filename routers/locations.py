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
import os
import sys
from typing import Annotated, List
from uuid import UUID

import plotly
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import LimitOffsetPage, Page
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import (
    Response,
    JSONResponse,
    HTMLResponse,
    StreamingResponse,
    FileResponse,
)
from starlette.status import HTTP_200_OK
from starlette.templating import Jinja2Templates

import models
import schemas
from crud import (
    public_release_filter,
    read_waterlevels_manual_query,
    read_waterlevels_pressure_query,
    read_well,
    read_ose_pod,
    read_waterlevels_acoustic_query,
    locations_feature_collection,
    geometry_filter,
    read_equipment,
    pointid_filter,
)
from dependencies import get_db
import plotly.graph_objects as go
from auth import get_current_user, User, get_current_active_user

router = APIRouter(prefix="/locations", tags=["locations"])


def _get_locations(db, only_public=True):
    q = db.query(models.Location, models.Well)
    q = q.join(models.Well)
    q = geometry_filter(q)
    if only_public:
        q = public_release_filter(q)
    q = q.order_by(models.Location.PointID)
    return q.all()


@router.get("/fc", response_model=schemas.LocationFeatureCollection)
def read_locations_geojson_fc(db: Session = Depends(get_db)):
    locations = _get_locations(db)

    content = locations_feature_collection(locations)
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


#
# @router.get("/pointid/{pointid}/sensitive")
# def read_sensitive(
#         pointid: str,
#         # current_user: Annotated[User, Depends(get_current_active_user)],
#         db: Session = Depends(get_db),
# ):
#     # print('asf', current_user)
#     q = db.query(models.Location, models.Well, models.OwnersData)
#     q = q.join(models.Well)
#     q = q.join(models.OwnerLink)
#     q = q.join(models.OwnersData)
#
#     q = q.filter(models.Location.PointID == pointid)
#
#     loc, well, ownersdata = q.first()
#
#     return {
#         "Name": f"{ownersdata.FirstName} {ownersdata.LastName}",
#         "Email": ownersdata.Email,
#         "Phone": ownersdata.Phone,
#         "Cell": ownersdata.CellPhone,
#     }
#     # return {'name': ownersdata.FirstName, 'last_name': ownersdata.LastName}


@router.get("/photo/{photoid}")
def read_photo(photoid: str):
    if sys.platform == "darwin":
        path = "/Volumes/amp/data/database/photos/Digital photos_wells"
    else:
        path = "/mnt/wellphotos/Digital photos_wells"
    path = f"{path}/{photoid}"
    return FileResponse(path)


@router.get("/pointid/{pointid}/photo")
def read_photo_pointid(pointid: str, db: Session = Depends(get_db)):
    paths = get_photo_path(pointid, db)

    # print(os.listdir('/Volumes/amp/data/database/photos/Digital photos_wells/'))
    # from smb.SMBConnection import SMBConnection

    # There will be some mechanism to capture userID, password, client_machine_name, server_name and server_ip
    # client_machine_name can be an arbitary ASCII string
    # server_name should match the remote machine name, or else the connection will be rejected
    # server_name = os.environ.get('SMB_SERVER_NAME', '')
    # server_host = os.environ.get('SMB_SERVER_HOST', '')
    # user = os.environ.get('SMB_USER', '')
    # password = os.environ.get('SMB_PASSWORD', '')

    # conn = SMBConnection(user, password, 'fastapi', server_name, is_direct_tcp=True)
    # result = conn.connect(server_host, 445, timeout=5)

    # print('rea', result)
    # from smbclient import register_session, listdir
    # register_session(server_host, username=user, password=password)

    # listdir(r'\\agustin\amp')
    # import smbclient
    # smbclient.ClientConfig(username=user, password=password)
    # print(smbclient.listdir('\\agustin\\amp\\data'))

    # print('acasdsadfasdf', result)
    # for s in conn.listShares():
    #     print('share', s.name)
    # print('fasd', conn.listPath('amp', '/data/database/photos/'))
    # for p in paths:
    #     print('asdf', p.OLEPath)
    #     npath = f'/data/database/photos/Digital photos_wells/{p.OLEPath}'
    #     print('npath', npath)
    #     fileobj = io.StringIO()
    #     conn.retrieveFile('amp', f'data/{p.OLEPath}', fileobj, timeout=0.5)
    #     fileobj.seek(0)

    return paths


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


# ====== Detail ==================================================


@router.get("/detail/{pointid}", response_class=HTMLResponse)
def location_detail(request: Request, pointid: str):
    return templates.TemplateResponse(
        "location_detail_view.html",
        {
            "request": request,
            "pointid": pointid,
            # "location": loc.dict() if loc else {},
            # "well": well,
            # "pod_url": well.pod_url,
            # "pods": pods,
            # "graphJSON": graphJSON,
        },
    )


@router.get("/{pointid}/projects", response_model=List[schemas.ProjectLocations])
def location_projects(pointid: str, db: Session = Depends(get_db)):
    q = db.query(models.ProjectLocations)
    q = q.filter(models.ProjectLocations.PointID == pointid)
    return q.all()


@router.get("/{pointid}/owners", response_model=schemas.OwnersData)
def location_detail_owners(pointid: str, db: Session = Depends(get_db)):
    q = db.query(models.Location, models.Well, models.OwnersData)
    q = q.join(models.Well)
    q = q.join(models.OwnerLink)
    q = q.join(models.OwnersData)

    q = q.filter(models.Location.PointID == pointid)
    try:
        loc, well, ownersdata = q.first()
        return ownersdata
    except TypeError:
        pass


@router.get("/{pointid}/location", response_model=schemas.Location)
def read_location_pointid_location(pointid: str, db: Session = Depends(get_db)):
    loc = get_location(pointid, db)
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)

    return loc


@router.get("/{pointid}/well", response_model=schemas.Well)
def read_location_pointid_well(pointid: str, db: Session = Depends(get_db)):
    well = read_well(pointid, db)
    if well is None:
        well = Response(status_code=HTTP_200_OK)

    return well


@router.get("/{pointid}/equipment", response_model=List[schemas.Equipment])
def read_location_pointid_equipment(pointid: str, db: Session = Depends(get_db)):
    equipment = read_equipment(pointid, db)
    if equipment is None:
        equipment = Response(status_code=HTTP_200_OK)
    return equipment


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
        continuous_waterlevels = read_waterlevels_acoustic_query(
            pointid, db, as_dict=True
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


def get_photo_path(pointid, db):
    q = db.query(models.WellPhotos)
    q = q.filter(models.WellPhotos.PointID == pointid)
    return q.all()


def get_location(pointid, db):
    q = db.query(models.Location)
    q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    return q.first()


# ============= EOF =============================================
