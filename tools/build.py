"""Build GPX + GeoJSON for a route defined as a list of waypoints.
Waypoint forms: ("Carrera 6", "Calle 5") -> intersection node; (lat, lon) -> nearest graph node.
"""
import json, sys, math, datetime
from graph import load, hav, norm, route, path_len, nearest
import networkx as nx

G, STREETS = load()

def wp_node(wp):
    if isinstance(wp, tuple) and isinstance(wp[0], str):
        a = STREETS.get(norm(wp[0]), set()); b = STREETS.get(norm(wp[1]), set())
        common = a & b
        if not common:
            # closest pair of nodes between the two streets
            best = None
            for i in a:
                for j in b:
                    d = hav(G.nodes[i]['ll'], G.nodes[j]['ll'])
                    if best is None or d < best[0]: best = (d, i, j)
            if best and best[0] < 40:
                return best[1]
            raise SystemExit(f'no intersection {wp} (closest {best[0] if best else None} m)')
        if len(common) > 1 and len(wp) > 2:
            # pick the one nearest to a hint (lat,lon)
            return min(common, key=lambda n: hav(G.nodes[n]['ll'], wp[2]))
        # pick the one with most street-edges (main crossing)
        return sorted(common, key=lambda n: -len(G[n]))[0]
    return nearest(G, wp[0], wp[1])


def wp_candidates(wp):
    if isinstance(wp, tuple) and isinstance(wp[0], str):
        a = STREETS.get(norm(wp[0]), set()); b = STREETS.get(norm(wp[1]), set())
        common = a & b
        if common: return list(common)
        best = []
        for i in a:
            for j in b:
                d = hav(G.nodes[i]['ll'], G.nodes[j]['ll'])
                if d < 40: best.append((d, i))
        if best: return [i for d, i in sorted(best)[:3]]
        raise SystemExit(f'no intersection {wp}')
    return [nearest(G, wp[0], wp[1])]

def resolve(waypoints):
    """Pick, for each waypoint, the candidate node nearest to the previous chosen node."""
    cands = [wp_candidates(w) for w in waypoints]
    # first: candidate nearest to the first candidate of the 2nd waypoint
    prev = None
    out = []
    for i, c in enumerate(cands):
        if prev is None:
            nxt = cands[1][0] if len(cands) > 1 else c[0]
            n = min(c, key=lambda x: hav(G.nodes[x]['ll'], G.nodes[nxt]['ll']))
        else:
            n = min(c, key=lambda x: hav(G.nodes[x]['ll'], G.nodes[prev]['ll']))
        out.append(n); prev = n
    return out

def build(name, waypoints, avoid=()):
    H = G.copy()
    for a, b in avoid:  # (street names) edges to remove
        pass
    nodes = resolve(waypoints)
    path = route(H, nodes)
    coords = [H.nodes[n]['ll'] for n in path]
    # dedupe consecutive duplicates
    out = [coords[0]]
    for c in coords[1:]:
        if c != out[-1]: out.append(c)
    L = path_len(H, path)
    # cumulative distance per point, and km markers
    cum = [0.0]
    for a, b in zip(out, out[1:]): cum.append(cum[-1] + hav(a, b))
    kms = []
    k = 1
    for i in range(1, len(out)):
        while cum[i] >= k*1000:
            f = (k*1000 - cum[i-1]) / (cum[i] - cum[i-1])
            kms.append((k, out[i-1][0] + f*(out[i][0]-out[i-1][0]), out[i-1][1] + f*(out[i][1]-out[i-1][1])))
            k += 1
    # streets used, in order
    seq = []
    for a, b in zip(path, path[1:]):
        nm = H[a][b]['name'] or '?'
        if not seq or seq[-1][0] != nm: seq.append([nm, H[a][b]['length']])
        else: seq[-1][1] += H[a][b]['length']
    return {'name': name, 'coords': out, 'length': L, 'cum': cum, 'kms': kms, 'streets': seq, 'wps': [H.nodes[n]['ll'] for n in nodes]}

def to_gpx(r, desc=''):
    pts = ''.join(f'      <trkpt lat="{la:.6f}" lon="{lo:.6f}"></trkpt>\n' for la, lo in r['coords'])
    wpts = f'  <wpt lat="{r["coords"][0][0]:.6f}" lon="{r["coords"][0][1]:.6f}"><name>Salida / Llegada - Parque Caldas</name></wpt>\n'
    wpts += ''.join(f'  <wpt lat="{la:.6f}" lon="{lo:.6f}"><name>Km {k}</name></wpt>\n' for k, la, lo in r['kms'])
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="ruta-mmc" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <name>{r['name']}</name>
    <desc>{desc}</desc>
    <time>{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</time>
  </metadata>
{wpts}  <trk>
    <name>{r['name']}</name>
    <trkseg>
{pts}    </trkseg>
  </trk>
</gpx>
'''

def to_geojson(r):
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'name': r['name'], 'length': r['length']},
         'geometry': {'type': 'LineString', 'coordinates': [[lo, la] for la, lo in r['coords']]}},
        *[{'type': 'Feature', 'properties': {'km': k}, 'geometry': {'type': 'Point', 'coordinates': [lo, la]}} for k, la, lo in r['kms']],
        *[{'type': 'Feature', 'properties': {'wp': i}, 'geometry': {'type': 'Point', 'coordinates': [lo, la]}} for i, (la, lo) in enumerate(r['wps'])],
    ]}
