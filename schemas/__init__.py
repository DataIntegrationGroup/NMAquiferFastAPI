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
from datetime import datetime, date
from typing import Union, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ORMBaseModel(BaseModel):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class Measurement(ORMBaseModel):
    MeasurementMethod: Union[str, None] = Field(..., alias="measurement_method")
    MeasuringAgency: Union[str, None] = Field(..., alias="measuring_agency")
    DataSource: Union[str, None] = Field(..., alias="data_source")
    DataQuality: Union[str, None] = Field(..., alias="data_quality")


class Location(ORMBaseModel):
    LocationId: UUID
    PointID: str
    PublicRelease: bool
    AlternateSiteID: Union[str, None]  # = Field(..., alias="alternate_site_id")
    elevation_method: Union[str, None]  # = Field(..., alias="elevation_method")
    Elevation: Union[float, None]
    SiteNames: Union[str, None]  # = Field(..., alias="site_names")
    SiteID: Union[str, None]  # = Field(..., alias="site_id")
    Easting: Union[float, None]
    Northing: Union[float, None]
    geometry: Optional[dict] = None

    @validator("Elevation")
    def elevation_check(cls, v):
        if v is not None:
            return round(v, 2)
        else:
            return 0


class ProjectLocations(ORMBaseModel):
    GlobalID: Union[UUID, None]
    LocationId: Union[UUID, None]
    PointID: Union[str, None]
    ProjectName: Union[str, None]


class Equipment(ORMBaseModel):
    PointID: str
    LocationId: UUID
    EquipmentType: Union[str, None]
    Model: Union[str, None]
    SerialNo: Union[str, None]
    DateInstalled: Union[date, None]
    DateRemoved: Union[date, None]
    RecordingInterval: Union[int, None]
    Equipment_Notes: Union[str, None]


class OwnersData(ORMBaseModel):
    FirstName: Union[str, None]
    LastName: Union[str, None]
    OwnerKey: Union[str, None]
    Email: Union[str, None]
    CellPhone: Union[str, None]
    Phone: Union[str, None]
    MailingAddress: Union[str, None]
    MailCity: Union[str, None]
    MailState: Union[str, None]
    MailZipCode: Union[str, None]
    PhysicalAddress: Union[str, None]
    PhysicalCity: Union[str, None]
    PhysicalState: Union[str, None]
    PhysicalZipCode: Union[str, None]
    SecondLastName: Union[str, None]
    SecondFirstName: Union[str, None]
    SecondCtctEmail: Union[str, None]
    SecondCtctPhone: Union[str, None]


class LocationJSONLD(Location):
    context: list = Field(
        [
            {
                "schema": "https://schema.org/",
                "geoconnex": "@id",
                "type": "@type",
                "geosparql": "http://www.opengis.net/ont/geosparql#",
            },
            {
                "sosa": "http://www.w3.org/ns/sosa/",
                "ssn": "http://www.w3.org/ns/ssn/",
                "Datastreams": "sosa:ObservationCollection",
                "name": "schema:name",
                "Locations": "schema:location",
                "description": "schema:description",
            },
        ],
        alias="@context",
    )
    type: str = "schema:Place"

    geosparql_has_geometry: dict = Field(..., alias="geosparql:hasGeometry")
    schema_geo: dict = Field(..., alias="schema:geo")
    links: list = Field(..., alias="links")


class LocationGeoJSON(ORMBaseModel):
    type: str = "Feature"
    properties:  dict = Field(default={}, alias="properties")
    geometry: dict = Field(..., alias="geometry")


class LocationFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list = Field(..., alias="features")


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

    @validator("CasingDiameter", "MPHeight")
    def round(cls, v):
        if v is not None:
            return round(v, 2)

# ============= EOF =============================================
