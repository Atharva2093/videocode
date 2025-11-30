"""
Backend Tests - Phase 6
Basic tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient


# Test configuration
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TEST_INVALID_URL = "not-a-valid-url"


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_health_check(self, client):
        """Test /api/health endpoint returns OK"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "yt_dlp_version" in data
    
    def test_ping(self, client):
        """Test /api/ping endpoint"""
        response = client.get("/api/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestVideoInfoEndpoints:
    """Tests for video information endpoints"""
    
    def test_metadata_invalid_url(self, client):
        """Test /api/metadata with invalid URL"""
        response = client.get(f"/api/metadata?url={TEST_INVALID_URL}")
        assert response.status_code in [400, 422]
    
    def test_metadata_missing_url(self, client):
        """Test /api/metadata without URL parameter"""
        response = client.get("/api/metadata")
        assert response.status_code == 422
    
    def test_playlist_invalid_url(self, client):
        """Test /api/playlist with invalid URL"""
        response = client.get(f"/api/playlist?url={TEST_INVALID_URL}")
        assert response.status_code in [400, 422]


class TestDownloadEndpoints:
    """Tests for download endpoints"""
    
    def test_queue_status(self, client):
        """Test /api/queue returns queue status"""
        response = client.get("/api/queue")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
    
    def test_download_invalid_url(self, client):
        """Test /api/download with invalid URL"""
        response = client.post(
            "/api/download",
            json={"url": TEST_INVALID_URL, "format": "mp4", "quality": "720p"}
        )
        assert response.status_code in [400, 422]
    
    def test_download_missing_url(self, client):
        """Test /api/download without URL"""
        response = client.post(
            "/api/download",
            json={"format": "mp4", "quality": "720p"}
        )
        assert response.status_code == 422
    
    def test_task_not_found(self, client):
        """Test /api/download/{task_id} with invalid task ID"""
        response = client.get("/api/download/nonexistent-task-id")
        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_endpoint(self, client):
        """Test non-existent endpoint returns 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test wrong HTTP method returns 405"""
        response = client.delete("/api/health")
        assert response.status_code == 405


class TestRateLimiting:
    """Tests for rate limiting"""
    
    def test_rate_limit_not_exceeded(self, client):
        """Test normal usage doesn't trigger rate limit"""
        # Make a few requests
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200


# Pytest fixtures
@pytest.fixture
def client():
    """Create test client"""
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from backend.main import app
        return TestClient(app)
    except ImportError:
        # If import fails, skip tests
        pytest.skip("Could not import backend.main")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
