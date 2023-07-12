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

import models
import requests


def geometry_filter(q):
    return q.filter(models.Location.Easting != None).filter(
        models.Location.Northing != None
    )


def collabnet_filter(q):
    return q.filter(models.ProjectLocations.ProjectName == "Water Level Network")


def public_release_filter(q):
    return q.filter(models.Location.PublicRelease == True)


def pointid_filter(q, pointid):
    if pointid:
        q = q.filter(models.Location.PointID == pointid)
    return q


def active_monitoring_filter(q):
    q = q.filter(models.Well.MonitoringStatus.notlike("%I%"))
    q = q.filter(models.Well.MonitoringStatus.notlike("%C%"))
    q = q.filter(models.Well.MonitoringStatus.notlike("%X%"))
    return q


# readers
def read_locations(db, pointid=None):
    q = db.query(models.Location)
    q = pointid_filter(q, pointid)
    q = public_release_filter(q)
    return q


def read_waterlevels_acoustic_query(pointid, db, as_dict=False):
    if as_dict:
        q = db.query(models.WaterLevelsContinuous_Acoustic.__table__)
    else:
        q = db.query(models.WaterLevelsContinuous_Acoustic)

    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = pointid_filter(q, pointid)
    q = q.order_by(models.WaterLevelsContinuous_Acoustic.DateMeasured)
    q = public_release_filter(q)
    return q


def read_waterlevels_acoustic_query(pointid, db, as_dict=False):
    return read_waterlevels_continuous_query(
        models.WaterLevelsContinuous_Acoustic, pointid, db, as_dict=as_dict
    )


def read_waterlevels_pressure_query(pointid, db, as_dict=False):
    return read_waterlevels_continuous_query(
        models.WaterLevelsContinuous_Pressure, pointid, db, as_dict=as_dict
    )


def read_waterlevels_continuous_query(table, pointid, db, as_dict=False):
    if as_dict:
        q = db.query(table.__table__)
    else:
        q = db.query(table)

    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = pointid_filter(q, pointid)
    q = q.order_by(table.DateMeasured)
    q = public_release_filter(q)
    return q


def read_waterlevels_manual_query(pointid, db, as_dict=False):
    if as_dict:
        q = db.query(models.WaterLevels.__table__)
    else:
        q = db.query(models.WaterLevels)

    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = pointid_filter(q, pointid)
    q = q.order_by(models.WaterLevels.DateMeasured)
    q = public_release_filter(q)
    return q


def read_equipment(pointid, db):
    q = db.query(models.Equipment)
    q = q.join(models.Location)
    q = pointid_filter(q, pointid)
    return q.all()


def read_well(pointid, db):
    q = db.query(models.Well)
    if pointid:
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    return q.first()


def read_ose_pod(ose_id):
    url = (
        "https://services2.arcgis.com/qXZbWTdPDbTjl7Dy/arcgis/rest/services/"
        "OSE_PODs/FeatureServer/0/query?"
        f"where=+db_file%3D%27{ose_id}%27&f=pjson&outFields=*"
    )
    return requests.get(url).json(), url


# def _read_pods(pointid, db):
#     q = db.query(models.Well)
#     if pointid:
#         q = q.join(models.Location)
#         q = q.filter(models.Location.PointID == pointid)
#         q = q.order_by(models.Well.WellID)
#         q = public_release_filter(q)
#
#         ps = q.all()
#
#         for pi in ps:
#             ose_id = pi.OSEWellID
#             pi.pods = []
#             if ose_id:
#                 url = 'https://services2.arcgis.com/qXZbWTdPDbTjl7Dy/arcgis/rest/services/' \
#                       'OSE_PODs/FeatureServer/0/query?'\
#                       f'where=+db_file%3D%27{ose_id}%27&f=pjson&outFields=*'
#
#                 pi.pod_url = url
#
#         return ps


def locations_feature_collection(locations):
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
