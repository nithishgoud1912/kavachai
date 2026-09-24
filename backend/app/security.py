"""Local authentication, RBAC, TOTP and audit primitives for KavachAI.

This module intentionally uses only Python standard-library cryptography so the
air-gapped deployment does not need a package download for authentication.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time
from enum import StrEnum
from typing import Iterable


class Role(StrEnum):
    ADMIN = "admin"
    WORKBENCH_USER = "ai_workbench_user"
    KNOWLEDGE_BASE_MANAGER = "knowledge_base_manager"
    REVIEWER_APPROVER = "reviewer_approver"
    AUDITOR = "auditor"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "users:manage", "roles:manage", "workspace:manage", "models:manage",
        "sandbox:manage", "configuration:manage", "audit:manage", "audit:read",
    },
    Role.WORKBENCH_USER: {
        "workspace:read", "chat:write", "investigation:write", "document:upload",
        "document:read", "knowledge_base:query", "model:use", "agent:invoke",
        "sandbox:request", "deliverable:create", "deliverable:read", "audit:read_own",
    },
    Role.KNOWLEDGE_BASE_MANAGER: {
        "workspace:read", "document:read", "document:upload", "knowledge_base:query",
        "knowledge_base:manage", "document:classify", "document:retire", "audit:read_own",
    },
    Role.REVIEWER_APPROVER: {
        "workspace:read", "document:read", "deliverable:read", "deliverable:approve",
        "classification:downgrade", "audit:read_approval",
    },
    Role.AUDITOR: {"audit:read", "policy:read", "configuration:read"},
}

CLASSIFICATION_RANK = {
    "public_demo": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
    "defence_sensitive": 4,
}


def normalise_role(role: str) -> Role:
    try:
        return Role(role)
    except ValueError as exc:
        raise ValueError(f"Unknown role: {role}") from exc


def permissions_for_roles(roles: Iterable[str]) -> set[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(normalise_role(role), set()))
    return permissions


def has_permission(roles: Iterable[str], permission: str) -> bool:
    return permission in permissions_for_roles(roles)


def can_access_classification(clearance: str, classification: str) -> bool:
    return CLASSIFICATION_RANK.get(clearance, -1) >= CLASSIFICATION_RANK.get(classification, 999)


def hash_password(password: str) -> str:
    """Hash a password using scrypt with a unique, random salt."""
    if len(password) < 14:
        raise ValueError("Password must be at least 14 characters long")
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**15, r=8, p=1, dklen=32,
        # OpenSSL's conservative default is smaller than the ~32 MiB this
        # approved work factor needs on some Windows builds.
        maxmem=64 * 1024 * 1024,
    )
    return "scrypt$32768$8$1${}${}".format(
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, encoded_salt, encoded_hash = encoded.split("$")
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(encoded_hash.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected),
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def generate_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def verify_totp(secret: str, code: str, *, period: int = 30, window: int = 1) -> bool:
    """Verify RFC 6238 TOTP locally, allowing one adjacent time step."""
    if not code.isdigit() or len(code) != 6:
        return False
    padded_secret = secret.upper() + "=" * ((8 - len(secret) % 8) % 8)
    try:
        key = base64.b32decode(padded_secret, casefold=True)
    except (ValueError, TypeError):
        return False
    counter = int(time.time() // period)
    for candidate in range(counter - window, counter + window + 1):
        digest = hmac.new(key, struct.pack(">Q", candidate), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
        if hmac.compare_digest(f"{value:06d}", code):
            return True
    return False


def generate_totp(secret: str, *, period: int = 30) -> str:
    """Generate the current RFC 6238 6-digit TOTP code for a base32 secret."""
    padded_secret = secret.upper() + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    counter = int(time.time() // period)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"
