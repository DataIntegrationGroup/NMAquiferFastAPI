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
import io
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

import models
import schemas
from crud import public_release_filter, read_waterlevels_manual_query
from dependencies import get_db

router = APIRouter(prefix="/collabnet", tags=["collabnet"])


@router.get("/waterlevels")
def read_waterlevels(db: Session = Depends(get_db)):
    q = db.query(models.Location)
    q = q.join(models.ProjectLocations)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = public_release_filter(q)
    locations = q.all()

    rows = []
    for l in locations:
        waterlevels = read_waterlevels_manual_query(l.PointID, db)
        for wi in waterlevels:
            rows.append((l.PointID, wi.DateMeasured, wi.DepthToWaterBGS))

    stream = io.StringIO()
    stream.write('\n'.join([','.join(map(str, r)) for r in rows]))
    response = StreamingResponse(
        iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=waterlevels.csv"
    return response


@router.get("/locations/geojson")
def read_locations_geojson(db: Session = Depends(get_db)):
    content = get_locations(db)
    stream = io.StringIO()
    stream.write(json.dumps(content))
    response = StreamingResponse(
        iter([stream.getvalue()]), media_type="application/json")
    response.headers["Content-Disposition"] = "attachment; filename=locations.json"
    return response


@router.get("/locations", response_model=schemas.LocationFeatureCollection)
def read_locations_geojson(db: Session = Depends(get_db)):
    content = get_locations(db)
    return content


def get_locations(db: Session = Depends(get_db)):
    q = db.query(models.Location, models.Well)
    q = q.join(models.ProjectLocations)
    q = q.join(models.Well)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = public_release_filter(q)
    locations = q.all()

    def togeojson(l, w):

        return {
            "type": "Feature",
            "properties": {"name": l.PointID,
                           "well_depth": {"value": w.WellDepth,
                                          "units": "ft"},},
            "geometry": l.geometry,
        }

    content = {
        "features": [togeojson(*l) for l in locations],
    }


    return content

# ============= EOF =============================================
