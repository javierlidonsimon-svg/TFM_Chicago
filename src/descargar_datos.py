"""Descarga dos fuentes públicas sin modificar sus respuestas originales."""
from pathlib import Path
import csv, hashlib, json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
WHERE = "crash_date >= '2024-01-01T00:00:00' AND crash_date < '2025-01-01T00:00:00'"

def fetch(url, destination):
    if destination.exists():
        print('Conservado:', destination.name, flush=True)
        return
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AcademicDataAnalysis/1.0'})
            with urllib.request.urlopen(req, timeout=180) as response:
                content = response.read()
            destination.write_bytes(content)
            print('Descargado:', destination.name, len(content), flush=True)
            return
        except Exception:
            if attempt == 2: raise
            time.sleep(3)

def export_weather_csv():
    """Copia tabular fiel de daily: sin limpieza, agregados ni variables derivadas."""
    source = RAW / 'open_meteo_chicago_2024.json'
    daily = json.loads(source.read_text(encoding='utf-8'))['daily']
    lengths = {len(values) for values in daily.values()}
    if len(lengths) != 1:
        raise ValueError('Longitudes meteorológicas distintas: no se exporta el CSV.')
    target = RAW / 'open_meteo_chicago_2024.csv'
    with target.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(daily.keys())
        writer.writerows(zip(*daily.values()))
    (RAW / 'exportacion_csv_meteo.json').write_text(json.dumps({
        'archivo': target.name, 'origen': source.name,
        'operacion': 'Serialización del bloque daily a CSV. Mismos nombres, orden y valores; sin limpieza ni variables derivadas.',
        'sha256_origen': hashlib.sha256(source.read_bytes()).hexdigest(),
        'sha256_csv': hashlib.sha256(target.read_bytes()).hexdigest(),
        'unidades': json.loads(source.read_text(encoding='utf-8'))['daily_units']
    }, indent=2, ensure_ascii=False), encoding='utf-8')

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    queries = [
        ('chicago_accidentes_2024.csv', 'https://data.cityofchicago.org/resource/85ca-t3if.csv?' + urllib.parse.urlencode({'$where': WHERE, '$limit': 200000, '$order': 'crash_record_id'})),
        ('chicago_metadata.json', 'https://data.cityofchicago.org/api/views/85ca-t3if.json'),
        ('chicago_recuento.json', 'https://data.cityofchicago.org/resource/85ca-t3if.json?' + urllib.parse.urlencode({'$where': WHERE, '$select': 'count(*)'})),
        ('open_meteo_chicago_2024.json', 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode({
            'latitude':41.8781, 'longitude':-87.6298, 'start_date':'2024-01-01', 'end_date':'2024-12-31',
            'daily':'temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max,wind_gusts_10m_max',
            'timezone':'America/Chicago', 'models':'era5', 'temperature_unit':'celsius', 'wind_speed_unit':'kmh', 'precipitation_unit':'mm'})),
    ]
    manifest=[]
    for name,url in queries:
        p=RAW/name
        fetch(url,p)
        manifest.append({'archivo':name, 'url':url, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes':p.stat().st_size})
    m=RAW/'manifest.json'
    if not m.exists():
        m.write_text(json.dumps({'descarga_utc':datetime.now(timezone.utc).isoformat(), 'fuentes':manifest},indent=2),encoding='utf-8')
    export_weather_csv()

if __name__ == '__main__': main()
