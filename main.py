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
import json

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from fastapi_pagination import add_pagination

from sqlalchemy.orm import Session

import models
from app import app

from crud import (
    read_waterlevels_manual_query,
    public_release_filter,
    _read_pods,
    read_waterlevels_pressure_query,
)

import plotly
import plotly.graph_objects as go

from dependencies import get_db
from routers import locations, wells, waterlevels, ngwmn
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


# ===============================================================================
# views
@app.get("/location/view/{pointid}", response_class=HTMLResponse)
def location_view(request: Request, pointid: str, db: Session = Depends(get_db)):
    q = db.query(models.Location.__table__)
    q = q.filter(models.Location.PointID == pointid)
    q = public_release_filter(q)
    loc = q.first()
    wells = _read_pods(pointid, db)

    well = None
    pods = []
    if wells:
        well = wells[0]
        pods = well.pods

    fig = go.Figure()
    manual_waterlevels = read_waterlevels_manual_query(pointid, db).all()
    mxs = [w.DateMeasured for w in manual_waterlevels]
    mys = [w.DepthToWaterBGS for w in manual_waterlevels]

    fig.add_trace(go.Scatter(x=mxs, y=mys, mode="markers", name="Manual Water Levels"))

    pressure_waterlevels = read_waterlevels_pressure_query(
        pointid, db, as_dict=True
    ).all()
    pxs = [w.DateMeasured for w in pressure_waterlevels]
    pys = [w.DepthToWaterBGS for w in pressure_waterlevels]
    fig.add_trace(
        go.Scatter(x=pxs, y=pys, mode="lines", name="Continuous Water Levels")
    )

    fig.update_layout(
        xaxis={"title": "Date Measured"},
        yaxis={"title": "Depth to Water BGS (ft)", "autorange": "reversed"},
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return templates.TemplateResponse(
        "location_view.html",
        {
            "request": request,
            "location": loc._mapping if loc else {},
            "well": well,
            "pods": pods,
            "graphJSON": graphJSON,
        },
    )


# end views
# ===============================================================================


# ===============================================================================
# routes
app.include_router(locations.router)
app.include_router(wells.router)
app.include_router(waterlevels.router)
app.include_router(ngwmn.router)
add_pagination(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

# ============= EOF =============================================
