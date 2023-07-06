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
from ngwmn_xml import lithology_xml, well_construction_xml, water_levels_xml2


def make_xml_response(db, sql, point_id, func):
    if not isinstance(sql, (tuple, list)):
        sql = (sql,)

    rs = []
    for si in sql:
        records = db.execute(si, {"point_id": point_id})
        rs.append(records.fetchall())
    return func(*rs)


def make_lithology(point_id, db):
    sql = "select * from dbo.view_NGWMN_Lithology where PointID=:point_id"
    return make_xml_response(db, sql, point_id, lithology_xml)


def make_wellconstruction(point_id, db):
    sql = "select * from dbo.view_NGWMN_WellConstruction where PointID=:point_id"
    return make_xml_response(db, sql, point_id, well_construction_xml)


def make_waterlevels(point_id, db):
    sql = "select * from dbo.view_NGWMN_WaterLevels where PointID=:point_id"
    sql2 = "select * from dbo.WaterLevelsContinuous_Pressure_Daily where PointID=:point_id and QCed=1"

    return make_xml_response(db, (sql, sql2), point_id, water_levels_xml2)

# ============= EOF =============================================
