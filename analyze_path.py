import json
import math

path_file = r'C:\Users\Andromeda\Documents\Unreal Projects\Supermarket\Saved\recorded_path.json'
with open(path_file) as f:
    path = json.load(f)

print(f'Totale punti: {len(path)}')
key = 'timestamp' if 'timestamp' in path[0] else 'time'
print(f'Campo temporale rilevato: "{key}"')
print(f'Primo:   {key}={path[0][key]}  loc={path[0]["loc"]}, rot={path[0]["rot"]}')
print(f'Secondo: {key}={path[1][key]}  loc={path[1]["loc"]}, rot={path[1]["rot"]}')
print(f'Terzo:   {key}={path[2][key]}  loc={path[2]["loc"]}, rot={path[2]["rot"]}')
print()

distances = []
for i in range(1, len(path)):
    p0 = path[i-1]['loc']
    p1 = path[i]['loc']
    dist = math.sqrt(sum((p1[j]-p0[j])**2 for j in range(3)))
    dt = path[i]['time'] - path[i-1]['time']
    distances.append({
        'idx': i,
        'dist': dist,
        'dt': dt,
        'loc': p1,
        'loc_prev': p0,
        'rot': path[i]['rot']
    })

dists_vals = [d['dist'] for d in distances]
mean_d = sum(dists_vals) / len(dists_vals)
std_d = math.sqrt(sum((x - mean_d)**2 for x in dists_vals) / len(dists_vals))

print('=== STATISTICHE DISTANZE ===')
print(f'Media:    {mean_d:.2f} cm')
print(f'StdDev:   {std_d:.2f} cm')
print(f'Min:      {min(dists_vals):.2f} cm')
print(f'Max:      {max(dists_vals):.2f} cm')
print(f'Soglia anomalia (media + 5*std): {mean_d + 5*std_d:.2f} cm')
print()

dts = [d['dt'] for d in distances]
mean_dt = sum(dts) / len(dts)
print('=== STATISTICHE TEMPO ===')
print(f'Media dt: {mean_dt:.3f}s  ({1/mean_dt:.1f} Hz)')
print(f'Max dt:   {max(dts):.3f}s')
print(f'Min dt:   {min(dts):.3f}s')
print()

# Anomalie di distanza (salti bruschi)
threshold = mean_d + 5 * std_d
anomalies = [d for d in distances if d['dist'] > threshold]
print(f'=== ANOMALIE DISTANZA (dist > {threshold:.1f} cm): {len(anomalies)} ===')
for a in anomalies[:20]:
    print(f'  [{a["idx"]:04d}] dist={a["dist"]:8.1f} cm | dt={a["dt"]:.3f}s')
    print(f'    Da:  loc={[round(x,1) for x in a["loc_prev"]]}')
    print(f'    A:   loc={[round(x,1) for x in a["loc"]]}  rot={[round(x,1) for x in a["rot"]]}')

# Punti a zero
zero_points = [i for i, p in enumerate(path) if all(abs(v) < 0.01 for v in p['loc'])]
print(f'\n=== PUNTI A ZERO (loc=[0,0,0]): {len(zero_points)} ===')
if zero_points:
    print(f'  Indici: {zero_points[:20]}')

# Duplicati consecutivi esatti
dups = [i for i in range(1, len(path)) if path[i]['loc'] == path[i-1]['loc']]
print(f'\n=== DUPLICATI CONSECUTIVI ESATTI: {len(dups)} ===')
if dups:
    print(f'  Indici: {dups[:20]}')

# Prime 10 distanze
print('\n=== PRIME 10 DISTANZE ===')
for d in distances[:10]:
    print(f'  [{d["idx"]:04d}] {d["dist"]:7.2f} cm  dt={d["dt"]:.3f}s  loc={[round(x,1) for x in d["loc"]]}')
