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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from starlette.requests import Request
from starlette.templating import Jinja2Templates

import models
import schemas
from crud import public_release_filter
from dependencies import get_db
from routers import csv_response, json_response
from pathlib import Path

router = APIRouter(prefix="/collabnet", tags=["collabnet"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


@router.get(
    "/map",
    summary="Collab Network Map view",
    description="Map view of the Collaborative Network",
)
def map_view(request: Request):
    return templates.TemplateResponse(
        "collabnet_map_view.html",
        {
            "request": request,
            "center": {"lat": 34.5, "lon": -106.0},
            "zoom": 6,
        },
    )


@router.get(
    "/stats",
    summary="Collab Network Stats",
    description="Stats for the Collaborative Network",
)
async def read_stats(db: Session = Depends(get_db)):
    return {"nlocations": _get_nlocations(db), "nwaterlevels": _get_nwaterlevels(db)}


@router.get(
    "/contributors",
    summary="Collab Network Contributors",
    description="Contributors to the Collaborative Network",
)
async def read_contributions(db: Session = Depends(get_db)):
    cons = _get_contributors(db)
    return [{"name": n, "contributions": c} for n, c in cons]


@router.get(
    "/waterlevels/csv",
    summary="Collab Network Water Levels CSV",
    description="Get all the water levels for all the wells in the Collaborative Network as a CSV file",
)
async def read_waterlevels(db: Session = Depends(get_db)):
    content = _get_waterlevels_csv(db)
    return csv_response("waterlevels.csv", content)


@router.get(
    "/locations/csv",
    summary="Collab Network Locations CSV",
    description="Get all the wells in the Collaborative Network as a CSV file",
)
def read_locations_csv(db: Session = Depends(get_db)):
    stream = io.StringIO()
    writer = csv.writer(stream)
    ls = _get_locations(db)
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


@router.get(
    "/locations/geojson",
    summary="Collab Network Locations GeoJSON",
    description="Get all the wells in the Collaborative Network as a GeoJSON file",
)
def read_locations_geojson(db: Session = Depends(get_db)):
    ls = _get_locations(db)
    content = _locations_geojson(ls)
    return json_response("locations", content)


@router.get(
    "/locations",
    response_model=schemas.LocationFeatureCollection,
    summary="Collab Network Locations",
    description="Get all the wells in the Collaborative Network as a GeoJSON FeatureCollection",
)
def read_locations_geojson(db: Session = Depends(get_db)):
    ls = _get_locations(db)
    content = _locations_geojson(ls)
    return content


# =========== helper functions ===========
def _get_nlocations(db: Session = Depends(get_db)):
    q = _get_locations_query(db)
    return q.count()


def _get_nwaterlevels(db: Session = Depends(get_db)):
    q = _get_waterlevels_query(db)
    return q.count()


def _get_contributors(db: Session = Depends(get_db)):
    q = db.query(models.Well.DataSource, func.count(models.Location.PointID))
    q = q.join(models.Location)
    q = q.join(models.ProjectLocations)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = public_release_filter(q)
    q = q.group_by(models.Well.DataSource)
    return q.all()


def _get_waterlevels_query(db):
    q = db.query(models.WaterLevels, models.Well)
    q = q.join(models.Well)
    q = q.join(models.Location)
    q = q.join(models.ProjectLocations)

    q = public_release_filter(q)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = q.order_by(models.Location.PointID)
    return q


def _get_waterlevels_csv(db):
    q = _get_waterlevels_query(db)
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


def _get_locations(db: Session = Depends(get_db)):
    q = _get_locations_query(db)
    try:
        return q.all()
    except Exception as e:
        return []


def _get_locations_query(db):
    q = db.query(models.Location, models.Well)
    q = q.join(models.ProjectLocations)
    q = q.join(models.Well)
    q = q.filter(models.ProjectLocations.ProjectName == "Water Level Network")
    q = public_release_filter(q)
    q = q.order_by(models.Location.PointID)
    return q


def _locations_geojson(locations):
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


# ============= EOF =============================================
