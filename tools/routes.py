import json, sys, os
from build import build, to_gpx, to_geojson, G, STREETS

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')

# 5K: Parque Caldas -> Calle 4 oeste -> Cra 11 norte (puente) -> Calle 1 (orilla norte) este, Comfacauca,
#     glorieta El Paso -> Cra 6 sur por el Puente del Humilladero -> Calle 3 este -> Cra 4 norte (puente) ->
#     Calle 3N -> Cra 3 -> Calle 10N -> Cra 2 (El Morro) -> Cra 2 sur -> Calle 1 -> Cra 3 sur -> Calle 5 ->
#     Cra 5 -> Calle 6 -> Cra 6 -> Calle 7 -> Cra 8 norte -> Calle 5 este -> Parque Caldas
R5 = [
    ("Carrera 6", "Calle 4"), ("Carrera 11", "Calle 4"), ("Carrera 11", "Calle 1"),
    ("Carrera 9", "Calle 1"), ("Carrera 6", "Calle 1"), ("Carrera 6", "Calle 3"),
    ("Carrera 4", "Calle 3"), ("Carrera 4", "Calle 7"), ("Carrera 4", "Calle 3N"), ("Carrera 3", "Calle 3N"),
    ("Carrera 3", "Calle 10N"), ("Carrera 2", "Calle 15N"), ("Carrera 2", "Calle 7"),
    ("Carrera 3", "Calle 2"), ("Carrera 3", "Calle 5"), ("Carrera 5", "Calle 5"), ("Carrera 5", "Calle 6"),
    ("Carrera 6", "Calle 6"), ("Carrera 6", "Calle 7"), ("Carrera 8", "Calle 7"), ("Carrera 8", "Calle 5"),
    ("Carrera 6", "Calle 5"),
]

# Centro Deportivo Universitario Tulcán: Cra 3, Calle 10N y una vuelta a la pista atlética (en el sentido de las manecillas), salida por Cra 2
TULCAN = [("Carrera 3", "Calle 10N"), (2.44675, -76.59955), (2.44731, -76.59993), (2.44796, -76.59893), (2.44752, -76.59857),
          (2.44675, -76.59955), ("Carrera 2", "Calle 15N")]
# Circuito sur-occidental compartido por 10K y 21K: Cra 9 sur, Calle 13, Cra 10A, Benito Juárez, Calle 8, Cra 17,
# desvío Calle 5A / Cra 14 / Calle 4, Cra 17 norte, Transversal 9N, Cra 11 sur, Calle 5 hasta el Parque Caldas
SUR = [("Carrera 9", "Calle 7"), ("Carrera 9", "Calle 13"), ("Carrera 10A", "Calle 13"), ("Carrera 10A", "Calle 8"),
       ("Carrera 17", "Calle 8"), ("Carrera 17", "Calle 5A"), ("Carrera 14", "Calle 5A"), ("Carrera 14", "Calle 4"),
       ("Carrera 17", "Calle 4"), ("Carrera 17", "Transversal 9N"), (2.44995, -76.60936), ("Carrera 11", "Calle 1"),
       ("Carrera 11", "Calle 5"), ("Carrera 7", "Calle 5"), ("Carrera 6", "Calle 5")]

# 10K: primer tramo igual al 5K hasta Cra 4, vuelta a Tulcán, bajada por Cra 2, Calle 4, Cra 5, Calle 6, circuito sur
R10 = R5[:11] + TULCAN + [("Carrera 2", "Calle 7"), ("Carrera 2", "Calle 3"), ("Carrera 2", "Calle 4"),
       ("Carrera 5", "Calle 4"), ("Carrera 5", "Calle 6"), ("Carrera 6", "Calle 6"), ("Carrera 9", "Calle 6")] + SUR

