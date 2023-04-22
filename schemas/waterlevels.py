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
from datetime import date, time, datetime
from typing import Union

from pydantic import Field

from schemas import ORMBaseModel, Measurement


class WaterLevels(ORMBaseModel):
    DepthToWaterBGS: Union[float, None] = Field(..., alias="depth_to_water_ftbgs")
    DateMeasured: Union[date, None] = Field(..., alias="measurement_date")
    TimeMeasured: Union[time, None] = Field(..., alias="measurement_time")


class WaterLevelsContinuous_Pressure(Measurement):
    DepthToWaterBGS: Union[float, None] = Field(..., alias="depth_to_water_ftbgs")
    DateMeasured: Union[datetime, None] = Field(..., alias="measurement_datetime")


class WaterLevelsContinuous_Acoustic(Measurement):
    DepthToWaterBGS: Union[float, None] = Field(..., alias="depth_to_water_ftbgs")
    DateMeasured: Union[datetime, None] = Field(..., alias="measurement_datetime")


# ============= EOF =============================================
