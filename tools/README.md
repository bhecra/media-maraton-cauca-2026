# Herramienta de trazado (Media Maratón del Cauca)

Genera los GPX y `mapa.html` a partir de listas de intersecciones (Carrera x Calle) trazadas sobre las calles reales de Popayán (OpenStreetMap).

- `osm/streets.json`: calles del centro de Popayán descargadas de Overpass (nov 2026).
- `graph.py`: grafo de calles, búsqueda de intersecciones, ruta más corta entre puntos.
- `build.py`: convierte una lista de intersecciones en track, puntos kilométricos, GPX y GeoJSON.
- `routes.py`: definición de cada recorrido (5K, 10K, 21K) como secuencia de intersecciones. Aquí se agregan o corrigen rutas.
- `template.html`: plantilla del mapa interactivo (`mapa.html`).

Uso (requiere Python 3 con `networkx`):

```bash
python3 -m venv venv && ./venv/bin/pip install networkx
./venv/bin/python tools/routes.py
```

Escribe `media-maraton-cauca-<distancia>.gpx` y `mapa.html` en la carpeta `ruta/`, y `preview/routes.geojson` para la página de verificación `preview/index.html`.

## Publicar en Vercel

La carpeta `public/` es el sitio estático que Vercel sirve (`index.html` es `mapa.html` y los tres GPX van al lado). `tools/routes.py` la regenera. `.vercelignore` deja por fuera `tools/`, `referencia/` y `preview/`.

```bash
npx vercel login
npx vercel --prod
```

La primera vez el CLI pregunta el nombre del proyecto y la configuración: aceptar los valores por defecto (framework "Other", sin build). Cada `npx vercel --prod` posterior publica los cambios.
