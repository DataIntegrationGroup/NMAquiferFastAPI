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
from datetime import date, time, datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class ORMBaseModel(BaseModel):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class Location(ORMBaseModel):
    LocationId: UUID
    PointID: str
    PublicRelease: bool
    geometry: Optional[dict] = None


class Well(ORMBaseModel):
    LocationId: UUID
    WellID: UUID
    PointID: Union[str, None]
    OSEWellID: Union[str, None] = Field(..., alias="ose_well_id")
    OSEWelltagID: Union[str, None] = Field(..., alias="ose_welltag_id")
    HoleDepth: Union[float, None] = Field(..., alias="hole_depth_ftbgs")
    WellDepth: Union[float, None] = Field(..., alias="well_depth_ftbgs")

    CasingDiameter: Union[float, None] = Field(..., alias="casing_diameter_ft")
    CasingDepth: Union[float, None] = Field(..., alias="casing_depth_ftbgs")
    CasingDescription: Union[str, None] = Field(..., alias="casing_description")

    MeasuringPoint: Union[str, None] = Field(..., alias="measuring_point")
    MPHeight: Union[float, None] = Field(..., alias="measuring_point_height_ft")

    FormationZone: Union[str, None] = Field(..., alias="formation")

    StaticWater: Union[float, None] = Field(..., alias="static_water_level_ftbgs")

    pods: Optional[list] = None


class Measurement(ORMBaseModel):
    MeasurementMethod: Union[str, None] = Field(..., alias="measurement_method")
    MeasuringAgency: Union[str, None] = Field(..., alias="measuring_agency")
    DataSource: Union[str, None] = Field(..., alias="data_source")


class WaterLevels(ORMBaseModel):
    DepthToWaterBGS: Union[float, None] = Field(..., alias="depth_to_water_ftbgs")
    DateMeasured: Union[date, None] = Field(..., alias="measurement_date")
    TimeMeasured: Union[time, None] = Field(..., alias="measurement_time")


class WaterLevelsContinuous_Pressure(Measurement):
    DepthToWaterBGS: Union[float, None] = Field(..., alias="depth_to_water_ftbgs")
    DateMeasured: Union[datetime, None] = Field(..., alias="measurement_datetime")


# ============= EOF =============================================
