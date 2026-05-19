from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from .config import get_settings


def issue(username: str, groups: tuple[str, ...]) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "iss": s.jwt_issuer,
        "aud": s.jwt_audience,
        "sub": username,
        "groups": list(groups),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=s.jwt_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def verify(token: str) -> dict | None:
    s = get_settings()
    try:
        return jwt.decode(
            token,
            s.jwt_secret,
            algorithms=[s.jwt_algorithm],
            audience=s.jwt_audience,
            issuer=s.jwt_issuer,
        )
    except JWTError:
        return None
