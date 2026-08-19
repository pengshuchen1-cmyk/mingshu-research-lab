from app.errors import APIError, ErrorDefinition, Errors


def _definitions() -> list[ErrorDefinition]:
    return [value for value in vars(Errors).values() if isinstance(value, ErrorDefinition)]


def test_error_catalog_codes_are_unique_and_complete():
    definitions = _definitions()

    assert definitions
    assert len({item.code for item in definitions}) == len(definitions)
    assert all(item.code and item.message for item in definitions)
    assert all(400 <= item.status_code < 600 for item in definitions)


def test_api_error_preserves_existing_fastapi_detail_contract():
    error = APIError(Errors.PACKAGE_NAME_ALREADY_EXISTS)

    assert error.status_code == 409
    assert error.detail == "Package name already exists"
    assert error.error_code == "PACKAGE_NAME_ALREADY_EXISTS"
