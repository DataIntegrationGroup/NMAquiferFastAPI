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
import models
import requests


def public_release_filter(q):
    return q.filter(models.Location.PublicRelease == True)


# readers
def read_locations(db, pointid=None):
    q = db.query(models.Location)
    if pointid:
        q = q.filter(models.Location.PointID == pointid)
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
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.WaterLevelsContinuous_Acoustic.DateMeasured)
    q = public_release_filter(q)
    return q


def read_waterlevels_pressure_query(pointid, db, as_dict=False):
    if as_dict:
        q = db.query(models.WaterLevelsContinuous_Pressure.__table__)
    else:
        q = db.query(models.WaterLevelsContinuous_Pressure)

    if pointid:
        q = q.join(models.Well)
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.WaterLevelsContinuous_Pressure.DateMeasured)
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
        q = q.filter(models.Location.PointID == pointid)
    q = q.order_by(models.WaterLevels.DateMeasured)
    q = public_release_filter(q)
    return q

def read_well(pointid, db):
    q = db.query(models.Well)
    if pointid:
        q = q.join(models.Location)
        q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    return q.first()


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


# ============= EOF =============================================
