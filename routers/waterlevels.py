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
from fastapi import Depends, APIRouter
from fastapi_pagination import Page, LimitOffsetPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

import models
import schemas
from app import app
from crud import _read_waterlevels_query, public_release_filter
from dependencies import get_db

router = APIRouter()

# ============= EOF =============================================
@router.get("/waterlevels", response_model=Page[schemas.WaterLevels])
@router.get(
    "/waterlevels/limit-offset", response_model=LimitOffsetPage[schemas.WaterLevels]
)
def read_waterlevels(pointid: str = None, db: Session = Depends(get_db)):
    q = _read_waterlevels_query(pointid, db)
    return paginate(q)


@router.get(
    "/waterlevels_pressure", response_model=Page[schemas.WaterLevelsContinuous_Pressure]
)
@router.get(
    "/waterlevels_pressure/limit-offset",
    response_model=LimitOffsetPage[schemas.WaterLevelsContinuous_Pressure],
)
def read_waterlevels_pressure(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.WaterLevelsContinuous_Pressure)
    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.WaterLevelsContinuous_Pressure.OBJECTID)
    q = public_release_filter(q)

    return paginate(q)