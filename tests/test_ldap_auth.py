"""Tests for LDAP authentication helper."""

from typing import Dict

from ldap3.core.exceptions import LDAPException

from gens.blueprints.login.views import authenticate_with_ldap
from gens.config import LdapConfig


def test_authenticate_with_ldap_builds_bind_dn(monkeypatch):
    calls: Dict[str, str] = {}

    class DummyServer:
        def __init__(self, url: str):
            calls["server"] = url

    class DummyConnection:
        def __init__(self, server: DummyServer, user: str, password: str, auto_bind: bool):
            calls["user"] = user
            calls["password"] = password

        def __enter__(self) -> "DummyConnection":
            self.bound = True
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            return None

    monkeypatch.setattr("gens.blueprints.login.views.Server", DummyServer)
    monkeypatch.setattr("gens.blueprints.login.views.Connection", DummyConnection)

    ldap_config = LdapConfig(
        server="ldap://ldap.example.com",
        bind_user_template="uid={username},ou=People,dc=example,dc=com",
    )

    assert authenticate_with_ldap("alice", "hunter2", ldap_config) is True
    assert calls["user"] == "uid=alice,ou=People,dc=example,dc=com"
    assert calls["server"] == "ldap://ldap.example.com"


def test_authenticate_with_ldap_handles_ldap_exception(monkeypatch):
    class DummyServer:
        def __init__(self, url: str):
            self.url = url

    class CustomLDAPException(LDAPException):
        pass

    class FailingConnection:
        def __init__(self, *args, **kwargs):
            raise CustomLDAPException("bind failed")

    monkeypatch.setattr("gens.blueprints.login.views.Server", DummyServer)
    monkeypatch.setattr("gens.blueprints.login.views.Connection", FailingConnection)

    ldap_config = LdapConfig(server="ldap://ldap.example.com")

    assert authenticate_with_ldap("alice", "hunter2", ldap_config) is False
