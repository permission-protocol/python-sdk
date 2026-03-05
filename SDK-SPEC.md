# Permission Protocol Python SDK — Build Spec

## Goal
Build a Python SDK that lets developers add authority receipts to any AI agent with one line of code. Must be publishable to PyPI as `permission-protocol`.

## API Surface (public)

### Configuration
```python
import permission_protocol as pp
pp.configure(api_key="pp_live_xxx", base_url="https://app.permissionprotocol.com")
```

### Core: authorize()
```python
receipt = pp.authorize(
    action="deploy",
    resource="billing-service",
    actor="deploy-bot",        # optional, defaults to hostname
    metadata={"pr": 42},       # optional
    wait=True,                 # block until approved (default True)
    timeout=300,               # seconds to wait for approval (default 300)
)

# receipt.id -> "pp_r_8f91c2"
# receipt.status -> "APPROVED"
# receipt.approved_by -> "sarah.kim"
# receipt.signature -> "pp_sig_..."
# receipt.url -> "https://permissionprotocol.com/r/8f91c2"
# receipt.json() -> dict
```

### Core: @require_approval decorator
```python
from permission_protocol import require_approval

@require_approval(resource="billing-service")
def deploy_service():
    deploy("billing-api")

# When deploy_service() is called:
# 1. Creates authorization request via PP API
# 2. Prints approval link to stdout
# 3. Polls until approved or timeout
# 4. On approval: executes the function, returns result
# 5. On rejection/timeout: raises PermissionDenied
```

### Verify
```python
receipt = pp.verify(receipt_id="pp_r_8f91c2")
assert receipt.valid  # True if signature checks out
```

### Receipt object
```python
class Receipt:
    id: str
    status: str  # APPROVED, DENIED, PENDING, EXPIRED
    action: str
    resource: str
    actor: str
    approved_by: Optional[str]
    policy: Optional[str]
    signature: Optional[str]
    issuer: str
    timestamp: datetime
    expires_at: Optional[datetime]
    url: str
    valid: bool
    
    def json(self) -> dict: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
```

### Exceptions
```python
class PermissionProtocolError(Exception): ...
class PermissionDenied(PermissionProtocolError): ...
class PermissionTimeout(PermissionProtocolError): ...
class AuthenticationError(PermissionProtocolError): ...
class APIError(PermissionProtocolError): ...
```

## Backend API Endpoints Used

Based on the existing PP API (app.permissionprotocol.com):

### POST /api/v1/receipts/verify
- Used for: Creating authorization requests + verifying receipts
- Auth: `X-PP-API-Key` header
- Body: `{ scope: { action, resource, actor, ... }, failOnMissing: true }`
- Returns: `{ valid, requestId, approvalUrl, receipt }`

### GET /api/v1/receipts/:id
- Used for: Fetching receipt details
- Auth: `X-PP-API-Key` header

### POST /api/v1/approvals (if exists)
- Used for: Creating standalone approval requests
- We may need to add this endpoint if it doesn't exist for the SDK flow

## Package Structure
```
permission_protocol/
├── __init__.py          # Public API: configure, authorize, verify, require_approval
├── client.py            # HTTP client, auth, retries
├── models.py            # Receipt, Config dataclasses
├── exceptions.py        # Custom exceptions
├── decorator.py         # @require_approval implementation
├── _version.py          # __version__
└── py.typed             # PEP 561 marker

pyproject.toml           # Build config (setuptools/hatch)
README.md                # PyPI readme
LICENSE                  # MIT
tests/
├── test_client.py
├── test_decorator.py
└── test_models.py
```

## Dependencies
- `httpx` — async-capable HTTP client (better than requests for polling)
- `typing_extensions` — for older Python compat
- Python >= 3.9

## PyPI Publishing
- Package name: `permission-protocol`
- Import name: `permission_protocol`
- Version: `0.1.0`
- License: MIT

## Key Design Decisions
1. **Sync-first, async-ready** — Main API is synchronous (blocking). Async wrappers come in v0.2.
2. **Polling with backoff** — `authorize(wait=True)` polls every 2s with exponential backoff up to 10s
3. **Pretty stdout** — When waiting for approval, print the approval URL prominently (developers will see this in their terminal)
4. **Zero config possible** — `PP_API_KEY` env var works without calling configure()
5. **Thread-safe** — Global config is module-level but uses threading.Lock
6. **No secrets in logs** — API key never printed/logged

## What to Build
Build ALL of the above. The SDK must be fully functional against the real PP API. Include a working pyproject.toml ready for `pip install -e .` and PyPI publishing.

After building:
1. Run any included tests
2. Verify `python -c "import permission_protocol; print(permission_protocol.__version__)"` works
3. Commit everything
