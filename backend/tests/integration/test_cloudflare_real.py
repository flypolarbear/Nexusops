"""
MK-010 Cloudflare DNS Real Integration Tests

Tests real Cloudflare API connectivity and DNS operations.
"""

import pytest
import requests
import uuid
import time


CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"


@pytest.mark.integration
@pytest.mark.cloudflare
class TestCloudflareConnection:
    """Test Cloudflare API connectivity"""

    def test_verify_token(self, cloudflare_config):
        """Test Cloudflare API token verification"""
        url = f"{CLOUDFLARE_API_BASE}/user/tokens/verify"
        headers = {
            "Authorization": f"Bearer {cloudflare_config['api_token']}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        assert response.status_code == 200, f"Token verification failed: {response.text}"
        data = response.json()
        assert data.get("success") is True, f"Token verification failed: {data}"

    def test_get_zone_info(self, cloudflare_config):
        """Test getting zone information"""
        zone_id = cloudflare_config["zone_id"]
        url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}"
        headers = {
            "Authorization": f"Bearer {cloudflare_config['api_token']}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        assert response.status_code == 200, f"Get zone info failed: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert "result" in data
        assert "name" in data["result"]


@pytest.mark.integration
@pytest.mark.cloudflare
class TestCloudflareDNSRecords:
    """Test Cloudflare DNS record operations"""

    def test_list_dns_records(self, cloudflare_config):
        """Test listing DNS records"""
        zone_id = cloudflare_config["zone_id"]
        url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records"
        headers = {
            "Authorization": f"Bearer {cloudflare_config['api_token']}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        assert response.status_code == 200, f"List DNS records failed: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert "result" in data

    def test_create_and_delete_txt_record(self, cloudflare_config):
        """Test creating and deleting a TXT record (safe operation)"""
        zone_id = cloudflare_config["zone_id"]
        headers = {
            "Authorization": f"Bearer {cloudflare_config['api_token']}",
            "Content-Type": "application/json",
        }

        # Create a unique TXT record for testing
        test_id = str(uuid.uuid4())[:8]
        record_name = f"_test-{test_id}"
        record_content = f"nexusops-integration-test-{test_id}"

        # Create TXT record
        create_url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records"
        create_data = {
            "type": "TXT",
            "name": record_name,
            "content": record_content,
            "ttl": 120,
            "comment": "NexusOps integration test - will be deleted",
        }

        create_response = requests.post(
            create_url, headers=headers, json=create_data, timeout=30
        )

        assert (
            create_response.status_code == 200
        ), f"Create TXT record failed: {create_response.text}"
        create_result = create_response.json()
        assert create_result.get("success") is True

        record_id = create_result["result"]["id"]
        print(f"Created test TXT record: {record_name} (ID: {record_id})")

        # Wait a moment for propagation
        time.sleep(2)

        # Delete the record
        delete_url = (
            f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records/{record_id}"
        )
        delete_response = requests.delete(delete_url, headers=headers, timeout=30)

        assert (
            delete_response.status_code == 200
        ), f"Delete TXT record failed: {delete_response.text}"
        delete_result = delete_response.json()
        assert delete_result.get("success") is True

        print(f"Deleted test TXT record: {record_name}")

    def test_list_record_types(self, cloudflare_config):
        """Test listing different DNS record types"""
        zone_id = cloudflare_config["zone_id"]
        headers = {
            "Authorization": f"Bearer {cloudflare_config['api_token']}",
            "Content-Type": "application/json",
        }

        # Test listing A records
        url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records?type=A"
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        a_records = response.json()
        print(f"A records: {len(a_records.get('result', []))}")

        # Test listing CNAME records
        url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/dns_records?type=CNAME"
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        cname_records = response.json()
        print(f"CNAME records: {len(cname_records.get('result', []))}")


@pytest.mark.integration
@pytest.mark.cloudflare
class TestCloudflareZoneAnalytics:
    """Test Cloudflare zone analytics"""

    def test_get_zone_analytics(self, cloudflare_config):
        """Test getting zone analytics summary"""
        zone_id = cloudflare_config["zone_id"]
        url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/analytics/dashboard"
        headers = {
            "Authorization": f"Bearer {cloudflare_config['api_token']}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        # Analytics might require higher permissions, so we just check connection
        if response.status_code == 200:
            data = response.json()
            print(f"Analytics available: {data.get('success')}")
        else:
            print(f"Analytics not available (status: {response.status_code})")
            # Don't fail - this is optional
