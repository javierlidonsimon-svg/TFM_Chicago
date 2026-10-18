"""Pruebas contra los datos entregados y los límites de las reglas de limpieza."""
from pathlib import Path
import sys, unittest, hashlib, json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from analisis import meteo_group

class TestTFM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=pd.read_csv(ROOT/'data/processed/accidentes_meteorologia_2024.csv')
        cls.w=pd.read_csv(ROOT/'data/processed/meteorologia_diaria.csv')

    def test_requisitos_y_unicidad(self):
        self.assertGreaterEqual(len(self.d),50000)
        self.assertGreaterEqual(len(self.d.columns),20)
        self.assertTrue(self.d.crash_record_id.is_unique)
        expected=int(json.loads((ROOT/'data/raw/chicago_recuento.json').read_text())[0]['count'])
        self.assertEqual(len(self.d),expected)

    def test_fuentes_intactas(self):
        m=json.loads((ROOT/'data/raw/manifest.json').read_text())
        for item in m['fuentes']:
            actual=hashlib.sha256((ROOT/'data/raw'/item['archivo']).read_bytes()).hexdigest()
            self.assertEqual(actual,item['sha256'])

    def test_csv_meteo_fiel_a_respuesta_original(self):
        source=ROOT/'data/raw/open_meteo_chicago_2024.json'
        csv=ROOT/'data/raw/open_meteo_chicago_2024.csv'
        expected=pd.DataFrame(json.loads(source.read_text(encoding='utf-8'))['daily'])
        pd.testing.assert_frame_equal(expected,pd.read_csv(csv),check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
        manifest=json.loads((ROOT/'data/raw/exportacion_csv_meteo.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),manifest['sha256_origen'])
        self.assertEqual(hashlib.sha256(csv.read_bytes()).hexdigest(),manifest['sha256_csv'])

    def test_todas_las_variables_meteorologicas(self):
        joined=self.d[['fecha']].merge(self.w,on='fecha',how='left',validate='many_to_one')
        for col in self.w.columns:
            if col=='fecha':continue
            pd.testing.assert_series_equal(joined[col],self.d[col],check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)

    def test_union_y_calendario(self):
        self.assertEqual(len(self.w),366)
        self.assertTrue(self.w.fecha.is_unique)
        self.assertEqual(set(self.w.fecha),set(pd.date_range('2024-01-01','2024-12-31').strftime('%Y-%m-%d')))
        expected=self.d[['fecha']].merge(self.w,on='fecha',validate='many_to_one')
        self.assertEqual(len(expected),len(self.d))
        self.assertTrue((expected.precipitation_sum.to_numpy()==self.d.precipitation_sum.to_numpy()).all())

    def test_umbrales_y_prioridad_nieve(self):
        x=pd.DataFrame({'precipitation_sum':[0,.99,1,20,0], 'snowfall_sum':[0,0,0,.1,.1]})
        self.assertEqual(meteo_group(x).tolist(),['Seco','Seco','Precipitacion','Nieve','Nieve'])

    def test_nulos_lesiones_no_son_ceros(self):
        mask=self.d.injuries_total.isna()
        self.assertTrue(self.d.loc[mask,'con_lesiones'].isna().all())
        self.assertTrue(self.d.loc[mask,'lesion_conocida'].eq(0).all())
        self.assertEqual(int(self.d.con_lesiones.sum()),int(self.d.injuries_total.gt(0).sum()))

    def test_agregados_dashboard(self):
        s=pd.read_csv(ROOT/'data/processed/resumen_dashboard.csv')
        for dim in ['Total','Hora','Dia','Via']:
            part=s[s.dimension.eq(dim)]
            self.assertEqual(int(part.accidentes.sum()),len(self.d))
            self.assertEqual(int(part.con_lesiones.sum()),int(self.d.con_lesiones.sum()))
        days=pd.read_csv(ROOT/'data/processed/dias_dashboard.csv')
        self.assertEqual(days.dias.sum(),366)

if __name__=='__main__':unittest.main()
