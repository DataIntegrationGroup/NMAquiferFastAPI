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
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="NMAquiferAPI",
    description="""This is a REST API for the New Mexico Aquifer Mapping Programs database. 
    It provides access water levels and water chemistry data for groundwater and surface water in New Mexico.""",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Stacy Timmons",
        "url": "http://geoinfo.nmt.edu",
        "email": "stacy.timmons@nmt.edu",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


app.mount("/static", StaticFiles(directory="static"), name="static")


# from graphql_app import graphql_app
# app.add_route("/graphql", graphql_app)
# app.add_websocket_route("/graphql", graphql_app)

# ============= EOF =============================================
