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
import csv
import io

from fastapi import Depends, APIRouter
from fastapi_pagination import Page, LimitOffsetPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

import models
from schemas import waterlevels
from crud import (
    read_waterlevels_manual_query,
    read_waterlevels_acoustic_query,
    read_waterlevels_pressure_query,
)
from dependencies import get_db

router = APIRouter(prefix="/waterlevels", tags=["waterlevels"])


@router.get("/manual", response_model=Page[waterlevels.WaterLevels])
@router.get(
    "/manual/limit-offset",
    response_model=LimitOffsetPage[waterlevels.WaterLevels],
    include_in_schema=False,
)
def read_waterlevels_manual(pointid: str = None, db: Session = Depends(get_db)):
    q = read_waterlevels_manual_query(pointid, db)
    return paginate(q)


@router.get(
    "/pressure", response_model=Page[waterlevels.WaterLevelsContinuous_Pressure]
)
@router.get(
    "/pressure/limit-offset",
    response_model=LimitOffsetPage[waterlevels.WaterLevelsContinuous_Pressure],
    include_in_schema=False,
)
def read_waterlevels_pressure(pointid: str = None, db: Session = Depends(get_db)):
    q = read_waterlevels_pressure_query(pointid, db)
    return paginate(q)


@router.get(
    "/acoustic", response_model=Page[waterlevels.WaterLevelsContinuous_Acoustic]
)
@router.get(
    "/acoustic/limit-offset",
    response_model=LimitOffsetPage[waterlevels.WaterLevelsContinuous_Acoustic],
    include_in_schema=False,
)
def read_waterlevels_acoustic(pointid: str = None, db: Session = Depends(get_db)):
    q = read_waterlevels_acoustic_query(pointid, db)
    return paginate(q)


@router.get("/{pointid}/csv")
def read_waterlevels_csv(pointid: str, db: Session = Depends(get_db)):
    manual = read_waterlevels_manual_query(pointid, db).all()
    acoustic = read_waterlevels_acoustic_query(pointid, db).all()
    pressure = read_waterlevels_pressure_query(pointid, db).all()

    rows = []
    rows.append(["#DateMeasured", "DepthToWater (ftbgs)"])
    rows.append(["#Manual Water Levels"])

    for mi in manual:
        row = [mi.DateMeasured, mi.DepthToWaterBGS]
        rows.append(row)

    if acoustic:
        rows.append(["#Acoustic Water Levels"])
        for ai in acoustic:
            row = [ai.DateMeasured, ai.DepthToWaterBGS]
            rows.append(row)

    if pressure:
        rows.append(["#Pressure Water Levels"])
        for pi in pressure:
            row = [pi.DateMeasured, pi.DepthToWaterBGS]
            rows.append(row)

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerows(rows)

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={pointid}_waterlevels.csv"
    return response


# ============= EOF =============================================
