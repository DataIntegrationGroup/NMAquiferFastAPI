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
import json

from starlette.responses import StreamingResponse


def json_response(filename, content):
    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    if isinstance(content, dict):
        content = json.dumps(content)

    response = StreamingResponse(
        [
            content,
        ],
        media_type="application/json",
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def csv_response(filename, content):
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"

    response = StreamingResponse(
        [
            content,
        ],
        media_type="text/csv",
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# ============= EOF =============================================
