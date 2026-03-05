import unittest
from datetime import datetime, timezone

from permission_protocol.models import Receipt


class ReceiptModelTests(unittest.TestCase):
    def test_receipt_from_dict_and_json_roundtrip(self):
        payload = {
            "id": "pp_r_8f91c2",
            "status": "APPROVED",
            "action": "deploy",
            "resource": "billing-service",
            "actor": "deploy-bot",
            "approvedBy": "sarah.kim",
            "policy": "prod-deploy",
            "signature": "pp_sig_123",
            "issuer": "permission-protocol",
            "timestamp": "2026-03-05T12:00:00Z",
            "expiresAt": "2026-03-05T13:00:00Z",
            "url": "https://permissionprotocol.com/r/8f91c2",
            "valid": True,
        }

        receipt = Receipt.from_dict(payload)

        self.assertEqual(receipt.id, "pp_r_8f91c2")
        self.assertEqual(receipt.approved_by, "sarah.kim")
        self.assertEqual(receipt.timestamp, datetime(2026, 3, 5, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(receipt.expires_at, datetime(2026, 3, 5, 13, 0, 0, tzinfo=timezone.utc))
        self.assertTrue(receipt.json()["valid"])

    def test_receipt_str_and_repr(self):
        receipt = Receipt(
            id="pp_r_test",
            status="PENDING",
            action="deploy",
            resource="billing-service",
            actor="bot",
        )
        self.assertIn("pp_r_test", str(receipt))
        self.assertIn("Receipt(", repr(receipt))


if __name__ == "__main__":
    unittest.main()
