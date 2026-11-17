# Stocks Dashboard

Dashboard de acciones y ETFs con datos públicos de Yahoo Finance (sin clave, sin realtime). Web pública de solo lectura + admin privado con Basic Auth.

> Nota: se descartó Stooq porque actualmente exige verificación JavaScript y ya no sirve CSV a un servidor. La capa de proveedor está aislada en `app/provider.py`.

## Cómo funciona

- Un único contenedor FastAPI sirve la web pública (`/`), el admin (`/admin`) y las APIs.
- Un bucle en el proceso consulta la API pública de Yahoo Finance cada hora y guarda cotizaciones e histórico en SQLite.
- El precio manual del admin (`override`) gana siempre sobre el precio de la API.
- La API pública **nunca** devuelve cantidades, precios de compra, importes ni P&L.
- Desplegado en `stocks.hugoperezvigo.es` (VPS 7, Apache + Cloudflare).

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt   # Windows
# source .venv/bin/activate && pip install -r requirements-dev.txt  # WSL/Linux

.venv\Scripts\python -m pytest -q

$env:ADMIN_USER="admin"; $env:ADMIN_PASSWORD="clave"
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Abre `http://127.0.0.1:8000/`. El admin pedirá las credenciales de arriba. La BD local se crea en `data/stocks.db`.

Si no hay activos, añádelos desde `/admin`. Tickers de Yahoo: `AAPL`, `SAN.MC`, `VOO`, `^GSPC` (se guardan en minúsculas). **Sin sufijo `.us`**: ese sufijo es de Stooq y en Yahoo da 404.

## Tests

```bash
.venv\Scripts\python -m pytest -q
```

## Despliegue en VPS 7 (Apache + Cloudflare)

1. `sudo mkdir -p /opt/StocksWeb && sudo chown ubuntu:ubuntu /opt/StocksWeb` y copiar el repo ahí.
2. Crear `/opt/StocksWeb/.env` con `ADMIN_USER`, `ADMIN_PASSWORD` (600, fuera del repo).
3. `cd /opt/StocksWeb && docker compose up -d --build`.
4. Copiar `apache-vhost.conf.example` a `/etc/apache2/sites-available/stocks.hugoperezvigo.es.conf`, `a2ensite`, `apache2ctl configtest`, `systemctl reload apache2`.
5. En Cloudflare: CNAME `stocks` → `hugoperezvigo.es`, proxied.
6. Verificar con UA de navegador (Cloudflare devuelve 1010 a clientes sin UA):
   ```bash
   curl -A "Mozilla/5.0" -sS -o /dev/null -w "%{http_code}\n" https://stocks.hugoperezvigo.es/       # 200
   curl -A "Mozilla/5.0" -sS -o /dev/null -w "%{http_code}\n" https://stocks.hugoperezvigo.es/admin # 401
   ```

**No ejecutar ningún cambio en producción sin confirmación previa** (normas de infraestructura SUOP).

### Trampa del DNS en este VPS

El DNS interno de Docker (`127.0.0.11`) reenvía al metadata de Oracle (`169.254.169.254`) y no resuelve hosts externos desde el contenedor. Ni `1.1.1.1` ni `8.8.8.8` funcionan como `dns:`. El compose usa `network_mode: host` y la app escucha en `127.0.0.1:8083` (Apache sigue apuntando ahí). Tras cambiar `network_mode`, hace falta `docker compose down && docker compose up -d` (un `up -d --force-recreate` no lo aplica).

### Cambiar credenciales

Docker no recarga `env_file` al editar `.env`; tras cambiarlo hay que recrear el contenedor:

```bash
cd /opt/StocksWeb && docker compose up -d --force-recreate --no-build
```

## Notas

- Yahoo Finance es gratuito y no oficial: los precios pueden ir con retraso. La capa de datos (`app/provider.py` + `app/market.py`) está aislada para poder cambiar de proveedor.
- Si un ticker falla, se conserva su último precio válido y se marca el error en el admin; el resto sigue actualizándose.
- Sin secretos en el repo: la contraseña solo vive en `.env` del servidor (600).
