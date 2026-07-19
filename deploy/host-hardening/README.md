# Flow2API host hardening notes (personal captcha + DNS)

These are the operational companion settings used with the code changes on this branch.

## Code changes

- `src/services/flow_client.py`
  - Map modern Chrome UA majors to `chrome146` TLS impersonate under `curl_cffi` 0.15.0
  - Prefer `chrome146` fallback instead of legacy `chrome` / `chrome124`
  - Re-enable legacy `:uploadUserImage` fallback after project-scoped `/flow/uploadImage` retries fail
- `src/services/browser_captcha_personal.py`
  - Force personal-browser UA major to `146.0.0.0` so it matches the TLS profile
- `requirements.txt`
  - `curl-cffi==0.15.0`

## Host-only systemd / DNS (not applied by app code)

### `/etc/systemd/system/flow2api.service.d/local-browser.conf`

`
[Service]
Environment=BROWSER_EXECUTABLE_PATH=/var/lib/flow2api/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome
Environment=PERSONAL_BROWSER_DISABLE_SANDBOX=true
Environment=PERSONAL_BROWSER_FRESH_RESTART_EVERY_N_SOLVES=3
Environment=PERSONAL_BROWSER_LAUNCH_PARALLELISM=1
Environment=PERSONAL_MAX_RESIDENT_TABS=2
`

### `/etc/systemd/system/flow2api.service.d/99-dns-reliable.conf`

`
[Service]
Environment=CURL_IPRESOLVE=4
Environment=NODE_OPTIONS=--dns-result-order=ipv4first
`

### `/etc/systemd/resolved.conf.d/99-flow2api-dns.conf`

`
[Resolve]
DNS=1.1.1.1 8.8.8.8 1.0.0.1 8.8.4.4
FallbackDNS=9.9.9.9 149.112.112.112
Domains=~.
DNSSEC=no
DNSOverTLS=no
Cache=yes
DNSStubListener=yes
ReadEtcHosts=yes
`

### `/etc/netplan/99-flow2api-dns.yaml`

`
network:
  version: 2
  ethernets:
    eth0:
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8, 1.0.0.1, 8.8.4.4]
      dhcp4-overrides:
        use-dns: false
      dhcp6-overrides:
        use-dns: false
`

## Notes

- Do not commit host secrets, API keys, cookies, or `INITIAL_ADMIN_CREDENTIALS.txt`
- `PUBLIC_ERROR_AUDIO_FILTERED` is a content filter, not a captcha failure; retry may succeed
- Companion package with apply/verify scripts: `teracoot/flow-captcha-relay`
