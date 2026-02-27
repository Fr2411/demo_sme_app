from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Easy Ecom API'
    api_v1_prefix: str = '/api/v1'
    secret_key: str = 'change_me'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60
    order_edit_2fa_code: str = '123456'

    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/easy_ecom'
    whatsapp_verify_token: str = 'change_me_verify_token'
    whatsapp_app_secret: str = ''
    whatsapp_access_token: str = ''
    whatsapp_phone_number_id: str = ''
    whatsapp_api_version: str = 'v20.0'


settings = Settings()
