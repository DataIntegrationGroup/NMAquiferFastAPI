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

from fastapi import APIRouter, Depends
from starlette.responses import Response

from dependencies import get_db
from ngwmn import make_waterlevels, make_wellconstruction, make_lithology

router = APIRouter(prefix="/ngwmn", tags=["ngwmn"])


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
