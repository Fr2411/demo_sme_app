import uuid

from services.client_service import CLIENT_COLUMNS, add_client, get_all_clients, update_client


def _build_client_payload(client_id: str, name: str) -> dict:
    payload = {col: "" for col in CLIENT_COLUMNS}
    payload.update(
        {
            "client_id": client_id,
            "client_name": name,
            "business_overview": "Retail",
            "opening_hours": "08:00",
            "closing_hours": "20:00",
            "max_discount_pct": "11.5",
            "return_refund_policy": "7 days",
            "sales_commission_pct": "2.5",
            "whatsapp_enabled": "true",
            "messenger_enabled": "true",
            "instagram_enabled": "false",
            "meta_business_manager_id": "meta-1",
        }
    )
    return payload


def test_update_client_persists_all_fields():
    client_id = f"test_client_{uuid.uuid4().hex[:8]}"
    add_payload = _build_client_payload(client_id, "Original Name")
    ok, _ = add_client(add_payload)
    assert ok is True

    update_payload = _build_client_payload(client_id, "Updated Name")
    update_payload["business_overview"] = "Updated overview"
    update_payload["return_refund_policy"] = "14 days"
    update_payload["meta_business_manager_id"] = "meta-updated"

    update_ok, message = update_client(client_id, update_payload)
    assert update_ok is True
    assert message == "Client updated successfully"

    clients = get_all_clients()
    updated = clients[clients["client_id"] == client_id].iloc[0]
    assert updated["client_name"] == "Updated Name"
    assert updated["business_overview"] == "Updated overview"
    assert updated["return_refund_policy"] == "14 days"
    assert updated["meta_business_manager_id"] == "meta-updated"


def test_update_client_requires_existing_client_and_name():
    missing_ok, missing_message = update_client("not_real", {"client_name": "X"})
    assert missing_ok is False
    assert missing_message == "Client ID not found"

    client_id = f"test_client_{uuid.uuid4().hex[:8]}"
    ok, _ = add_client(_build_client_payload(client_id, "Needs Name"))
    assert ok is True

    no_name_ok, no_name_message = update_client(client_id, {"client_name": ""})
    assert no_name_ok is False
    assert no_name_message == "Client Name is required"
