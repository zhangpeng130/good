import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "good")
    jwt_secret: str = os.getenv("JWT_SECRET", "please-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_seconds: int = int(os.getenv("JWT_EXPIRE_SECONDS", "604800"))

    tencent_region: str = os.getenv("TENCENT_REGION", "ap-guangzhou")
    tencent_secret_id: str = os.getenv("TENCENT_SECRET_ID", "")
    tencent_secret_key: str = os.getenv("TENCENT_SECRET_KEY", "")

    sms_sdk_app_id: str = os.getenv("SMS_SDK_APP_ID", "")
    sms_sign_name: str = os.getenv("SMS_SIGN_NAME", "我很好")
    sms_template_id: str = os.getenv("SMS_TEMPLATE_ID", "")

    cos_region: str = os.getenv("COS_REGION", "ap-guangzhou")
    cos_bucket: str = os.getenv("COS_BUCKET", "")
    cos_base_url: str = os.getenv("COS_BASE_URL", "")

    db_host: str = os.getenv("DB_HOST", "")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "good")

    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_tts_endpoint: str = os.getenv(
        "DASHSCOPE_TTS_ENDPOINT",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/audio/speech",
    )
    dashscope_tts_model: str = os.getenv("DASHSCOPE_TTS_MODEL", "cosyvoice-v1")
    dashscope_tts_voice: str = os.getenv("DASHSCOPE_TTS_VOICE", "longxiaochun")

    wechat_notify_webhook: str = os.getenv("WECHAT_NOTIFY_WEBHOOK", "")
    voice_message_webhook: str = os.getenv("VOICE_MESSAGE_WEBHOOK", "")

    mock_external_services: bool = _get_bool("MOCK_EXTERNAL_SERVICES", default=False)
    debug: bool = _get_bool("DEBUG", default=False)


settings = Settings()

