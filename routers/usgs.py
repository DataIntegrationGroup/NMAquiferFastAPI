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
import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies import get_db
from crud import get_location

router = APIRouter(prefix="/usgs", tags=["usgs"])


@router.get("/sitemetadata/{pointid}")
def get_site_metadata(pointid: str, db: Session = Depends(get_db)):
    loc = get_location(pointid, db)
    return get_site_metadata(location=loc)


def get_usgs_gwl(siteid):
    if siteid:
        url = f"https://waterservices.usgs.gov/nwis/gwlevels/?format=json&sites={siteid}&siteStatus=all"
        resp = requests.get(url)
        return extract_usgs_timeseries(resp.json())


def extract_usgs_timeseries(obj):
    ts = obj["value"]["timeSeries"]
    data = []
    for i, ti in enumerate(ts):
        # print(ti.keys(), ti['variable'].keys(), ti['variable']['variableCode'][0])
        # print(ti['variable']['variableName'])
        # if ti['variable']['variableCode'][0]['variableID'] == 52331280:
        if (
            ti["variable"]["variableName"]
            == "Depth to water level, ft below land surface"
        ):
            for j, tj in enumerate(ti["values"]):
                values = tj["value"]
                data.append(
                    {
                        "phenomenonTime": values[0]["dateTime"],
                        "result": values[0]["value"],
                    }
                )

    return data


def get_site_metadata(location):
    siteid = location.SiteID
    url = f"https://waterservices.usgs.gov/nwis/site/?format=rdb&sites={siteid}&siteStatus=all&siteOutput=expanded"
    resp = requests.get(url)
    if resp.status_code == 200:
        return make_site_record(resp.text), url


def make_site_record(txt):
    for line in txt.split("\n"):
        if line.startswith("#"):
            continue

        if line.startswith("agency_cd"):
            header = [h.strip() for h in line.split("\t")]
            continue

        if line.startswith("5s"):
            continue

        return dict(zip(header, [l.strip() for l in line.split("\t")]))


# ============= EOF =============================================
