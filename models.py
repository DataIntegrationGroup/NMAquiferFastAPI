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
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Float,
    Numeric,
    Date,
    Time,
    DateTime,
)
from sqlalchemy.orm import relationship, declared_attr
from fastapi_utils.guid_type import GUID
from database import Base
from geo_utils import utm_to_latlon


class WellPhotos(Base):
    __tablename__ = "WellPhotos"
    GlobalID = Column(GUID, primary_key=True)
    PointID = Column(String(50))
    OLEPath = Column(String(255))


class Location(Base):
    __tablename__ = "Location"
    LocationId = Column(GUID, primary_key=True)
    PointID = Column(String(50))
    SiteID = Column(String(200))
    AlternateSiteID = Column(String(50))

    PublicRelease = Column(Boolean)
    Easting = Column(Integer)
    Northing = Column(Integer)
    Altitude = Column(Float)
    AltitudeMethod = Column(String(50), ForeignKey("LU_AltitudeMethod.Code"))

    lu_elevation_method = relationship("LU_AltitudeMethod", uselist=False)

    @property
    def elevation_method(self):
        return self.lu_elevation_method.Meaning

    @property
    def geometry(self):
        lon, lat = self.lonlat
        elevation = self.Altitude
        # altitude is in ft above sea level geojson wants meters
        if elevation is not None:
            # convert feet to meters
            elevation *= 0.3048

        return {"coordinates": [lon, lat, elevation], "type": "Point"}

    _lonlat = None

    @property
    def lonlat(self):
        if self._lonlat is None:
            e, n = self.Easting, self.Northing
            lon, lat = utm_to_latlon(e, n)
            self._lonlat = lon, lat
        else:
            lon, lat = self._lonlat

        return lon, lat

    @property
    def geosparql_has_geometry(self):
        lon, lat = self.lonlat
        return {
            "@type": "http://www.opengis.net/ont/sf#Point",
            "geosparql:asWKT": f"POINT({lon}, {lat})",
        }

    @property
    def schema_geo(self):
        lon, lat = self.lonlat
        return {
            "@type": "schema:GeoCoordinates",
            "schema:latitude": lon,
            "schema:longitude": lat,
        }

    @property
    def links(self):
        return [
            {
                "rel": "self",
                "href": str(self.request_url),
                "type": "application/ld+json",
                "title": "This document as RDF (JSON-LD)",
            },
            {
                "rel": "alternate",
                "href": f"{self.request_base_url}location/pointid/{self.PointID}",
                "type": "application/json",
                "title": "This document as JSON",
            },
            {
                "rel": "alternate",
                "href": f"{self.request_base_url}location/pointid/{self.PointID}/geojson",
                "type": "application/geo+json",
                "title": "This document as GeoJSON",
            },
        ]

    @property
    def properties(self):
        return {
            "point_id": self.PointID,
            "alternate_name": self.AlternateSiteID,
            "elevation_method": self.elevation_method,
        }


class LU_Mixin(object):
    Code = Column(Integer, primary_key=True)
    Meaning = Column(String(50))


class LU_Formations(Base, LU_Mixin):
    __tablename__ = "LU_Formations"


class LU_LevelStatus(Base, LU_Mixin):
    __tablename__ = "LU_LevelStatus"


class LU_DataQuality(Base, LU_Mixin):
    __tablename__ = "LU_DataQuality"


class LU_MeasurementMethod(Base, LU_Mixin):
    __tablename__ = "LU_MeasurementMethod"


class LU_DataSource(Base, LU_Mixin):
    __tablename__ = "LU_DataSource"


class LU_AltitudeMethod(Base, LU_Mixin):
    __tablename__ = "LU_AltitudeMethod"


class ProjectLocations(Base):
    __tablename__ = "ProjectLocations"
    GlobalID = Column(GUID, primary_key=True)
    LocationId = Column(GUID, ForeignKey("Location.LocationId"))
    PointID = Column(String(10))
    ProjectName = Column(String(250))


class OwnersData(Base):
    __tablename__ = "OwnersData"
    FirstName = Column(String(50))
    LastName = Column(String(50))
    OwnerKey = Column(String(50), primary_key=True)
    Email = Column(String(50))
    CellPhone = Column(String(50))
    Phone = Column(String(50))
    MailingAddress = Column(String(50))


class OwnerLink(Base):
    __tablename__ = "OwnerLink"
    GlobalID = Column(GUID, primary_key=True)
    LocationId = Column(GUID, ForeignKey("Location.LocationId"))
    OwnerKey = Column(String(50), ForeignKey("OwnersData.OwnerKey"))


