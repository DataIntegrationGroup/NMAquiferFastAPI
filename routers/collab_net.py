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
import csv
import io
import json
import os
import threading
import time

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count, func
from sqlalchemy.testing import in_
from starlette.requests import Request
from starlette.responses import StreamingResponse, FileResponse
from starlette.templating import Jinja2Templates

import models
import schemas
from crud import public_release_filter
from dependencies import get_db
from routers import csv_response, json_response

router = APIRouter(prefix="/collabnet", tags=["collabnet"])
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


@router.get("/map")
def map_view(request: Request, db: Session = Depends(get_db)):
    # ls = get_locations(db)
    # def make_point(loc, well):
    #     return {
    #         "type": "Feature",
    #         "properties": {"name": f"Point {loc.PointID}"},
    #         "geometry": loc.geometry,
    #     }
    stats = [
        {"name": "N. Wells", "value": get_nlocations(db)},
        {"name": "N. Water Levels", "value": get_nwaterlevels(db)},
    ]

    return templates.TemplateResponse(
        "collabnet_map_view.html",
        {
            "request": request,
            "center": {"lat": 34.5, "lon": -106.0},
            "zoom": 6,
            "data_url": "/collabnet/locations",
            # 'stats': stats
            # "nlocations": get_nlocations(db),
            # 'nwaterlevels': get_nwaterlevels(db)
        },
    )


@router.get("/stats")
async def read_stats(db: Session = Depends(get_db)):
    return [
        {"name": "N. Wells", "value": get_nlocations(db)},
        {"name": "N. Water levels", "value": get_nwaterlevels(db)},
    ]


@router.get("/contributors")
async def read_contributions(db: Session = Depends(get_db)):
    cons = get_contributors(db)
    return [{"name": n, "contributions": c} for n, c in cons]


@router.get("/waterlevels/csv")
async def read_waterlevels(db: Session = Depends(get_db)):
    stream = get_waterlevels_csv(db)

    return csv_response("waterlevels.csv", stream)


@router.get("/locations/csv")
def read_locations_csv(db: Session = Depends(get_db)):
    stream = io.StringIO()
    writer = csv.writer(stream)
    ls = get_locations(db)
    writer.writerow(
        (
            "index",
            "PointID",
            "Latitude",
            "Longitude",
            "Elevation (ft asl)",
            "WellDepth (ft bgs)",
        )
    )
    for i, (l, w) in enumerate(ls):
        lon, lat = l.lonlat
        row = (
            i + 1,
            l.PointID,
            lat,
            lon,
            f"{l.Altitude :0.2f}",
            f"{w.WellDepth or 0:0.2f}",
        )
        writer.writerow(row)

    return csv_response("locations", stream.getvalue())


@router.get("/locations/geojson")
def read_locations_geojson(db: Session = Depends(get_db)):
    ls = get_locations(db)
    content = locations_geojson(ls)
    return json_response("locations", content)

    # stream = io.StringIO()
    # stream.write(json.dumps(content))
    # response = StreamingResponse(
    #     iter([stream.getvalue()]), media_type="application/json"
    # )
    # response.headers["Content-Disposition"] = "attachment; filename=locations.json"
    # return response


@router.get("/locations", response_model=schemas.LocationFeatureCollection)
def read_locations_geojson(db: Session = Depends(get_db)):
    ls = get_locations(db)
    content = locations_geojson(ls)
    return content



def get_nlocations(db: Session = Depends(get_db)):
    q = get_locations_query(db)
    return q.count()


def get_nwaterlevels(db: Session = Depends(get_db)):
    q = get_waterlevels_query(db)
    return q.count()


def get_contributors(db: Session = Depends(get_db)):
    q = db.query(models.Well.DataSource, func.count(models.Location.PointID))
    q = q.join(models.Location)
    q = q.join(models.ProjectLocations)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = public_release_filter(q)
    q = q.group_by(models.Well.DataSource)
    return q.all()


def get_waterlevels_query(db):
    q = db.query(models.WaterLevels, models.Well)
    q = q.join(models.Well)
    q = q.join(models.Location)
    q = q.join(models.ProjectLocations)

    q = public_release_filter(q)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = q.order_by(models.Location.PointID)
    return q


def get_waterlevels_csv(db):
    q = get_waterlevels_query(db)
    header = (
        "PointID",
        "DateMeasured",
        "DepthToWaterBGS",
        "MeasurementMethod",
        "DataSource",
        "MeasuringAgency",
        "LevelStatus",
        "DataQuality",
    )

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(header)
    n = q.count()
    for i, (record, well) in enumerate(q.all()):
        print(f"{i + 1}/{n}")
        if record.DateMeasured is None:
            continue

        row = (
            well.PointID,
            record.DateMeasured.isoformat(),
            record.DepthToWaterBGS,
            record.measurement_method,
            record.data_source,
            record.MeasuringAgency,
            record.level_status,
            record.data_quality,
        )
        writer.writerow(map(str, row))
    return stream.getvalue()


def get_locations(db: Session = Depends(get_db)):
    q = get_locations_query(db)
    try:
        return q.all()
    except Exception as e:
        return []


def get_locations_query(db):
    q = db.query(models.Location, models.Well)
    q = q.join(models.ProjectLocations)
    q = q.join(models.Well)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = public_release_filter(q)
    q = q.order_by(models.Location.PointID)
    return q


def locations_geojson(locations):
    def togeojson(l, w):
        return {
            "type": "Feature",
            "properties": {
                "name": l.PointID,
                "well_depth": {"value": w.WellDepth, "units": "ft"},
            },
            "geometry": l.geometry,
        }

    content = {
        "features": [togeojson(*l) for l in locations],
    }

    return content


# def waterlevels_loop():
#     evt = threading.Event()
#     while 1:
#         if os.path.isfile("waterlevels.csv"):
#             s = os.stat("waterlevels.csv")
#             if time.time() - s.st_mtime < 60 * 60 * 24:
#                 continue
#
#         db = next(get_db())
#         txt = get_waterlevels_csv(db)
#         with open("waterlevels.csv", "w") as fp:
#             fp.write(txt)
#
#         evt.wait(1)
#
#
# t = threading.Thread(target=waterlevels_loop)
# t.start()


# ============= EOF =============================================
