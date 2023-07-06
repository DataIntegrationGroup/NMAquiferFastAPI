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

from fastapi import APIRouter, Depends, Request, Response

import models
import schemas
from crud import locations_feature_collection
from dependencies import get_db
from ngwmn import make_waterlevels, make_wellconstruction, make_lithology
from routers import templates

router = APIRouter(prefix="/ngwmn", tags=["ngwmn"])


@router.get(
    "/map",
    summary="NGWMN Map view",
    description="Map view of the Collaborative Network",
)
def map_view(request: Request):
    return templates.TemplateResponse(
        "ngwmn_map_view.html",
        {
            "request": request,
            "center": {"lat": 34.5, "lon": -106.0},
            "zoom": 6,
        },
    )


@router.get("/locations/fc",
            response_model=schemas.LocationFeatureCollection,)
async def read_ngwmn_locations_feature_collection(db=Depends(get_db)):

    q = db.query(models.Location, models.Well)
    q = q.join(models.Well)
    q = q.join(models.ProjectLocations)
    q = q.filter(models.ProjectLocations.ProjectName == "NGWMN")

    ls = q.all()
    content = locations_feature_collection(ls)

    return content


@router.get("/waterlevels/{pointid}")
async def read_ngwmn_waterlevels(pointid: str, db=Depends(get_db)):
    data = make_waterlevels(pointid, db)
    return Response(content=data, media_type="application/xml")


@router.get("/wellconstruction/{pointid}")
async def read_ngwmn_wellconstruction(pointid: str, db=Depends(get_db)):
    data = make_wellconstruction(pointid, db)
    return Response(content=data, media_type="application/xml")


@router.get("/lithology/{pointid}")
async def read_ngwmn_lithology(pointid: str, db=Depends(get_db)):
    data = make_lithology(pointid, db)
    return Response(content=data, media_type="application/xml")

# ============= EOF =============================================
