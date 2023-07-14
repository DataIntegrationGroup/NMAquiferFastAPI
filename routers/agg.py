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
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

import models
import schemas
from crud import locations_feature_collection, get_location, read_well, read_ose_pod
from dependencies import get_db
from ngwmn import make_waterlevels, make_wellconstruction, make_lithology
from routers import templates
from routers.usgs import get_site_metadata

router = APIRouter(prefix="/agg", tags=["aggregation"])


@router.get("/{pointid}/sitemetadata")
def get_agg_sitemetadata(pointid: str, db: Session = Depends(get_db)):
    nmbgmr_sm = location = get_location(pointid, db)
    if nmbgmr_sm:
        nmbgmr_sm = schemas.Location.from_orm(nmbgmr_sm)

    well = read_well(pointid, db)
    ose_sm, pod_url = read_ose_pod(well.OSEWellID)

    usgs_sm = get_site_metadata(location=location)

    return {"usgs": usgs_sm, "ose": ose_sm, "nmbgmr": nmbgmr_sm}


# ============= EOF =============================================
