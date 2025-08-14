import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger("olymps_service")


class HttpClient:
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: float = 10.0, max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "HEAD"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.headers: Dict[str, str] = {"User-Agent": "TeamSearchBot/1.0"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def post(self, path: str, json_body: Dict[str, Any]) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self.session.post(url, json=json_body, timeout=self.timeout, headers=self.headers)

    def head(self, url: str) -> requests.Response:
        return self.session.head(url, timeout=self.timeout, allow_redirects=True, headers=self.headers)

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        final_headers = dict(self.headers)
        if headers:
            final_headers.update(headers)
        return self.session.get(url, timeout=self.timeout, headers=final_headers)