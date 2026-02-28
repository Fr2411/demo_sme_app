from services.dashboard_service import load_api_dashboard_context


def test_load_api_dashboard_context_tracks_dashboard_endpoints(monkeypatch):
    payload_by_path = {
        "/api/v1/reports/profit-loss": {"profit": "10.00"},
        "/api/v1/returns": [{"id": 1}],
        "/api/v1/reports/stock-aging": {"rows": [{"sku": "SKU-1"}]},
        "/api/v1/inventory/movements": [],
        "/api/v1/sessions/logs": [{"id": 2}],
        "/api/v1/orders": [{"id": 3}],
    }

    def fake_request(path, params=None):
        return payload_by_path.get(path)

    monkeypatch.setattr("services.dashboard_service._request_json", fake_request)

    context = load_api_dashboard_context()

    assert len(context["endpoint_statuses"]) == 6
    assert all(status["connected"] for status in context["endpoint_statuses"])
    assert context["api_connected"] is True
    assert context["stock_aging_rows"] == [{"sku": "SKU-1"}]
