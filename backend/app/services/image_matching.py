from sqlalchemy.orm import Session

from backend.app.models.product import Product
from backend.app.models.product_image import ProductImage


class ImageMatchingService:
    def find_top_matches(self, db: Session, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        distance = ProductImage.embedding.cosine_distance(query_embedding)
        rows = (
            db.query(
                Product.id.label('product_id'),
                Product.sku.label('sku'),
                Product.name.label('name'),
                Product.category.label('category'),
                ProductImage.s3_url.label('image_url'),
                distance.label('distance'),
            )
            .join(Product, Product.id == ProductImage.product_id)
            .order_by(distance.asc())
            .limit(top_k * 10)
            .all()
        )

        matches: list[dict] = []
        seen_products: set[int] = set()
        for row in rows:
            if row.product_id in seen_products:
                continue
            seen_products.add(row.product_id)
            matches.append(
                {
                    'product_id': row.product_id,
                    'sku': row.sku,
                    'name': row.name,
                    'category': row.category,
                    'image_url': row.image_url,
                    'similarity_score': max(0.0, 1 - float(row.distance)),
                }
            )
            if len(matches) >= top_k:
                break
        return matches
