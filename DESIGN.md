# Visual direction contract (surface: `stocks.hugoperezvigo.es`)

> Modo **Operate** (dashboard). Restrained + un acento propio. Tema oscuro elegido por el使用场景: revisión rápida de cartera en móvil, a menudo de noche, con lectura frecuente de cifras.

**THESIS.** Un terminal de mercado que se lee como un paper financiero, no como una app de gamificación: la cifra y la línea importan; el ruido no. Se rechaza la cuadrícula de tarjetas iguales y el "hero de métrica gigante" genérico.

**OWN-WORLD.** Fondo tinta azulada (`#0F151D`), superficie (`#171F2A`), superficie elevada (`#1F2937`); texto cálido (`#E7EDF3`) y secundario teñido (`#93A1B1`); acento oro (`#E3B341`) para identidad y foco; verde menta (`#3FD08A`) y coral (`#F0756B`) para estado. Reglas finas de 1px, radios 12–14px, una sola elevación suave con offset. Numeros en mono tabular; UI en sans del sistema. Sin glow, sin glass decorativo, sin degradados en texto.

**STORY.** El visitante entiende en un vistazo qué se sigue, cómo va hoy y dónde está el gráfico; el propietario entra al admin, ve su cartera y corrige lo que quiera con un campo claro.

**FIRST VIEWPORT (móvil 390px).** Cabecera compacta con marca y "datos cada hora". Banda de resumen con 3 cifras (activos, acciones/ETFs, última actualización) sin tarjetas: divisores finos. Gráfico principal del activo seleccionado con selector de rango. Debajo, lista de tickers con precio, badge de variación y sparkline; tocar una fila cambia el gráfico. En escritorio, resumen arriba, gráfico a la izquierda y tabla a la derecha.

**FORM.** Operate/Surface. Estructura propia derivada de "paper de mercado": tabla + gráfico, densidad alta pero legible. Semilla: `market-paper`.

**FINISH.** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
