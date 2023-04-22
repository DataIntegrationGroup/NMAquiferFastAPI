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
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import LimitOffsetPage, Page
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK

import models
import schemas
from crud import public_release_filter
from dependencies import get_db

router = APIRouter()


@router.get("/locations", response_model=Page[schemas.Location])
@router.get("/locations/limit-offset", response_model=LimitOffsetPage[schemas.Location])
def read_locations(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Location)
    if pointid:
        q = q.filter(models.Location.PointID.like(f"%{pointid}%"))

    q = q.order_by(models.Location.LocationId)
    q = public_release_filter(q)
    return paginate(q)


@router.get("/location/{location_id}", response_model=schemas.Location)
def read_location(location_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(models.Location)
        .filter(models.Location.LocationId == location_id)
        .first()
    )


@router.get("/location/pointid/{pointid}", response_model=schemas.Location)
def read_location_pointid(pointid: str, db: Session = Depends(get_db)):
    q = db.query(models.Location)
    q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    loc = q.first()
    if loc is None:
        loc = Response(status_code=HTTP_200_OK)

    return loc


# ============= EOF =============================================
