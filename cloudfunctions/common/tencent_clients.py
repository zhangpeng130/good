import base64
import json
from typing import Iterable, Optional

import requests

from .config import settings


def _ensure_credentials():
    if not settings.tencent_secret_id or not settings.tencent_secret_key:
        raise RuntimeError("TencentCloud credentials are not configured")


def send_sms_code(phone: str, code: str) -> dict:
    _ensure_credentials()
    if not settings.sms_sdk_app_id or not settings.sms_template_id:
        raise RuntimeError("SMS config is incomplete")

    from tencentcloud.common import credential
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
        TencentCloudSDKException,
    )
    from tencentcloud.sms.v20210111 import models, sms_client

    cred = credential.Credential(settings.tencent_secret_id, settings.tencent_secret_key)
    client = sms_client.SmsClient(cred, settings.tencent_region)
    req = models.SendSmsRequest()
    req.SmsSdkAppId = settings.sms_sdk_app_id
    req.SignName = settings.sms_sign_name
    req.TemplateId = settings.sms_template_id
    req.TemplateParamSet = [code]
    req.PhoneNumberSet = [f"+86{phone}"]

    try:
        resp = client.SendSms(req)
        payload = json.loads(resp.to_json_string())
        status_set = payload.get("SendStatusSet", [])
        if not status_set or status_set[0].get("Code") != "Ok":
            raise RuntimeError(f"SMS send failed: {payload}")
        return payload
    except TencentCloudSDKException as exc:
        raise RuntimeError(f"SMS send failed: {exc}") from exc


def synthesize_code_audio(code: str) -> Optional[str]:
    if not settings.dashscope_api_key:
        return None

    text = f"您好，您的验证码是：{' '.join(code)}。请在五分钟内使用。"
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.dashscope_tts_model,
        "voice": settings.dashscope_tts_voice,
        "input": text,
        "response_format": "wav",
    }
    resp = requests.post(
        settings.dashscope_tts_endpoint, headers=headers, json=payload, timeout=20
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"CosyVoice TTS failed: {resp.text}")
    return base64.b64encode(resp.content).decode("utf-8")


def upload_audio_to_cos(content: bytes, key: str, content_type: str = "audio/wav") -> str:
    _ensure_credentials()
    if not settings.cos_bucket:
        raise RuntimeError("COS bucket is not configured")

    from qcloud_cos import CosConfig, CosS3Client

    config = CosConfig(
        Region=settings.cos_region,
        SecretId=settings.tencent_secret_id,
        SecretKey=settings.tencent_secret_key,
        Scheme="https",
    )
    client = CosS3Client(config)
    client.put_object(
        Bucket=settings.cos_bucket,
        Body=content,
        Key=key,
        ContentType=content_type,
        EnableMD5=False,
    )

    if settings.cos_base_url:
        return f"{settings.cos_base_url.rstrip('/')}/{key}"
    return f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com/{key}"


def send_voice_message(phone: str, message: str) -> None:
    if not settings.voice_message_webhook:
        # Keep function callable in dev; in prod use TencentCloud VoiceMessage API endpoint.
        print(f"[voice-message-skip] phone={phone} message={message}")
        return

    payload = {"phone": phone, "message": message}
    resp = requests.post(settings.voice_message_webhook, json=payload, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"voice message webhook failed: {resp.text}")


def send_wechat_subscription(openids: Iterable[str], title: str, content: str) -> None:
    targets = [item for item in openids if item]
    if not targets:
        return
    if not settings.wechat_notify_webhook:
        print(f"[wechat-notify-skip] targets={len(targets)} title={title} content={content}")
        return

    payload = {"openids": targets, "title": title, "content": content}
    resp = requests.post(settings.wechat_notify_webhook, json=payload, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"wechat notify webhook failed: {resp.text}")

