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
from pprint import pprint

import requests
from uuid import UUID
from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

import models
import schemas
from app import app
from database import SessionLocal

templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def public_release_filter(q):
    return q.filter(models.Location.PublicRelease == True)


# ===============================================================================
# views

@app.get('/location_view', response_class=HTMLResponse)
def location_view(request: Request, pointid: str = None, db: Session = Depends(get_db)):
    if pointid:
        q = db.query(models.Location.__table__)
        q = q.filter(models.Location.PointID == pointid)
        q = public_release_filter(q)
        loc = q.first()
        wells = _read_pods(pointid, db)
        well = wells[0]
        pods = well.pods

        return templates.TemplateResponse('location_view.html', {'request': request,
                                                                 'location': loc,
                                                                 'well': well,
                                                                 'pods': pods, })


# end views
# ===============================================================================

# ===============================================================================
# routes
@app.get("/locations", response_model=Page[schemas.Location])
@app.get("/locations/limit-offset", response_model=LimitOffsetPage[schemas.Location])
def read_locations(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Location)
    if pointid:
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.Location.LocationId)
    q = public_release_filter(q)
    return paginate(q)


@app.get('/locations/{location_id}', response_model=schemas.Location)
def read_location(location_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.Location).filter(models.Location.LocationId == location_id).first()


@app.get("/well", response_model=schemas.Well)
def read_well(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Well)
    if pointid:
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.Well.WellID)
    q = public_release_filter(q)
    return q.first()


@app.get("/pod", response_model=list[schemas.Well])
def read_pods(pointid: str = None, db: Session = Depends(get_db)):
    return _read_pods(pointid, db)


def _read_pods(pointid, db):
    q = db.query(models.Well)
    if pointid:
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
        q = q.order_by(models.Well.WellID)
        q = public_release_filter(q)

        ps = q.all()

        for pi in ps:
            print(pi)
            ose_id = pi.OSEWellID
            if ose_id:
                url = f'https://services2.arcgis.com/qXZbWTdPDbTjl7Dy/arcgis/rest/services/OSE_PODs/FeatureServer/0/query' \
                      f'?where' \
                      f'=db_file= \'{ose_id}\' &outFields=*&outSR=4326&f=json'

                resp = requests.get(url)
                resp = resp.json()
                # pprint(resp)
                pods = resp.get('features')
                pprint(pods)
                # for pod in pods:
                #     print(pod.keys())

                pi.pods = pods

        return ps


@app.get("/waterlevels", response_model=Page[schemas.WaterLevels])
@app.get("/waterlevels/limit-offset", response_model=LimitOffsetPage[schemas.WaterLevels])
def read_waterlevels(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.WaterLevels)
    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.WaterLevels.OBJECTID)
    q = public_release_filter(q)

    return paginate(q)


@app.get("/waterlevels_pressure", response_model=Page[schemas.WaterLevelsContinuous_Pressure])
@app.get("/waterlevels_pressure/limit-offset", response_model=LimitOffsetPage[schemas.WaterLevelsContinuous_Pressure])
def read_waterlevels(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.WaterLevelsContinuous_Pressure)
    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.WaterLevelsContinuous_Pressure.OBJECTID)
    q = public_release_filter(q)

    return paginate(q)


add_pagination(app)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)

# ============= EOF =============================================
