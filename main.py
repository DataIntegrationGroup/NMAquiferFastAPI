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

from uuid import UUID
from fastapi import Depends
from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session

import models
import schemas
from app import app
from database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def public_release_filter(q):
    return q.filter(models.Location.PublicRelease == True)


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
        # q = q.filter(models.Well.location.PointID == pointid)
    q = q.order_by(models.Well.WellID)
    q = public_release_filter(q)
    return q.first()



add_pagination(app)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)

# ============= EOF =============================================
