from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.example'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_name: str = 'Easy Ecom API'
    api_v1_prefix: str = '/api/v1'
    secret_key: str = 'change_me'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60
    order_edit_2fa_code: str = '123456'
    cors_origins: str = 'http://localhost,http://localhost:80'

    database_url: str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/easy_ecom'
    whatsapp_verify_token: str = 'change_me_verify_token'
    whatsapp_app_secret: str = ''
    whatsapp_access_token: str = ''
    whatsapp_phone_number_id: str = ''
    whatsapp_api_version: str = 'v20.0'

    openai_api_key: str = ''
    openai_embedding_model: str = 'text-embedding-3-small'

    s3_region: str = 'us-east-1'
    s3_access_key_id: str = ''
    s3_secret_access_key: str = ''
    s3_bucket_name: str = ''
    s3_product_image_prefix: str = 'product-images'


settings = Settings()
