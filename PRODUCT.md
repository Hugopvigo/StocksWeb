# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: Python 3.12 + FastAPI + SQLite + httpx, frontend vanilla JS con gráficos SVG propios, un contenedor Docker en VPS 7 (ARM). Elegido por simplicidad, sin build step y sin claves de API.

## Users

- **Hugo (propietario):** revisa sus acciones y ETFs desde el móvil y el escritorio; gestiona la lista de activos, cantidades, precios de compra y corrige valores a mano desde un admin privado.
- **Visitantes públicos:** consultan una web de solo lectura con precios, variación y gráficos. No necesitan cuenta y no deben poder modificar nada ni ver importes/cantidades del propietario.

## Product Purpose

Un dashboard de seguimiento de cartera (acciones, ETFs, etc.) con datos públicos de Yahoo Finance sin realtime, actualizados cada hora. El valor para Hugo: ver su cartera en un solo sitio y tener el control editorial de lo que se muestra, sin que el público pueda alterarlo.

## Operating Context

- Dominio público: `stocks.hugoperezvigo.es`, servido por Apache en VPS 7 con Cloudflare delante. Se indexa en buscadores (sin `noindex`).
- El admin va detrás de HTTP Basic Auth con contraseña de un solo usuario.
- Actualización horaria mediante un bucle en el proceso; botón "Actualizar ahora" en el admin.
- Yahoo Finance: API pública de chart, sin clave. Tickers (`AAPL`, `SAN.MC`, `VOO`); se normalizan a minúsculas en la BD. Stooq se descartó porque exige verificación JavaScript.

## Capabilities and Constraints

- Público: tabla de cotizaciones (precio, variación diaria), gráfico histórico por activo y distribución por número de activos (acciones vs ETFs). **Nunca** expone cantidades, precio de compra, importes ni P&L.
- Admin: CRUD de activos (ticker, nombre, tipo, cantidad, precio medio de compra), campo de **precio manual (override)** que manda sobre el valor de la API, resumen con valor total y P&L, y actualización manual.
- Un ticker con error no rompe el barrido: se conserva el último dato válido y se reporta el error.
- Sin secretos en el repositorio; la contraseña vive en `.env` del servidor (600).
- **Inferido del brief** (no confirmado explícitamente): interfaz en español, tema oscuro, moneda por defecto USD (configurable por activo no solicitada).

## Product Principles

1. El backend es el único escritor: el público solo lee.
2. La corrección manual gana siempre sobre el dato automático.
3. Lo privado nunca cruza la frontera de la API pública.
4. Simple primero: sin build, sin frameworks de UI, sin dependencias de pago.

## Accessibility & Inclusion

Sin requisitos legales declarados. Se aplica WCAG AA por defecto: contraste, foco visible, tablas con encabezados, etiquetas en formularios y diseño mobile-first.
