import unittest
from collections import deque
from unittest.mock import patch

from permission_protocol.client import PermissionProtocolClient
from permission_protocol.exceptions import APIError, PermissionDenied, PermissionTimeout
from permission_protocol.models import Config, Receipt


class DummyClient(PermissionProtocolClient):
    def __init__(self):
        super().__init__(Config(api_key="pp_live_test", base_url="https://app.permissionprotocol.com"))


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.client = DummyClient()

    def tearDown(self):
        self.client.close()

    def test_authorize_wait_false_builds_pending_receipt(self):
        def fake_request(method, path, **kwargs):
            self.assertEqual(method, "POST")
            self.assertEqual(path, "/api/v1/receipts/verify")
            return {
                "valid": False,
                "requestId": "pp_r_123",
                "approvalUrl": "https://permissionprotocol.com/r/123",
            }

        self.client._request = fake_request

        receipt = self.client.authorize(action="deploy", resource="billing", wait=False)

        self.assertEqual(receipt.id, "pp_r_123")
        self.assertEqual(receipt.status, "PENDING")
        self.assertTrue(receipt.url.endswith("/123"))

    def test_authorize_wait_true_polls_until_approved(self):
        sequence = deque(
            [
                Receipt(id="pp_r_1", status="PENDING", action="deploy", resource="svc", actor="bot"),
                Receipt(id="pp_r_1", status="APPROVED", action="deploy", resource="svc", actor="bot"),
            ]
        )

        self.client._request = lambda method, path, **kwargs: {
            "requestId": "pp_r_1",
            "approvalUrl": "https://permissionprotocol.com/r/1",
        }
        self.client.get_receipt = lambda _: sequence.popleft()

        with patch("permission_protocol.client.time.sleep", lambda _: None):
            receipt = self.client.authorize(action="deploy", resource="svc", wait=True, timeout=10)

        self.assertEqual(receipt.status, "APPROVED")

    def test_authorize_denied_raises(self):
        self.client._request = lambda method, path, **kwargs: {
            "requestId": "pp_r_2",
            "approvalUrl": "https://permissionprotocol.com/r/2",
        }
        self.client.get_receipt = lambda _: Receipt(
            id="pp_r_2", status="DENIED", action="deploy", resource="svc", actor="bot"
        )

        with self.assertRaises(PermissionDenied):
            self.client.authorize(action="deploy", resource="svc", wait=True, timeout=5)

    def test_authorize_timeout_raises(self):
        self.client._request = lambda method, path, **kwargs: {
            "requestId": "pp_r_3",
            "approvalUrl": "https://permissionprotocol.com/r/3",
        }
        self.client.get_receipt = lambda _: Receipt(
            id="pp_r_3", status="PENDING", action="deploy", resource="svc", actor="bot"
        )

        time_values = iter([0.0, 0.0, 5.1, 5.1])
        with patch("permission_protocol.client.time.monotonic", lambda: next(time_values)):
            with patch("permission_protocol.client.time.sleep", lambda _: None):
                with self.assertRaises(PermissionTimeout):
                    self.client.authorize(action="deploy", resource="svc", wait=True, timeout=5)

    def test_verify_uses_get_and_verification(self):
        self.client.get_receipt = lambda receipt_id: Receipt(
            id=receipt_id,
            status="APPROVED",
            action="deploy",
            resource="svc",
            actor="bot",
            valid=False,
        )

        def fake_request(method, path, **kwargs):
            self.assertEqual(method, "POST")
            self.assertEqual(path, "/api/v1/receipts/verify")
            return {"valid": True}

        self.client._request = fake_request

        receipt = self.client.verify(receipt_id="pp_r_4")
        self.assertTrue(receipt.valid)

    def test_verify_fails_closed_when_verification_request_fails(self):
        self.client.get_receipt = lambda receipt_id: Receipt(
            id=receipt_id,
            status="APPROVED",
            action="deploy",
            resource="svc",
            actor="bot",
            valid=True,
        )

        def fake_request(method, path, **kwargs):
            raise APIError("verification service unavailable")

        self.client._request = fake_request

        with self.assertRaises(APIError):
            self.client.verify(receipt_id="pp_r_5")

    def test_verify_does_not_trust_fetched_receipt_valid_flag(self):
        self.client.get_receipt = lambda receipt_id: Receipt(
            id=receipt_id,
            status="APPROVED",
            action="deploy",
            resource="svc",
            actor="bot",
            valid=True,
        )

        def fake_request(method, path, **kwargs):
            self.assertEqual(method, "POST")
            self.assertEqual(path, "/api/v1/receipts/verify")
            return {}

        self.client._request = fake_request

        receipt = self.client.verify(receipt_id="pp_r_6")
        self.assertFalse(receipt.valid)


if __name__ == "__main__":
    unittest.main()
