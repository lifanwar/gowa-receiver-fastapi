# GOWA Webhook FastAPI - Redis Pub/Sub Version

Alur:

1. FastAPI menerima webhook GOWA.
2. Signature diverifikasi.
3. Payload JSON diparse.
4. Payload dinormalisasi.
5. `device_id` dibersihkan menjadi safe key.
6. Jika `ALLOWED_DEVICES` diisi, device dicek whitelist.
7. Event dipublish ke Redis Pub/Sub channel:

```text
wa:incoming:{device_id}
```

Tidak ada Redis Stream, tidak ada queue, tidak ada dedup. Jika worker tidak subscribe, event akan lewat begitu saja.

## File yang berubah

- `main.py`
- `redis_pubsub.py` baru, menggantikan `redis_stream.py`
- `settings.py`

`normalizer.py` tetap sama.

## Contoh subscribe manual Redis CLI

```bash
redis-cli SUBSCRIBE wa:incoming:DEVICE_ID_KAMU
```

## Contoh publish flow

Jika `device_id` dari payload adalah `device_1`, maka FastAPI publish ke:

```text
wa:incoming:device_1
```

Response `subscribers` menunjukkan jumlah subscriber aktif pada saat publish.
Jika `subscribers` bernilai `0`, itu bukan error dalam desain Pub/Sub fire-and-forget.
