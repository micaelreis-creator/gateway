"""
Canva Connect API Client
========================
Reverse-engineered from the Canva Connect API (https://www.canva.com/developers/).

Covers:
  - OAuth 2.0 client_credentials token acquisition & auto-refresh
  - GET  /rest/v1/design-templates   – list / search design templates
  - POST /rest/v1/designs            – create a new design
  - GET  /rest/v1/designs/{id}       – fetch design metadata
  - GET  /rest/v1/designs            – list user's designs

Authentication
--------------
Canva uses OAuth 2.0 (client_credentials or authorization_code).
To get credentials: https://www.canva.com/developers/ → Apps → create an app
  CLIENT_ID     e.g. "OXabc123..."
  CLIENT_SECRET e.g. "7f3a..."

Replace CLIENT_ID and CLIENT_SECRET below, then run:
  python api_client.py
"""

import time
import requests
from typing import Optional

# ---------------------------------------------------------------------------
# Credentials – replace with your own from https://www.canva.com/developers/
# ---------------------------------------------------------------------------
CLIENT_ID     = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"

# If you already have a bearer token from the browser/OAuth flow, paste it here:
BEARER_TOKEN: Optional[str] = None  # e.g. "eyJhbGciOi..."

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL   = "https://api.canva.com/rest/v1"
TOKEN_URL  = "https://api.canva.com/rest/v1/oauth/token"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------
_token_cache: dict = {}


def get_access_token(client_id: str = CLIENT_ID,
                     client_secret: str = CLIENT_SECRET) -> str:
    """
    Obtain (or return cached) an OAuth 2.0 access token using client_credentials.
    Re-fetches automatically when the token is about to expire.
    """
    # Honour a manually supplied bearer token
    if BEARER_TOKEN:
        return BEARER_TOKEN

    now = time.time()
    if _token_cache.get("access_token") and _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["access_token"]

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type":    "client_credentials",
            "client_id":     client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"]   = now + payload.get("expires_in", 3600)
    return _token_cache["access_token"]


def _session() -> requests.Session:
    """Return a requests.Session pre-loaded with auth headers."""
    s = requests.Session()
    s.headers.update(HEADERS)
    s.headers["Authorization"] = f"Bearer {get_access_token()}"
    return s


