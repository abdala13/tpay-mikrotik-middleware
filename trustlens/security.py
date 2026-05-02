import ipaddress
import socket
from urllib.parse import urlparse, urljoin

BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}

def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise ValueError("URL is required.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are allowed.")
    if not parsed.netloc:
        raise ValueError("Invalid URL host.")
    return url

def _is_private_ip(ip: str) -> bool:
    obj = ipaddress.ip_address(ip)
    return obj.is_private or obj.is_loopback or obj.is_link_local or obj.is_multicast or obj.is_reserved or obj.is_unspecified

def validate_public_url(url: str) -> str:
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = parsed.hostname or ""
    host_l = host.lower().strip("[]")
    if host_l in BLOCKED_HOSTS or host_l.endswith(".local"):
        raise ValueError("Local/internal hosts are not allowed.")
    try:
        if _is_private_ip(host_l):
            raise ValueError("Private/internal IP addresses are not allowed.")
    except ValueError as ip_err:
        if "not allowed" in str(ip_err):
            raise
    try:
        results = socket.getaddrinfo(host_l, None)
        for family, _, _, _, sockaddr in results:
            ip = sockaddr[0]
            if _is_private_ip(ip):
                raise ValueError("This host resolves to a private/internal IP and cannot be scanned.")
    except socket.gaierror:
        raise ValueError("Could not resolve this domain.")
    return normalized

def safe_join(base, href):
    if not href:
        return None
    joined = urljoin(base, href)
    parsed = urlparse(joined)
    if parsed.scheme not in {"http", "https"}:
        return None
    return joined
