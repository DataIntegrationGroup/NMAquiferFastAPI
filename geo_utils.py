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
import pyproj

PROJECTIONS = {}


def utm_to_latlon(e, n, zone=13):
    name = f"utm{zone}"
    if name not in PROJECTIONS:
        pr = pyproj.Proj(proj="utm", zone=int(zone), ellps="WGS84")
        PROJECTIONS[name] = pr
    pr = PROJECTIONS[name]
    return pr(e, n, inverse=True)


def latlon_to_utm(lon, lat):
    name = "latlon"
    if name not in PROJECTIONS:
        pr = pyproj.Proj(proj="utm", ellps="WGS84")
        PROJECTIONS[name] = pr

    pr = PROJECTIONS[name]
    return pr(lon, lat)


# ============= EOF =============================================
