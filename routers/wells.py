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
from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK

import models
import schemas
from crud import _read_pods, public_release_filter
from dependencies import get_db

router = APIRouter()


@router.get("/well", response_model=schemas.Well)
def read_well(pointid: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Well)
    if pointid:
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
        q = q.order_by(models.Well.WellID)
        q = public_release_filter(q)
        return q.first()
    else:
        return Response(status_code=HTTP_200_OK)


@router.get("/pod", response_model=List[schemas.Well])
def read_pods(pointid: str = None, db: Session = Depends(get_db)):
    pods = _read_pods(pointid, db)
    if pods is None:
        pods = Response(status_code=HTTP_200_OK)
    return pods


# ============= EOF =============================================
