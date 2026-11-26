import json, math, re, sys, os
import networkx as nx

OSM = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'osm', 'streets.json')
SKIP = {'motorway','motorway_link','construction','proposed','raceway','bus_guideway','platform'}

def hav(a, b):
    R = 6371000.0
    la1, lo1 = map(math.radians, a); la2, lo2 = map(math.radians, b)
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*R*math.asin(math.sqrt(h))

def norm(name):
    n = name.lower().strip()
    n = n.replace('avenida ', '').replace('av. ', '')
    n = re.sub(r'\s+', ' ', n)
    n = n.replace(' norte', 'n').replace(' bis', 'bis').replace(' este', 'e')
    n = re.sub(r'(\d)\s+([a-z])', r'\1\2', n)
    return n

def load():
    d = json.load(open(OSM))
    nodes = {e['id']: (e['lat'], e['lon']) for e in d['elements'] if e['type'] == 'node'}
    G = nx.Graph()
    streets = {}  # norm name -> set of node ids
    for w in d['elements']:
        if w['type'] != 'way': continue
        t = w.get('tags', {})
        hw = t.get('highway')
        if not hw or hw in SKIP: continue
        name = t.get('name', '')
        nn = norm(name) if name else ''
        ids = [i for i in w['nodes'] if i in nodes]
        for a, b in zip(ids, ids[1:]):
            L = hav(nodes[a], nodes[b])
            if G.has_edge(a, b):
                if not G[a][b]['name'] and name: G[a][b]['name'] = name
                continue
            G.add_edge(a, b, length=L, name=name, hw=hw)
        if nn:
            streets.setdefault(nn, set()).update(ids)
    for n in G.nodes: G.nodes[n]['ll'] = nodes[n]
    # extra ways not tagged as highway (e.g. the Tulcán running track), connected to the nearest street node
    extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'osm', 'extra.json')
    if os.path.exists(extra):
        street_nodes = list(G.nodes)
        for w in json.load(open(extra))['elements']:
            name = w.get('tags', {}).get('name') or 'Pista Tulcán'
            pts = [(p['lat'], p['lon']) for p in w['geometry']]
            ids = [f"x{w['id']}_{i}" for i in range(len(pts))]
            for i, (a, b) in enumerate(zip(ids, ids[1:])):
                G.add_edge(a, b, length=hav(pts[i], pts[i+1]), name=name, hw='track')
            for i, n in enumerate(ids): G.nodes[n]['ll'] = pts[i]
            # connect the two closest pairs (track node, street node) within 90 m
            pairs = sorted(((hav(pts[i], G.nodes[s]['ll']), ids[i], s) for i in range(len(pts)) for s in street_nodes
                            if abs(G.nodes[s]['ll'][0]-pts[i][0]) < 0.001 and abs(G.nodes[s]['ll'][1]-pts[i][1]) < 0.001))
            used = set()
            for d, a, s in pairs:
                if d > 90 or len(used) >= 2: break
                if a in used: continue
                G.add_edge(a, s, length=d, name='', hw='path'); used.add(a)
            streets.setdefault(norm(name), set()).update(ids)
    return G, streets

def intersections(streets, G, s1, s2):
    a = streets.get(norm(s1), set()); b = streets.get(norm(s2), set())
    common = a & b
    # also near-misses: nodes of s1 within 12 m of nodes of s2 (separate carriageways)
    return sorted(common)

def nearest(G, lat, lon):
    return min(G.nodes, key=lambda n: hav(G.nodes[n]['ll'], (lat, lon)))

def route(G, pts):
    path = []
    for a, b in zip(pts, pts[1:]):
        p = nx.shortest_path(G, a, b, weight='length')
        path.extend(p if not path else p[1:])
    return path

def path_len(G, path):
    return sum(G[a][b]['length'] for a, b in zip(path, path[1:]))

if __name__ == '__main__':
    G, streets = load()
    print('graph', G.number_of_nodes(), G.number_of_edges(), 'streets', len(streets))
    for s in sys.argv[1:]:
        ids = streets.get(norm(s), set())
        pts = [G.nodes[i]['ll'] for i in ids]
        if not pts: print(s, 'NOT FOUND'); continue
        lats = [p[0] for p in pts]; lons = [p[1] for p in pts]
        print(f"{s}: {len(ids)} nodes lat {min(lats):.5f}..{max(lats):.5f} lon {min(lons):.5f}..{max(lons):.5f}")
        # crossing streets
        xs = {}
        for i in ids:
            for nb in G[i]:
                nm = G[i][nb]['name']
                if nm and norm(nm) != norm(s):
                    xs.setdefault(nm, []).append(G.nodes[i]['ll'])
        for nm, ll in sorted(xs.items(), key=lambda kv: kv[1][0]):
            print(f"   x {nm:22s} {ll[0][0]:.5f},{ll[0][1]:.5f}  ({len(ll)})")
