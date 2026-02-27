from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.product import Product
from backend.app.models.product_image import ProductImage
from backend.app.schemas.product import (
    ProductCreate,
    ProductImageMatchRead,
    ProductImageRead,
    ProductRead,
    ProductUpdate,
)
from backend.app.services.image_embeddings import OpenAIImageEmbeddingService
from backend.app.services.image_matching import ImageMatchingService
from backend.app.services.image_storage import S3ImageStorageService

router = APIRouter(prefix='/products', tags=['products'])


@router.get('', response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.post('', response_model=ProductRead)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.query(Product).filter(Product.sku == payload.sku).first():
        raise HTTPException(status_code=409, detail='SKU already exists')
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get('/{product_id}', response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return product


@router.patch('/{product_id}', response_model=ProductRead)
def patch_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete('/{product_id}', status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    db.delete(product)
    db.commit()
    return None


@router.post('/{product_id}/images', response_model=ProductImageRead)
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='Uploaded file must be an image')

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail='Image is empty')

    storage_service = S3ImageStorageService()
    embedding_service = OpenAIImageEmbeddingService()

    upload_result = storage_service.upload_product_image(
        product_id=product_id,
        file_name=image.filename or 'upload.bin',
        payload=image_bytes,
        content_type=image.content_type,
    )
    embedding = embedding_service.create_embedding(image_bytes=image_bytes, content_type=image.content_type)

    product_image = ProductImage(
        product_id=product_id,
        file_name=image.filename or 'upload.bin',
        content_type=image.content_type,
        s3_bucket=upload_result.bucket,
        s3_key=upload_result.key,
        s3_url=upload_result.url,
        embedding=embedding,
    )
    db.add(product_image)
    db.commit()
    db.refresh(product_image)
    return product_image


@router.post('/image-search', response_model=list[ProductImageMatchRead])
async def search_products_by_image(
    screenshot: UploadFile = File(...),
    top_k: int = Form(default=5),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if top_k < 1 or top_k > 20:
        raise HTTPException(status_code=400, detail='top_k must be between 1 and 20')
    if not screenshot.content_type or not screenshot.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='Screenshot must be an image')

    screenshot_bytes = await screenshot.read()
    if not screenshot_bytes:
        raise HTTPException(status_code=400, detail='Screenshot is empty')

    embedding_service = OpenAIImageEmbeddingService()
    matcher = ImageMatchingService()

    query_embedding = embedding_service.create_embedding(
        image_bytes=screenshot_bytes,
        content_type=screenshot.content_type,
    )
    return matcher.find_top_matches(db=db, query_embedding=query_embedding, top_k=top_k)
