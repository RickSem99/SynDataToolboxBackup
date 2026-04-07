"""
migrate_recorded_path.py
Converte il recorded_path.json dal vecchio formato {"time": ...} al nuovo {"timestamp": N}.
"""
import json
import os
import shutil

path_file = r'C:\Users\Andromeda\Documents\Unreal Projects\Supermarket\Saved\recorded_path.json'

# Backup del file originale
backup_file = path_file.replace('.json', '_backup_old_format.json')
shutil.copy2(path_file, backup_file)
print(f"✅ Backup salvato in: {backup_file}")

with open(path_file, 'r') as f:
    path = json.load(f)

print(f"📂 Punti trovati: {len(path)}")
print(f"🔍 Primo punto originale: {path[0]}")

# Controlla se già nel nuovo formato
if 'timestamp' in path[0]:
    print("ℹ️  Il file è già nel nuovo formato con 'timestamp'. Nessuna migrazione necessaria.")
    exit(0)

# Migrazione: sostituisce "time" con "timestamp" progressivo (1-based)
migrated = []
for i, point in enumerate(path):
    migrated.append({
        "timestamp": i + 1,
        "loc": point["loc"],
        "rot": point["rot"]
    })

with open(path_file, 'w') as f:
    json.dump(migrated, f, indent=4)

print(f"✅ Migrazione completata: {len(migrated)} punti convertiti.")
print(f"🔍 Primo punto nuovo: {migrated[0]}")
print(f"🔍 Secondo punto nuovo: {migrated[1]}")
print(f"🔍 Ultimo punto nuovo:  {migrated[-1]}")
