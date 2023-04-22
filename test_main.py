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
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_read_locations():
    response = client.get("/locations")
    assert response.status_code == 200


def test_read_location_pointid():
    response = client.get("/location/pointid/MG-030")
    assert response.status_code == 200


def test_read_location_view():
    response = client.get("/location/view/MG-030")
    assert response.status_code == 200


def test_well():
    response = client.get("/well")
    assert response.status_code == 200


def test_read_pod():
    response = client.get("/pod")
    assert response.status_code == 200


def test_read_waterlevels_manual():
    response = client.get("/waterlevels/manual")
    assert response.status_code == 200


def test_read_waterlevels_pressure():
    response = client.get("/waterlevels/pressure")
    assert response.status_code == 200


def test_read_waterlevels_acoustic():
    response = client.get("/waterlevels/acoustic")
    assert response.status_code == 200


# ============= EOF =============================================
