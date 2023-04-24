# ===============================================================================
# Copyright 2018 ross
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
from datetime import datetime
from xml.etree import ElementTree as etree

# NSMAP = dict(xsi="http://www.w3.org/2001/XMLSchema-instance", xsd="http://www.w3.org/2001/XMLSchema")


def continuous_water_levels_xml(records):
    return make_xml("WaterLevels", records, make_continuous_water_level)


def water_levels_xml(records):
    return make_xml("WaterLevels", records, make_water_level)


def water_levels_xml2(manual, pressure):
    if not pressure:
        return make_xml("WaterLevels", manual, make_water_level)
    else:
        root = etree.Element("WaterLevels")
        # doc = etree.ElementTree(root)

        columns = [
            "GlobalID",
            "OBJECTID",
            "WellID",
            "PointID",
            "DateMeasured",
            "TemperatureWater",
            "WaterHead",
            "WaterHeadAdjusted",
            "DepthToWaterBGS",
            "MeasurementMethod",
            "DataSource",
            "MeasuringAgency",
            "QCed",
            "Notes",
            "Created",
            "Updated",
            "ProcessedBy",
            "CheckedBy",
            "CONDDL (mS/cm)",
        ]

        manual_dates = [r[1] for r in manual]
        records = []
        for r in pressure:
            dm = r[columns.index("DateMeasured")]
            tag = "pressure"
            if dm.date() in manual_dates:
                ri = next((ri for ri in manual if ri[1] == dm.date()))
                if ri[2] < r[columns.index("DepthToWaterBGS")]:
                    r = ri
                    tag = "manual"
                manual.remove(ri)

            records.append((tag, r))

        for mi in manual:
            records.append(("manual", mi))

        for k, record in sorted(
            records, key=lambda r: r[1][4].date() if r[0] == "pressure" else r[1][1]
        ):
            if k == "pressure":
                make_continuous_water_level(root, record)
            else:
                make_water_level(root, record)
        return etree.tostring(root)


def well_construction_xml(records):
    return make_xml("Casings", records, make_well_construction)


def lithology_xml(records):
    return make_xml("Lithologies", records, make_lithology)


def make_xml(name, records, make_record):
    root = etree.Element(name)
    # doc = etree.ElementTree(root)
    for r in records:
        make_record(root, r)

    # etree.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    # etree.register_namespace('xsd', 'http://www.w3.org/2001/XMLSchema')

    return etree.tostring(root)


# ==================== make records =======================
def make_continuous_water_level(root, r):
    elem = etree.SubElement(root, "WaterLevel")
    make_point_id(elem, r, idx=3)

    columns = [
        "GlobalID",
        "OBJECTID",
        "WellID",
        "PointID",
        "DateMeasured",
        "TemperatureWater",
        "WaterHead",
        "WaterHeadAdjusted",
        "DepthToWaterBGS",
        "MeasurementMethod",
        "DataSource",
        "MeasuringAgency",
        "QCed",
        "Notes",
        "Created",
        "Updated",
        "ProcessedBy",
        "CheckedBy",
        "CONDDL (mS/cm)",
    ]

    m = r[columns.index("DateMeasured")]

    # m = datetime.strptime(m, '%Y-%m-%d')
    for attr, val in (
        (
            "DepthFromLandSurfaceData",
            "{:0.2f}".format(r[columns.index("DepthToWaterBGS")]),
        ),
        ("WaterLevelUnits", "ft bgs"),
        ("MeasuringMethod", "Pressure Transducer"),
        ("MeasurementMonth", m.month),
        ("MeasurementDay", m.day),
        ("MeasurementYear", m.year),
        ("MeasurementTime", "0:00:00"),
        ("MeasurementTimezone", "MST"),
        ("WaterLevelAccuracy", "0.02 ft"),
    ):
        e = etree.SubElement(elem, attr)
        e.text = str(val)


def make_water_level(root, r):
    elem = etree.SubElement(root, "WaterLevel")
    make_point_id(elem, r)

    m = r[1]

    # m = datetime.strptime(m, '%Y-%m-%d')
    for attr, val in (
        ("DepthFromLandSurfaceData", "{:0.2f}".format(r[2])),
        ("WaterLevelUnits", r[3]),
        ("MeasuringMethod", r[4]),
        ("MeasurementMonth", m.month),
        ("MeasurementDay", m.day),
        ("MeasurementYear", m.year),
        ("MeasurementTime", "0:00:00"),
        ("MeasurementTimezone", "MST"),
        ("WaterLevelAccuracy", r[5]),
    ):
        e = etree.SubElement(elem, attr)
        e.text = str(val)


def make_well_construction(root, r):
    """
    0        1         2             3          4       5            6,    7,  8
    pointid, castop, casbottom, cadepthunits, screentop, screenbotom, units,screen description, casing description
    :param root:
    :param r:
    :return:
    """
    elem = etree.SubElement(root, "Casing")
    make_point_id(elem, r)

    e = etree.SubElement(elem, "CasingTop")
    e.text = str(r[1])

    e = etree.SubElement(elem, "CasingBottom")
    e.text = str(r[2])

    e = etree.SubElement(elem, "CasingDepthUnits")
    e.text = str(r[3])

    e = etree.SubElement(elem, "ScreenTop")
    e.text = str(r[4])

    e = etree.SubElement(elem, "ScreenBottom")
    e.text = str(r[5])

    e = etree.SubElement(elem, "ScreenBottomUnits")
    e.text = str(r[6])

    # e = etree.SubElement(elem, 'ScreenDescription')
    # e.text = str(r[7])
    # e = etree.SubElement(elem, 'CasingDescription')
    # e.text = str(r[8])

    e = etree.SubElement(elem, "ScreenIntervalMaterial")
    e.text = str(r[7]) if r[7] else "Unknown"
    e = etree.SubElement(elem, "CasingIntervalMaterial")
    e.text = str(r[8]) if r[8] else "Unknown"


def make_lithology(root, r):
    elem = etree.SubElement(root, "Lithology")
    make_point_id(elem, r)

    e = etree.SubElement(elem, "LithologyCode")
    e.text = r[1]

    e = etree.SubElement(elem, "TERM")
    e.text = r[2]

    e = etree.SubElement(elem, "StratSource")
    e.text = r[3]

    e = etree.SubElement(elem, "StratTop")
    e.text = str(r[4])

    e = etree.SubElement(elem, "StratTopUnit")
    e.text = str(r[5])

    e = etree.SubElement(elem, "StratBottom")
    e.text = str(r[6])

    e = etree.SubElement(elem, "StratBottomUnit")
    e.text = str(r[7])


def make_point_id(elem, r, idx=0):
    e = etree.SubElement(elem, "PointID")
    e.text = str(r[idx])


# ============= EOF =============================================
