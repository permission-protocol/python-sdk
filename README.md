# Permission Protocol Python SDK

`permission-protocol` is the official Python SDK for requesting and verifying Permission Protocol authority receipts.

## Installation

```bash
pip install permission-protocol
```

## Quickstart

```python
import permission_protocol as pp

pp.configure(api_key="pp_live_xxx", base_url="https://app.permissionprotocol.com")

receipt = pp.authorize(
    action="deploy",
    resource="billing-service",
    actor="deploy-bot",
    metadata={"pr": 42},
    wait=True,
    timeout=300,
)

print(receipt.id)
print(receipt.status)
print(receipt.json())
```

You can also skip `configure()` by setting `PP_API_KEY` (and optionally `PP_BASE_URL`) in the environment.

## Decorator

```python
from permission_protocol import require_approval

@require_approval(resource="billing-service")
def deploy_service():
    return "deploy complete"
```

When `deploy_service()` is called, the SDK creates an approval request, prints an approval URL, and blocks until approved or timed out.

## Verify

```python
import permission_protocol as pp

receipt = pp.verify(receipt_id="pp_r_8f91c2")
assert receipt.valid
```

## Exceptions

The SDK raises these exceptions:

- `PermissionProtocolError`
- `PermissionDenied`
- `PermissionTimeout`
- `AuthenticationError`
- `APIError`

## Development

```bash
pip install -e .[dev]
pytest
python3 -c "import permission_protocol; print(permission_protocol.__version__)"
```

## License

MIT
