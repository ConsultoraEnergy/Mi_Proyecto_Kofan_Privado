"""Almacenamiento en object storage (Fase 3) contra un S3 simulado en memoria (moto)."""

from typing import Any

import boto3
import pytest
from bson import ObjectId
from moto import mock_aws
from pydantic import SecretStr

from backend.app.core.settings import Settings, get_settings
from backend.app.modules.media import storage
from backend.tests.conftest import future, make_png, web_booking

BUCKET = "kawari-test"
CDN = "https://kawari-test.nyc3.cdn.digitaloceanspaces.com"
ALL_USERS = "http://acs.amazonaws.com/groups/global/AllUsers"


@pytest.fixture
def s3(monkeypatch):
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        settings = get_settings()
        for name, value in {
            "storage_backend": "s3",
            "s3_bucket": BUCKET,
            "s3_endpoint_url": None,
            "s3_region": "us-east-1",
            "s3_access_key_id": SecretStr("test"),
            "s3_secret_access_key": SecretStr("test"),
            "s3_key_prefix": "kawari",
            "s3_public_base_url": CDN,
        }.items():
            monkeypatch.setattr(settings, name, value)
        storage.reset_backend_cache()
        yield client
    storage.reset_backend_cache()


def _keys(client, prefix: str) -> list[str]:
    return [o["Key"] for o in client.list_objects_v2(Bucket=BUCKET, Prefix=prefix).get("Contents", [])]


def _is_public(client, key: str) -> bool:
    grants = client.get_object_acl(Bucket=BUCKET, Key=key)["Grants"]
    return any(g["Grantee"].get("URI") == ALL_USERS and g["Permission"] == "READ" for g in grants)


async def test_fotos_publicas_en_bucket_con_miniatura(api, admin_headers, room, s3, storage_dirs):
    response = await api.post(
        f"/rooms/{room['_id']}/images",
        headers=admin_headers,
        files=[("files", ("a.png", make_png((1600, 900)), "image/png"))],
    )
    assert response.status_code == 200, response.text
    url = response.json()["images"][0]
    assert url.startswith(f"{CDN}/kawari/public/") and url.endswith(".png")

    name = url.rsplit("/", 1)[-1]
    key, thumb_key = f"kawari/public/{name}", f"kawari/public/thumbs/{name[:-4]}.webp"
    assert sorted(_keys(s3, "kawari/")) == sorted([key, thumb_key])
    assert _is_public(s3, key) and _is_public(s3, thumb_key)

    head = s3.head_object(Bucket=BUCKET, Key=key)
    assert head["ContentType"] == "image/png" and "immutable" in head["CacheControl"]
    thumb = s3.head_object(Bucket=BUCKET, Key=thumb_key)
    assert thumb["ContentType"] == "image/webp" and thumb["ContentLength"] < head["ContentLength"]
    assert list(storage_dirs["public"].iterdir()) == []  # nada en disco

    removed = await api.delete(f"/rooms/{room['_id']}/images", params={"url": url}, headers=admin_headers)
    assert removed.status_code == 200
    assert _keys(s3, "kawari/") == []


async def test_comprobante_privado_en_bucket(api, admin_headers, db, room, s3, storage_dirs):
    booking = (await web_booking(api, room, future(2), future(3))).json()
    receipt_key = (await db.bookings.find_one({"_id": ObjectId(booking["id"])}))["receipt"]["key"]

    assert _keys(s3, "kawari/receipts/") == [f"kawari/receipts/{receipt_key}"]
    assert _keys(s3, "kawari/public/") == []
    assert not _is_public(s3, f"kawari/receipts/{receipt_key}")
    assert list(storage_dirs["private"].iterdir()) == []

    download = await api.get(booking["receipt_url"], headers=admin_headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "image/png"
    assert download.headers["cache-control"] == "private, no-store"
    assert download.content.startswith(b"\x89PNG")

    sin_permiso = await api.get(booking["receipt_url"])
    assert sin_permiso.status_code == 401


async def test_bucket_caido_responde_503(api, admin_headers, room, s3):
    s3.delete_bucket(Bucket=BUCKET)
    response = await api.post(
        f"/rooms/{room['_id']}/images",
        headers=admin_headers,
        files=[("files", ("a.png", make_png(), "image/png"))],
    )
    assert response.status_code == 503
    assert "almacenamiento" in response.json()["detail"]


async def test_url_ajena_no_borra_nada(s3):
    s3.put_object(Bucket=BUCKET, Key="otro-proyecto/foto.png", Body=b"x")
    assert await storage.delete_public_file("https://evil.example.com/kawari/public/" + "a" * 32 + ".png") is False
    assert await storage.delete_public_file(f"{CDN}/kawari/public/../../otro-proyecto/foto.png") is False
    assert _keys(s3, "otro-proyecto/") == ["otro-proyecto/foto.png"]


# --- Configuración ---


def _settings(**env: Any) -> Settings:
    values: dict[str, Any] = {"mongo_uri": "mongodb://x", "secret_key": "k" * 40, **env}
    return Settings(_env_file=None, **values)


def test_acepta_variables_de_digitalocean(monkeypatch):
    for name, value in {
        "STORAGE_BACKEND": "s3",
        "DO_AWS_ACCESS_KEY_ID": "id",
        "DO_AWS_SECRET_ACCESS_KEY": "secret",
        "DO_AWS_REGION": "nyc3",
        "DO_AWS_BUCKET_NAME": "kawari",
        # El "Origin Endpoint" que muestra DigitalOcean incluye el nombre del bucket
        "DO_S3_ENDPOINT_URL": "https://kawari.nyc3.digitaloceanspaces.com/",
    }.items():
        monkeypatch.setenv(name, value)
    settings = _settings()
    assert settings.s3_bucket == "kawari" and settings.s3_region == "nyc3"
    assert settings.s3_client_endpoint == "https://nyc3.digitaloceanspaces.com"
    assert settings.s3_public_base == "https://kawari.nyc3.digitaloceanspaces.com"


def test_s3_sin_credenciales_no_arranca(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "kawari")
    with pytest.raises(ValueError, match="S3_ACCESS_KEY_ID"):
        _settings(storage_backend="s3")