def _authed_get(path: str, params: Optional[dict] = None) -> dict:
    """GET with automatic 401 token refresh."""
    s = _session()
    url = f"{BASE_URL}{path}"
    resp = s.get(url, params=params, timeout=30)
    if resp.status_code in (401, 403):
        _token_cache.clear()          # force re-auth
        s.headers["Authorization"] = f"Bearer {get_access_token()}"
        resp = s.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _authed_post(path: str, json_body: dict) -> dict:
    """POST with automatic 401 token refresh."""
    s = _session()
    url = f"{BASE_URL}{path}"
    resp = s.post(url, json=json_body, timeout=30)
    if resp.status_code in (401, 403):
        _token_cache.clear()
        s.headers["Authorization"] = f"Bearer {get_access_token()}"
        resp = s.post(url, json=json_body, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# 1. Design Templates
# ---------------------------------------------------------------------------
def get_design_templates(
    *,
    query: Optional[str] = None,
    design_type: Optional[str] = None,
    locale: str = "en",
    continuation: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    GET /rest/v1/design-templates
    List or search Canva design templates.

    Args:
        query:       Free-text search term (e.g. "birthday", "presentation").
        design_type: Filter by Canva design type slug
                     (e.g. "presentation", "social_media", "poster").
        locale:      BCP-47 locale code (default "en").
        continuation: Pagination cursor from a previous response.
        limit:       Max results per page (1-50, default 20).

    Returns:
        JSON dict with keys:
          items        – list of template objects
          continuation – cursor for the next page (may be absent)
    """
    params: dict = {"locale": locale, "limit": limit}
    if query:
        params["query"] = query
    if design_type:
        params["design_type"] = design_type
    if continuation:
        params["continuation"] = continuation
    return _authed_get("/design-templates", params=params)


# ---------------------------------------------------------------------------
# 2. Create a Design
# ---------------------------------------------------------------------------
def create_design(
    *,
    design_type: Optional[str] = None,
    title: Optional[str] = None,
    width_px: Optional[int] = None,
    height_px: Optional[int] = None,
    asset_id: Optional[str] = None,
    template_id: Optional[str] = None,
) -> dict:
    """
    POST /rest/v1/designs
    Create a new Canva design.

    Supply either a preset design_type OR explicit width_px/height_px.
    Optionally seed from a template (template_id) or an uploaded asset (asset_id).

    Args:
        design_type: Canva preset (e.g. "presentation", "instagram_post").
        title:       Human-readable title for the design.
        width_px:    Custom width in pixels (use with height_px).
        height_px:   Custom height in pixels.
        asset_id:    Canva asset ID to seed the design from.
        template_id: Template ID to base the new design on.

    Returns:
        JSON dict with the new design object (id, title, urls, …).
    """
    body: dict = {}

    if design_type:
        body["design_type"] = {"type": "preset", "name": design_type}
    elif width_px and height_px:
        body["design_type"] = {
            "type": "custom",
            "width":  width_px,
            "height": height_px,
        }
    else:
        raise ValueError("Provide either design_type or both width_px and height_px.")

    if title:
        body["title"] = title
    if asset_id:
        body["asset_id"] = asset_id
    if template_id:
        body["template_id"] = template_id

    return _authed_post("/designs", json_body=body)


# ---------------------------------------------------------------------------
# 3. Fetch Design Metadata
# ---------------------------------------------------------------------------
def get_design(design_id: str) -> dict:
    """
    GET /rest/v1/designs/{designId}
    Retrieve metadata for a specific design.

    Args:
        design_id: The Canva design ID (e.g. "DAFxxxxxx").

    Returns:
        JSON dict with:
          id, title, design_type, thumbnail, urls (view/edit/export), created_at, …
    """
    return _authed_get(f"/designs/{design_id}")


# ---------------------------------------------------------------------------
# 4. List User Designs
# ---------------------------------------------------------------------------
def list_designs(
    *,
    query: Optional[str] = None,
    continuation: Optional[str] = None,
    limit: int = 20,
    ownership: str = "owned",
) -> dict:
    """
    GET /rest/v1/designs
    List the authenticated user's designs.

    Args:
        query:        Optional search term.
        continuation: Pagination cursor from a previous response.
        limit:        Max results per page (1-50, default 20).
        ownership:    "owned" | "shared" | "any"  (default "owned").

    Returns:
        JSON dict with keys:
          items        – list of design summary objects
          continuation – cursor for the next page (may be absent)
    """
    params: dict = {"limit": limit, "ownership": ownership}
    if query:
        params["query"] = query
    if continuation:
        params["continuation"] = continuation
    return _authed_get("/designs", params=params)


# ---------------------------------------------------------------------------
# Main – demo
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== Canva Connect API Demo ===\n")

    # 1. Design templates
    print("[1] Fetching design templates (query='presentation') …")
    templates = get_design_templates(query="presentation", limit=5)
    items = templates.get("items", [])
    print(f"    Found {len(items)} template(s)")
    for t in items[:3]:
        tid  = t.get("id", "?")
        name = t.get("title", t.get("name", "untitled"))
        print(f"      • {tid}: {name}")

    # Grab a template ID for step 2 (if any)
    tpl_id = items[0]["id"] if items else None

    print()

    # 2. Create a new design
    print("[2] Creating a new presentation design …")
    new_design = create_design(
        design_type="presentation",
        title="My API-generated Presentation",
        **({"template_id": tpl_id} if tpl_id else {}),
    )
    design_id = new_design.get("design", {}).get("id") or new_design.get("id")
    print(f"    New design ID: {design_id}")
    print(f"    Edit URL:      {new_design.get('design', new_design).get('urls', {}).get('edit_url', 'N/A')}")

    print()

    # 3. Fetch design metadata
    if design_id:
        print(f"[3] Fetching metadata for design {design_id} …")
        meta = get_design(design_id)
        d = meta.get("design", meta)
        print(f"    Title:   {d.get('title', 'N/A')}")
        print(f"    Created: {d.get('created_at', 'N/A')}")
        print(f"    Type:    {d.get('design_type', {}).get('name', 'N/A')}")
    else:
        print("[3] Skipped – no design ID from step 2.")

    print()

    # 4. List user designs
    print("[4] Listing user's designs (first 5) …")
    my_designs = list_designs(limit=5)
    for d in my_designs.get("items", [])[:5]:
        print(f"      • {d.get('id')}: {d.get('title', 'untitled')}")

    print("\nDone.")


if __name__ == "__main__":
    main()
