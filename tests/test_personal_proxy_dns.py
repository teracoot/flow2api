"""Browser proxy metadata must not switch HTTP traffic to local DNS."""
import types
import unittest
from unittest.mock import AsyncMock, patch

from src.services.browser_captcha_personal import (
    BrowserCaptchaService,
    _compose_proxy_url,
    _parse_proxy_url,
)
from src.services.flow_client import FlowClient


class PersonalProxyDnsTests(unittest.IsolatedAsyncioTestCase):
    def test_chrome_and_curl_use_equivalent_remote_dns(self):
        parts = _parse_proxy_url("socks5h://127.0.0.1:10808")
        self.assertEqual(parts[:3], ("socks5", "127.0.0.1", "10808"))
        self.assertEqual(_compose_proxy_url(*parts), "socks5h://127.0.0.1:10808")

    def test_http_and_auth_are_preserved(self):
        self.assertEqual(_compose_proxy_url("http", "proxy.test", "8080", "user", "pass"),
                         "http://user:pass@proxy.test:8080")
        self.assertEqual(_compose_proxy_url("socks5", "proxy.test", "1080", "user", "pass"),
                         "socks5h://user:pass@proxy.test:1080")
        self.assertIsNone(_compose_proxy_url(None, None, None))

    async def test_recaptcha_asset_download_preserves_remote_dns(self):
        service = BrowserCaptchaService.__new__(BrowserCaptchaService)
        service._resolve_personal_proxy = AsyncMock(return_value=_parse_proxy_url("socks5h://127.0.0.1:10808"))
        self.assertEqual(await service._resolve_personal_proxy_download_url(), "socks5h://127.0.0.1:10808")

    async def test_fingerprint_override_passes_socks5h_to_curl(self):
        service = BrowserCaptchaService.__new__(BrowserCaptchaService)
        service._proxy_url = _compose_proxy_url(*_parse_proxy_url("socks5h://127.0.0.1:10808"))
        service._tab_evaluate = AsyncMock(return_value={"user_agent": "Mozilla/5.0 Chrome/124.0.0.0"})
        fingerprint = await service._extract_tab_fingerprint(object())
        self.assertEqual(fingerprint["proxy_url"], "socks5h://127.0.0.1:10808")
        manager = types.SimpleNamespace(get_request_proxy_url=AsyncMock(return_value="socks5h://127.0.0.1:10808"))
        client = FlowClient(manager)
        client._set_request_fingerprint(fingerprint)
        response = types.SimpleNamespace(status_code=200, json=lambda: {"ok": True})
        fake_session = AsyncMock()
        fake_session.__aenter__.return_value = fake_session
        fake_session.get.return_value = response
        with patch("src.services.flow_client.AsyncSession", return_value=fake_session):
            await client._make_request("GET", "https://aisandbox-pa.googleapis.com/v1/credits",
                                       allow_urllib_fallback=False)
        self.assertEqual(fake_session.get.call_args.kwargs["proxy"], "socks5h://127.0.0.1:10808")


if __name__ == "__main__":
    unittest.main()
