"""
Tests for the Mergington High School Activities API endpoints.
"""

import pytest
import json
from fastapi import status


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Tests for the activities endpoint."""
    
    def test_get_activities_success(self, client):
        """Test successful retrieval of all activities."""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) >= 3  # At least the 3 test activities
        
        # Check that required fields are present
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_get_activities_contains_expected_data(self, client):
        """Test that activities endpoint contains expected test data."""
        response = client.get("/activities")
        activities = response.json()
        
        # Check for specific test activities
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        
        # Verify Chess Club data
        chess_club = activities["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for the activity signup endpoint."""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity in result["message"]
        
        # Verify the participant was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for a non-existent activity."""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]
    
    def test_signup_duplicate_registration(self, client):
        """Test that duplicate registrations are prevented."""
        email = "michael@mergington.edu"  # Already registered in Chess Club
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"]
    
    def test_signup_activity_name_with_spaces(self, client):
        """Test signup with activity names containing spaces."""
        email = "newstudent@mergington.edu"
        activity = "Programming Class"
        
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_200_OK
        
        # Verify registration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_special_characters_in_email(self, client):
        """Test signup with special characters in email."""
        email = "test.student+tag@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_200_OK
        
        # Verify registration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]


class TestUnregisterEndpoint:
    """Tests for the activity unregister endpoint."""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"  # Pre-registered in Chess Club
        activity = "Chess Club"
        
        # Verify user is initially registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity in result["message"]
        
        # Verify the participant was actually removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistration from a non-existent activity."""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]
    
    def test_unregister_not_registered(self, client):
        """Test unregistration when student is not registered."""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        result = response.json()
        assert "detail" in result
        assert "not registered" in result["detail"]
    
    def test_unregister_activity_name_with_spaces(self, client):
        """Test unregistration with activity names containing spaces."""
        email = "emma@mergington.edu"  # Pre-registered in Programming Class
        activity = "Programming Class"
        
        response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify unregistration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests covering multiple operations."""
    
    def test_full_registration_cycle(self, client):
        """Test complete registration and unregistration cycle."""
        email = "integration.test@mergington.edu"
        activity = "Chess Club"
        
        # Initial state - user not registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        initial_count = len(activities[activity]["participants"])
        assert email not in activities[activity]["participants"]
        
        # Register user
        signup_response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify registration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count + 1
        
        # Unregister user
        # Unregister user
        unregister_response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert unregister_response.status_code == status.HTTP_200_OK        # Verify unregistration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count
        
        # Try to unregister again (should fail)
        unregister_again_response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert unregister_again_response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_multiple_activities_registration(self, client):
        """Test registering for multiple activities."""
        email = "multi.activity@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Register for multiple activities
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup", json={"email": email})
            assert response.status_code == status.HTTP_200_OK
        
        # Verify all registrations
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]
        
        # Unregister from one activity
        response = client.request(
            "DELETE",
            f"/activities/Chess Club/unregister", 
            json={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify partial unregistration
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        assert email not in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]
        assert email in activities_data["Gym Class"]["participants"]


class TestURLEncoding:
    """Tests for proper URL encoding handling."""
    
    def test_activity_name_url_encoding(self, client):
        """Test that activity names with spaces are properly handled in URLs."""
        email = "url.test@mergington.edu"
        activity = "Programming Class"  # Contains space
        
        # Test signup with URL encoding
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_200_OK
        
        # Test unregister with URL encoding
        response = client.request(
            "DELETE",
            f"/activities/{activity}/unregister", 
            json={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_email_url_encoding(self, client):
        """Test that emails with special characters are properly handled."""
        email = "test+tag@mergington.edu"  # Contains + character
        activity = "Chess Club"
        
        # Test signup
        response = client.post(f"/activities/{activity}/signup", json={"email": email})
        assert response.status_code == status.HTTP_200_OK
        
        # Verify registration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]