from app import tokens


def test_round_trip():
    t = tokens.issue("op-42", ("freeweigh.operator",))
    claims = tokens.verify(t)
    assert claims is not None
    assert claims["sub"] == "op-42"
    assert claims["groups"] == ["freeweigh.operator"]


def test_tampered_token_rejected():
    t = tokens.issue("op-42", ("freeweigh.operator",))
    bad = t[:-2] + ("aa" if not t.endswith("aa") else "bb")
    assert tokens.verify(bad) is None
