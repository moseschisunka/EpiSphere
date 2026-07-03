from app.core.privacy import hash_identifier, mask_identifier, normalize_identifier


def test_hash_identifier_is_stable_and_normalized(monkeypatch):
    first = hash_identifier(" mrn-001 ")
    second = hash_identifier("MRN-001")

    assert first == second
    assert first != "MRN-001"


def test_mask_identifier_hides_prefix():
    assert mask_identifier("PATIENT-12345") == "***2345"
    assert mask_identifier("123") == "***"
    assert mask_identifier(None) is None


def test_normalize_identifier_handles_blank_values():
    assert normalize_identifier("  abc   123 ") == "ABC 123"
    assert normalize_identifier("   ") is None