class Equipment(Base):
    __tablename__ = "Equipment"
    ID = Column(Integer, primary_key=True)
    PointID = Column(String(50))
    LocationId = Column(GUID, ForeignKey("Location.LocationId"))
    EquipmentType = Column(String(50))
    Model = Column(String(50))
    SerialNo = Column(String(50))
    DateInstalled = Column(DateTime)
    DateRemoved = Column(DateTime)
    RecordingInterval = Column(Integer)
    Equipment_Notes = Column(String(50), name="Equipment Notes")


class Well(Base):
    __tablename__ = "WellData"
    # LocationId = Column(GUID, ForeignKey("Location.LocationId"))
    LocationId = Column(GUID)
    WellID = Column(GUID, primary_key=True)
    PointID = Column(String(50), ForeignKey("Location.PointID"))
    HoleDepth = Column(Integer)
    WellDepth = Column(Integer)
    OSEWellID = Column(String(50))
    OSEWelltagID = Column(String(50))
    MeasuringPoint = Column(String(50))
    MPHeight = Column(Numeric)
    CasingDiameter = Column(Numeric)
    CasingDepth = Column(Numeric)
    CasingDescription = Column(String(50))
    FormationZone = Column(String(50), ForeignKey("LU_Formations.Code"))
    StaticWater = Column(Numeric)
    DataSource = Column(String(200))
    MonitoringStatus = Column(String(3))

    lu_formation = relationship("LU_Formations", backref="wells", uselist=False)
    location = relationship("Location", backref="well", uselist=False)
    manual_waterlevels = relationship("WaterLevels", backref="well", uselist=False)

    @property
    def pod_url(self):
        ose_id = self.OSEWellID
        if ose_id:
            url = (
                "https://services2.arcgis.com/qXZbWTdPDbTjl7Dy/arcgis/rest/services/"
                "OSE_PODs/FeatureServer/0/query?"
                f"where=+db_file%3D%27{ose_id}%27&f=pjson&outFields=*"
            )
            return url

    @property
    def formation(self):
        return self.lu_formation.Meaning


class MeasurementMixin(object):
    MeasuringAgency = Column(String(50))

    @declared_attr
    def MeasurementMethod(cls):
        return Column(String(50), ForeignKey("LU_MeasurementMethod.Code"))

    @declared_attr
    def DataSource(cls):
        return Column(String(50), ForeignKey("LU_DataSource.Code"))

    @declared_attr
    def lu_measurement_method(cls):
        return relationship("LU_MeasurementMethod", uselist=False, lazy="joined")

    @declared_attr
    def lu_data_source(cls):
        return relationship("LU_DataSource", uselist=False, lazy="joined")

    @property
    def measurement_method(self):
        try:
            return self.lu_measurement_method.Meaning
        except AttributeError:
            return ""

    @property
    def data_source(self):
        try:
            return self.lu_data_source.Meaning
        except AttributeError:
            return ""


class WaterLevelsContinuous_Pressure(Base, MeasurementMixin):
    __tablename__ = "WaterLevelsContinuous_Pressure"
    GlobalID = Column(GUID, primary_key=True)
    OBJECTID = Column(Integer)
    WellID = Column(GUID, ForeignKey("WellData.WellID"))
    DepthToWaterBGS = Column(Numeric)

    DateMeasured = Column(DateTime)


class WaterLevelsContinuous_Acoustic(Base, MeasurementMixin):
    __tablename__ = "WaterLevelsContinuous_Acoustic"
    GlobalID = Column(GUID, primary_key=True)
    OBJECTID = Column(Integer)
    WellID = Column(GUID, ForeignKey("WellData.WellID"))
    DepthToWaterBGS = Column(Numeric)

    DateMeasured = Column(DateTime)


class WaterLevels(Base, MeasurementMixin):
    __tablename__ = "WaterLevels"
    OBJECTID = Column(Integer, primary_key=True)
    WellID = Column(
        GUID, ForeignKey("WellData.WellID"), primary_key=True, cache_ok=True
    )
    DepthToWaterBGS = Column(Numeric)
    DateMeasured = Column(Date)
    TimeMeasured = Column(Time)

    PublicRelease = Column(Boolean)

    @declared_attr
    def LevelStatus(self):
        return Column(String(2), ForeignKey("LU_LevelStatus.Code"))

    @declared_attr
    def DataQuality(self):
        return Column(String(2), ForeignKey("LU_DataQuality.Code"))

    @declared_attr
    def lu_level_status(cls):
        return relationship("LU_LevelStatus", uselist=False, lazy="joined")

    @declared_attr
    def lu_data_quality(cls):
        return relationship("LU_DataQuality", uselist=False, lazy="joined")

    @property
    def level_status(self):
        try:
            return self.lu_level_status.Meaning
        except AttributeError:
            return ""

    @property
    def data_quality(self):
        try:
            return self.lu_data_quality.Meaning
        except AttributeError:
            return ""

# ============= EOF =============================================
