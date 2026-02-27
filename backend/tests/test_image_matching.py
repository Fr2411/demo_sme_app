from types import SimpleNamespace

from backend.app.services.image_matching import ImageMatchingService


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def join(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    def query(self, *_args, **_kwargs):
        return FakeQuery(self.rows)


def test_find_top_matches_returns_unique_products():
    rows = [
        SimpleNamespace(product_id=1, sku='SKU1', name='Prod1', category='Cat', image_url='u1', distance=0.1),
        SimpleNamespace(product_id=1, sku='SKU1', name='Prod1', category='Cat', image_url='u2', distance=0.2),
        SimpleNamespace(product_id=2, sku='SKU2', name='Prod2', category='Cat', image_url='u3', distance=0.3),
    ]
    service = ImageMatchingService()
    result = service.find_top_matches(FakeSession(rows), [0.0] * 1536, top_k=2)

    assert len(result) == 2
    assert result[0]['product_id'] == 1
    assert result[1]['product_id'] == 2
