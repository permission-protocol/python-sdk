import unittest

import permission_protocol as pp


class DecoratorTests(unittest.TestCase):
    def test_require_approval_calls_authorize_and_executes(self):
        captured = {}

        def fake_authorize(**kwargs):
            captured.update(kwargs)

        original = pp.authorize
        pp.authorize = fake_authorize
        try:
            @pp.require_approval(resource="billing-service")
            def deploy_service():
                return "done"

            result = deploy_service()
        finally:
            pp.authorize = original

        self.assertEqual(result, "done")
        self.assertEqual(captured["resource"], "billing-service")
        self.assertEqual(captured["action"], "deploy_service")
        self.assertTrue(captured["wait"])


if __name__ == "__main__":
    unittest.main()