# 21K: Calle 4, Cra 11, Calle 1, Cra 9 norte, Avenida Carrera 9 hasta Transversal 7 (km 6), regreso por Carrera 6
#      hasta el Humilladero (km 11), Calle 3, Cra 5 (puente), Calle 7, Cra 4, Cra 3, vuelta a la pista de Tulcán (km 12),
#      Cra 2 hasta las oficinas de Tránsito (km 14) y regreso, Cra 3 al sur, Calle 5, Cra 6, Calle 7, circuito sur
R21 = [("Carrera 6", "Calle 4"), ("Carrera 11", "Calle 4"), ("Carrera 11", "Calle 1"), ("Carrera 9", "Calle 1"),
       (2.45040, -76.60557), (2.45536, -76.59742), ("Avenida Carrera 9", "Calle 27N"),
       ("Avenida Carrera 9", "Calle 35N"), ("Avenida Carrera 9", "Transversal 7"), (2.47437, -76.57797),
       ("Carrera 6", "Calle 48N"), ("Carrera 6", "Calle 35N"), ("Carrera 6", "Calle 25"), ("Carrera 6", "Calle 15N"),
       ("Carrera 6", "Calle 9"), ("Carrera 6", "Calle 1N"), ("Carrera 6", "Calle 3"), (2.44278, -76.60451),
       (2.44642, -76.60299), ("Carrera 4", "Calle 7"), ("Carrera 4", "Calle 3N"), ("Carrera 3", "Calle 3N")] + TULCAN + [
       (2.45120, -76.59080), ("Carrera 2", "Calle 15N"), ("Carrera 3", "Calle 2N"), ("Carrera 3", "Calle 1"),
       ("Carrera 3", "Calle 5"), ("Carrera 6", "Calle 5"), ("Carrera 6", "Calle 7")] + SUR

ROUTES = [
    {'key': '5K', 'name': 'Media Maratón del Cauca - 5K', 'file': 'media-maraton-cauca-5k.gpx', 'wps': R5,
     'desc': 'Recorrido 5K (aprox.) Media Maratón del Cauca, Popayán. Salida y llegada en el Parque Caldas. Trazado sobre OpenStreetMap a partir del mapa oficial publicado; sujeto a modificaciones.'},
    {'key': '10K', 'name': 'Media Maratón del Cauca - 10K', 'file': 'media-maraton-cauca-10k.gpx', 'wps': R10,
     'desc': 'Recorrido 10K (aprox.) Media Maratón del Cauca, Popayán. Salida y llegada en el Parque Caldas. Trazado sobre OpenStreetMap a partir del mapa oficial publicado; sujeto a modificaciones.'},
    {'key': '21K', 'name': 'Media Maratón del Cauca - 21K', 'file': 'media-maraton-cauca-21k.gpx', 'wps': R21,
     'desc': 'Recorrido 21K Media Maratón del Cauca, Popayán. Salida y llegada en el Parque Caldas. Trazado sobre OpenStreetMap a partir del mapa oficial publicado; sujeto a modificaciones.'},
]

if __name__ == '__main__':
    fc = {'type': 'FeatureCollection', 'features': []}
    data = []
    for R in ROUTES:
        r = build(R['name'], R['wps'])
        print(f"== {R['key']}: {r['length']/1000:.3f} km, {len(r['coords'])} pts")
        for nm, L in r['streets']: print(f"   {nm:28s} {L:6.0f} m")
        gj = to_geojson(r)
        for f in gj['features']: f['properties']['route'] = R['key']
        fc['features'] += gj['features']
        open(f"{OUT}/{R['file']}", 'w').write(to_gpx(r, R['desc']))
        data.append({'key': R['key'], 'name': R['name'], 'file': R['file'], 'length': round(r['length']),
                     'coords': [[round(la, 6), round(lo, 6)] for la, lo in r['coords']],
                     'kms': [[k, round(la, 6), round(lo, 6)] for k, la, lo in r['kms']],
                     'desc': R['desc']})
    json.dump(fc, open(f'{OUT}/preview/routes.geojson', 'w'))
    html = open(TEMPLATE, encoding='utf-8').read().replace('/*__DATA__*/', 'const DATA = ' + json.dumps(data, ensure_ascii=False) + ';')
    open(f'{OUT}/mapa.html', 'w', encoding='utf-8').write(html)
    print('wrote', [R['file'] for R in ROUTES], 'and mapa.html')
