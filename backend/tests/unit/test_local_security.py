"""Regression tests for the local-authentication security primitives."""

from app.security import (
    Role, can_access_classification, generate_totp_secret, has_permission,
    hash_password, verify_password,
)


def test_scrypt_password_hash_verifies_only_the_original_password():
    encoded = hash_password("Sovereign-Workbench-2026!")
    assert encoded.startswith("scrypt$")
    assert verify_password("Sovereign-Workbench-2026!", encoded)
    assert not verify_password("Sovereign-Workbench-2027!", encoded)


def test_password_policy_rejects_short_passwords():
    try:
        hash_password("too-short")
    except ValueError as error:
        assert "14" in str(error)
    else:
        raise AssertionError("short passwords must be rejected")


def test_five_role_permissions_are_least_privilege():
    assert has_permission([Role.WORKBENCH_USER.value], "agent:invoke")
    assert not has_permission([Role.WORKBENCH_USER.value], "users:manage")
    assert has_permission([Role.AUDITOR.value], "audit:read")
    assert not has_permission([Role.AUDITOR.value], "document:upload")


def test_classification_is_ordered_and_default_deny_for_unknown_values():
    assert can_access_classification("restricted", "confidential")
    assert not can_access_classification("internal", "restricted")
    assert not can_access_classification("internal", "unknown")


def test_generated_totp_secret_is_base32_shaped():
    secret = generate_totp_secret()
    assert len(secret) >= 32
    assert secret.isalnum()
