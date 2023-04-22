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
from typing import List

from fastapi import APIRouter

from schemas import waterchemistry

router = APIRouter(prefix="/waterchem", tags=["waterchem"])


@router.get("/{pointid}/{analyte}", response_model=List[waterchemistry.Analyte])
async def read_analyte(pointid: str, analyte: str):
    pass


# ============= EOF =============================================
