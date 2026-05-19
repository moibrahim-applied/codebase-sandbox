"""Auth Service — issues JWTs for FreeWeigh.Net operators."""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from . import ldap_stub, tokens

app = FastAPI(
    title="MT Auth Service",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class VerifyRequest(BaseModel):
    token: str


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": "auth-service",
            "product": "FreeWeigh.Net",
            "version": __version__,
            "compliance": ["ALCOA+", "CFR-21-Part-11", "IEC-62443-4-1"],
        }
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/login")
def login(req: LoginRequest) -> dict:
    user = ldap_stub.lookup(req.username)
    if not user or not ldap_stub.verify_password(user, req.password):
        # Same response for missing-user vs wrong-password (no username enumeration).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )
    token = tokens.issue(user.username, user.groups)
    return {"token": token, "groups": list(user.groups), "display_name": user.display_name}


@app.post("/verify")
def verify(req: VerifyRequest) -> dict:
    claims = tokens.verify(req.token)
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    return {"valid": True, "claims": claims}
