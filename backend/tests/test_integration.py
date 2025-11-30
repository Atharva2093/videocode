"""
Backend Integration Tests - Phase 11
Tests for all API endpoints including new search and subtitle functionality
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_health_check(self):
        """Test /api/health returns healthy status"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "yt_dlp_version" in data
    
    def test_ping(self):
        """Test /api/ping returns pong"""
        response = client.get("/api/ping")
        assert response.status_code == 200
        assert response.json()["ping"] == "pong"
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "YouTube Video Downloader API" in data["message"]
        assert data["version"] == "2.0.0"


class TestSearchEndpoints:
    """Tests for YouTube search endpoints"""
    
    @patch('backend.routes.search.yt_dlp.YoutubeDL')
    def test_search_youtube(self, mock_ydl):
        """Test /api/search endpoint"""
        # Mock yt-dlp response
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'entries': [
                {
                    'id': 'test123',
                    'title': 'Test Video',
                    'channel': 'Test Channel',
                    'duration': 300,
                    'view_count': 1000000,
                    'thumbnail': 'https://example.com/thumb.jpg'
                }
            ]
        }
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        response = client.get("/api/search?q=test%20video&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_empty_query(self):
        """Test search with empty query returns error"""
        response = client.get("/api/search?q=")
        # Empty query causes yt-dlp error or validation error
        assert response.status_code in [400, 422, 500]
    
    def test_search_limit_bounds(self):
        """Test search limit validation"""
        # Too high limit
        response = client.get("/api/search?q=test&limit=100")
        assert response.status_code == 422  # Validation error


class TestSubtitleEndpoints:
    """Tests for subtitle endpoints"""
    
    @patch('backend.routes.search.yt_dlp.YoutubeDL')
    def test_get_subtitles(self, mock_ydl):
        """Test /api/subtitles endpoint"""
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'id': 'test123',
            'title': 'Test Video',
            'subtitles': {
                'en': [{'ext': 'vtt'}],
                'es': [{'ext': 'vtt'}]
            },
            'automatic_captions': {
                'fr': [{'ext': 'vtt'}]
            }
        }
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        response = client.get("/api/subtitles?url=https://www.youtube.com/watch?v=test123")
        assert response.status_code == 200
        data = response.json()
        assert 'subtitles' in data
        assert data['has_subtitles'] == True


class TestMetadataEndpoints:
    """Tests for video metadata endpoints"""
    
    @patch('backend.routes.video_info.yt_dlp.YoutubeDL')
    def test_get_metadata(self, mock_ydl):
        """Test /api/metadata endpoint"""
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'id': 'test123',
            'title': 'Test Video',
            'description': 'Test description',
            'duration': 300,
            'channel': 'Test Channel',
            'view_count': 1000000,
            'thumbnail': 'https://example.com/thumb.jpg',
            'upload_date': '20231201',
            'formats': []
        }
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        response = client.get("/api/metadata?url=https://www.youtube.com/watch?v=test123")
        assert response.status_code == 200
        data = response.json()
        assert 'title' in data
    
    def test_metadata_invalid_url(self):
        """Test metadata with invalid URL"""
        response = client.get("/api/metadata?url=invalid-url")
        assert response.status_code in [400, 500]


class TestDownloadEndpoints:
    """Tests for download endpoints"""
    
    def test_queue_status(self):
        """Test /api/queue endpoint"""
        response = client.get("/api/queue")
        assert response.status_code == 200
        data = response.json()
        assert 'tasks' in data
        assert 'active_downloads' in data
        assert 'queued_downloads' in data
    
    def test_download_invalid_task(self):
        """Test getting invalid task status"""
        response = client.get("/api/download/nonexistent-task-id")
        assert response.status_code == 404


class TestCacheEndpoints:
    """Tests for cache management endpoints"""
    
    def test_cache_stats(self):
        """Test /api/cache/stats endpoint"""
        response = client.get("/api/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'entries' in data
        assert 'ttl_seconds' in data
    
    def test_cache_clear(self):
        """Test /api/cache/clear endpoint"""
        response = client.delete("/api/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True


class TestRateLimiting:
    """Tests for rate limiting middleware"""
    
    def test_rate_limit_headers(self):
        """Test that rate limiting works"""
        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.get("/api/health")
            responses.append(response)
        
        # All should succeed (under limit)
        for r in responses:
            assert r.status_code == 200


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """Test invalid HTTP method"""
        response = client.put("/api/health")
        assert response.status_code == 405


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
