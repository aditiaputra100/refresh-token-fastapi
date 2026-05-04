# Refresh Token FastAPI

Project ini dibuat untuk mempelajari bagaimana access token dan refresh token bekerja di FastAPI.

## Tech Stack

- FastAPI
- SQLAlchemy 2.x async
- SQLite sebagai database default
- Pydantic Settings
- PyJWT
- pwdlib dengan Argon2
- pytest
- httpx

## Fitur

- Register user
- Login user
- Refresh access token menggunakan refresh token
- Logout dan revoke refresh token
- Current user endpoint dengan access token di Authorization header
- Health check endpoint

## Struktur Endpoint

- `POST /register`
- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /users/me`
- `GET /health`

## Catatan Auth

- Access token dikirim di response body sebagai `access_token` dan dipakai client dengan header `Authorization: Bearer <token>`.
- Refresh token tetap disimpan di HttpOnly cookie.
- Endpoint `GET /users/me` membaca bearer token dari header, bukan cookie.

## Prasyarat

- Python 3.13+
- Virtual environment aktif

## Setup

1. Clone repository.
2. Install dependency menggunakan `uv`.

```bash
uv sync
```

## Konfigurasi Environment

1. Salin `.env.example` menjadi `.env`.
2. Isi `SECRET_KEY` dengan nilai acak yang panjang.
3. Sesuaikan konfigurasi database jika tidak memakai SQLite default.

Contoh:

```bash
cp .env.example .env
```

## Menjalankan Project

Jalankan server development dengan:

```bash
uv run uvicorn main:app --reload
```

Setelah server berjalan, buka:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## Menjalankan Test

Jalankan seluruh test dengan:

```bash
uv run pytest
```

Jalankan feature test saja dengan:

```bash
uv run pytest tests/features/
```

## Catatan

- Proyek ini fokus pada alur belajar refresh token, bukan production-ready auth.
- Jangan commit file `.env` yang berisi secret asli.
