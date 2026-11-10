from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(deepcopy(original_state))


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities_returns_available_activities(client: TestClient):
    # Arrange
    endpoint = "/activities"

    # Act
    response = client.get(endpoint)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "Programming Class" in payload


def test_signup_for_activity_succeeds(client: TestClient):
    # Arrange
    email = "new.student@mergington.edu"
    endpoint = f"/activities/Chess%20Club/signup?email={email}"

    # Act
    response = client.post(endpoint)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client: TestClient):
    # Arrange
    endpoint = "/activities/Unknown%20Activity/signup?email=student@mergington.edu"

    # Act
    response = client.post(endpoint)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_duplicate_error_for_existing_participant(client: TestClient):
    # Arrange
    endpoint = "/activities/Chess%20Club/signup?email=michael@mergington.edu"

    # Act
    response = client.post(endpoint)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_error_when_activity_is_full(client: TestClient):
    # Arrange
    activities["Chess Club"]["participants"] = [
        f"student{i}@mergington.edu" for i in range(activities["Chess Club"]["max_participants"])
    ]
    endpoint = "/activities/Chess%20Club/signup?email=another.student@mergington.edu"

    # Act
    response = client.post(endpoint)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_normalizes_email_and_rejects_case_insensitive_duplicates(client: TestClient):
    # Arrange
    first_signup_endpoint = "/activities/Basketball%20Team/signup?email=%20New.Student%40mergington.edu%20"
    duplicate_signup_endpoint = "/activities/Basketball%20Team/signup?email=NEW.STUDENT%40mergington.edu"

    # Act
    response = client.post(first_signup_endpoint)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new.student@mergington.edu for Basketball Team"}
    assert "new.student@mergington.edu" in activities["Basketball Team"]["participants"]

    # Act
    duplicate = client.post(duplicate_signup_endpoint)

    # Assert
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Student already signed up for this activity"
