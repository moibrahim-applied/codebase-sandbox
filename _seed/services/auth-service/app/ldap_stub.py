"""LDAP directory stub.

The real implementation binds to the corporate AD at `ldap.mt.internal`
and runs a sub-tree search under `OU=FreeWeigh,DC=mt,DC=internal`. The
sandbox version embeds a small hard-coded fixture so the service is
runnable offline.
"""

from dataclasses import dataclass
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class DirectoryUser:
    username: str
    display_name: str
    groups: tuple[str, ...]
    password_hash: str


# Fixture seeded with the same hashes you'd see in `ldapsearch -L` output.
# Passwords are "operator" / "supervisor" / "qa" respectively.
_FIXTURE: dict[str, DirectoryUser] = {
    "op-42": DirectoryUser(
        username="op-42",
        display_name="Operator 42",
        groups=("freeweigh.operator",),
        password_hash=_pwd.hash("operator"),
    ),
    "sup-7": DirectoryUser(
        username="sup-7",
        display_name="Supervisor 7",
        groups=("freeweigh.operator", "freeweigh.supervisor"),
        password_hash=_pwd.hash("supervisor"),
    ),
    "qa-1": DirectoryUser(
        username="qa-1",
        display_name="QA Reviewer 1",
        groups=("freeweigh.qa",),
        password_hash=_pwd.hash("qa"),
    ),
}


def lookup(username: str) -> DirectoryUser | None:
    return _FIXTURE.get(username)


def verify_password(user: DirectoryUser, plaintext: str) -> bool:
    return _pwd.verify(plaintext, user.password_hash)
