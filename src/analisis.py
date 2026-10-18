"""Limpieza, unión m:1, EDA y estadística reproducibles del TFM.

Unidad principal: un accidente. Inferencia meteorológica: un día (366 días).
No se imputan lesiones ausentes ni se interpretan asociaciones como causas.
"""
from pathlib import Path
import json, os, tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'tfm_chicago_matplotlib'))
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC = ROOT/'data/raw', ROOT/'data/processed'
TABLES, FIG = ROOT/'reports/tables', ROOT/'reports/figures'
SEED = 2024
WEATHER = ['Seco', 'Precipitacion', 'Nieve']
DAYS = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
MONTHS = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
COLS = ['crash_record_id','crash_date','crash_date_est_i','posted_speed_limit',
 'traffic_control_device','device_condition','weather_condition','lighting_condition',
 'first_crash_type','trafficway_type','alignment','roadway_surface_cond','road_defect',
 'report_type','crash_type','intersection_related_i','private_property_i','hit_and_run_i',
 'damage','date_police_notified','prim_contributory_cause','sec_contributory_cause',
 'street_direction','street_name','beat_of_occurrence','num_units','most_severe_injury',
 'injuries_total','injuries_fatal','injuries_incapacitating','injuries_non_incapacitating',
 'injuries_reported_not_evident','injuries_no_indication','injuries_unknown','latitude','longitude']

def meteo_group(w, threshold=1.0):
    # Snowfall is in cm. Precipitation includes rain and water-equivalent snow (mm).
    return np.select([w.snowfall_sum >= .1, w.precipitation_sum >= threshold],
                     ['Nieve','Precipitacion'], default='Seco')

def save_table(df, name, index=False):
    df.to_csv(TABLES/f'{name}.csv',index=index)

def clean_join():
    raw = pd.read_csv(RAW/'chicago_accidentes_2024.csv',dtype='string')
    expected = int(json.loads((RAW/'chicago_recuento.json').read_text())[0]['count'])
    assert len(raw) == expected, 'Descarga incompleta o fuente modificada: revisar recuento.'
    qa = {'filas_originales':len(raw),'columnas_originales':len(raw.columns)}
    save_table(pd.DataFrame({'variable':raw.columns,'nulos':raw.isna().sum().values,
                            'porcentaje_nulo':raw.isna().mean().values*100}), 'nulos_originales')
    qa['duplicados_exactos'] = int(raw.duplicated().sum())
    raw = raw.drop_duplicates()
    if raw.crash_record_id.duplicated().any():
        raise ValueError('Identificadores repetidos con contenido diferente. Revisar manualmente.')
    d = raw[COLS].copy()
    for c in d.columns:
        d[c] = d[c].str.strip().replace('',pd.NA)
    d['crash_date'] = pd.to_datetime(d.crash_date,errors='coerce')
    d['date_police_notified'] = pd.to_datetime(d.date_police_notified,errors='coerce')
    valid = d.crash_date.notna() & d.crash_date.ge('2024-01-01') & d.crash_date.lt('2025-01-01') & d.crash_record_id.notna()
    qa['excluidas_fecha_o_id'] = int((~valid).sum())
    d.loc[~valid].to_csv(PROC/'registros_excluidos.csv',index=False)
    d = d.loc[valid].copy()
    nums = ['posted_speed_limit','num_units','latitude','longitude'] + [c for c in COLS if c.startswith('injuries_')]
    for c in nums:
        d[c] = pd.to_numeric(d[c],errors='coerce')
    # Codes Y/N: absence is unknown, never automatically interpreted as No.
    for c in ['crash_date_est_i','intersection_related_i','private_property_i','hit_and_run_i']:
        d[c] = d[c].map({'Y':'Sí','N':'No'}).fillna('No consta')
    categorical = [c for c in COLS if c not in nums and c not in ['crash_date','date_police_notified','crash_record_id']]
    for c in categorical:
        d[c] = d[c].fillna('No consta')
    qa['limite_velocidad_no_valido'] = int((~d.posted_speed_limit.between(1,100)).sum())
    # Range is a plausibility screen, not a statutory speed limit. Keep raw unchanged.
    d.loc[~d.posted_speed_limit.between(1,100),'posted_speed_limit'] = np.nan
    badgeo = ~(d.latitude.between(41.6,42.1)&d.longitude.between(-88,-87.4))
    qa['coordenadas_ausentes_o_fuera_envolvente'] = int(badgeo.sum())
    d.loc[badgeo,['latitude','longitude']] = np.nan
    qa['lesiones_negativas'] = 0
    for c in [x for x in nums if x.startswith('injuries_')]+['num_units']:
        mask = d[c].lt(0)
        qa['lesiones_negativas'] += int(mask.sum())
        d.loc[mask,c] = np.nan
    d['fecha'] = d.crash_date.dt.strftime('%Y-%m-%d')
    d['mes'] = d.crash_date.dt.month
    d['hora'] = d.crash_date.dt.hour
    d['dia_semana_num'] = d.crash_date.dt.dayofweek
    d['dia_semana'] = d.dia_semana_num.map(dict(enumerate(DAYS)))
    d['via'] = d.street_direction.str.cat(d.street_name,sep=' ').str.strip()
    # injuries_total includes fatal injuries. Use accurate labels in all outputs.
    d['con_lesiones'] = d.injuries_total.gt(0).astype(float).where(d.injuries_total.notna())
    d['con_lesion_grave_o_mortal'] = (d.injuries_incapacitating+d.injuries_fatal).gt(0).astype(float).where(d.injuries_incapacitating.notna()&d.injuries_fatal.notna())
    d['lesion_conocida'] = d.injuries_total.notna().astype(int)
    d['horas_hasta_aviso'] = (d.date_police_notified-d.crash_date).dt.total_seconds()/3600
    qa['avisos_anteriores_accidente'] = int(d.horas_hasta_aviso.lt(0).sum())
    d.loc[d.horas_hasta_aviso.lt(0),'horas_hasta_aviso'] = np.nan
    components = ['injuries_fatal','injuries_incapacitating','injuries_non_incapacitating','injuries_reported_not_evident']
    qa['discrepancias_suma_lesiones'] = int((d[components].sum(axis=1,min_count=4)-d.injuries_total).abs().gt(0).sum())
    wjson = json.loads((RAW/'open_meteo_chicago_2024.json').read_text())
    w = pd.DataFrame(wjson['daily']).rename(columns={'time':'fecha'})
    assert len(w)==366 and w.fecha.is_unique
    assert w.drop(columns='fecha').notna().all().all(), 'Meteorología incompleta'
    w['grupo_meteo'] = meteo_group(w)
    w.to_csv(PROC/'meteorologia_diaria.csv',index=False)
    d = d.merge(w,on='fecha',how='left',validate='many_to_one',indicator=True)
    qa['sin_correspondencia_meteo'] = int(d['_merge'].ne('both').sum())
    assert qa['sin_correspondencia_meteo']==0
    d = d.drop(columns='_merge')
    qa.update(filas_finales=len(d),columnas_finales=len(d.columns),dias_meteorologia=len(w),
              lesion_desconocida=int(d.injuries_total.isna().sum()),
              coordenadas_meteo_respuesta={k:wjson[k] for k in ['latitude','longitude','elevation','timezone']})
    assert len(d)>=50000 and len(d.columns)>=20 and d.crash_record_id.is_unique
    d.to_csv(PROC/'accidentes_meteorologia_2024.csv',index=False)
    save_table(pd.DataFrame({'variable':d.columns,'tipo':[str(t) for t in d.dtypes],
        'nulos':d.isna().sum().values,'valores_distintos':d.nunique().values}), 'calidad_final')
    (ROOT/'reports/calidad.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False),encoding='utf-8')
    return d,w,qa

def summarize(d,keys):
    return d.groupby(keys,dropna=False).agg(accidentes=('crash_record_id','size'),
        con_lesiones=('con_lesiones','sum'),lesion_conocida=('lesion_conocida','sum'),
        personas_lesionadas=('injuries_total',lambda x:x.sum(min_count=1)),
        fallecidos=('injuries_fatal',lambda x:x.sum(min_count=1)),
        graves_o_mortales=('con_lesion_grave_o_mortal','sum')).reset_index()

def stats_analysis(d,w):
    daily = w.merge(summarize(d,['fecha']),on='fecha',how='left',validate='one_to_one')
    cols=['accidentes','con_lesiones','lesion_conocida','personas_lesionadas','fallecidos','graves_o_mortales']
    daily[cols] = daily[cols].fillna(0) # Here zero means a covered calendar day without crashes.
    dates = pd.to_datetime(daily.fecha)
    daily['mes'] = dates.dt.month
    daily['dia_semana_num'] = dates.dt.dayofweek
    daily.to_csv(PROC/'serie_diaria.csv',index=False)
    byweather = daily.groupby('grupo_meteo').agg(dias=('fecha','size'),accidentes=('accidentes','sum'),
        media_accidentes_dia=('accidentes','mean'),mediana_accidentes_dia=('accidentes','median'),
        con_lesiones=('con_lesiones','sum'),lesion_conocida=('lesion_conocida','sum')).reindex(WEATHER)
    byweather['proporcion_con_lesiones']=byweather.con_lesiones/byweather.lesion_conocida
    # Cluster bootstrap: resample whole days within each weather category, not individual crashes.
    rng=np.random.default_rng(SEED)
    boot={}
    for g in WEATHER:
        z=daily.loc[daily.grupo_meteo.eq(g),['con_lesiones','lesion_conocida']].to_numpy(float)
        ix=rng.integers(0,len(z),(5000,len(z)))
        samples=z[ix].sum(axis=1)
        boot[g]=samples[:,0]/samples[:,1]
        byweather.loc[g,'ic95_inferior'],byweather.loc[g,'ic95_superior']=np.quantile(boot[g],[.025,.975])
    diff=boot['Precipitacion']-boot['Seco']
    # Sensitivity: weekly moving blocks retain some serial dependence across days.
    block_diffs=[]
    for _ in range(3000):
        starts=rng.integers(0,len(daily),int(np.ceil(len(daily)/7)))
        ix=((starts[:,None]+np.arange(7))%len(daily)).ravel()[:len(daily)]
        b=daily.iloc[ix]
        a=b.loc[b.grupo_meteo.eq('Precipitacion')]
        z=b.loc[b.grupo_meteo.eq('Seco')]
        if a.lesion_conocida.sum()>0 and z.lesion_conocida.sum()>0:
            block_diffs.append(a.con_lesiones.sum()/a.lesion_conocida.sum()-z.con_lesiones.sum()/z.lesion_conocida.sum())
    save_table(byweather.reset_index(),'meteorologia_resumen')
    kw=stats.kruskal(*(daily.loc[daily.grupo_meteo.eq(g),'accidentes'] for g in WEATHER))
    sp=stats.spearmanr(daily.precipitation_sum,daily.accidentes)
    adjusted=multipletests([kw.pvalue,sp.pvalue],method='holm')[1]
    exploratory=pd.DataFrame([
        ['Kruskal-Wallis: accidentes/día por meteorología',kw.statistic,kw.pvalue,adjusted[0]],
        ['Spearman: precipitación y accidentes/día',sp.statistic,sp.pvalue,adjusted[1]]],
        columns=['contraste','estadistico','p_sin_ajuste','p_holm'])
    save_table(exploratory,'contrastes_exploratorios')
    # Quasi-Poisson-style inference: Poisson mean with robust HAC covariance for overdispersion/serial dependence.
    formula="accidentes ~ C(grupo_meteo, Treatment(reference='Seco')) + C(mes) + C(dia_semana_num) + temperature_2m_mean + wind_speed_10m_max"
    model=smf.glm(formula,daily,family=sm.families.Poisson()).fit(cov_type='HAC',cov_kwds={'maxlags':7})
    ci=model.conf_int()
    reg=pd.DataFrame({'termino':model.params.index,'coef_log':model.params.values,
        'razon_recuentos':np.exp(model.params.values),'ic95_inferior':np.exp(ci[0].values),
        'ic95_superior':np.exp(ci[1].values),'p':model.pvalues.values})
    weather_mask=reg.termino.str.contains('grupo_meteo')
    reg.loc[weather_mask,'p_holm_meteo']=multipletests(reg.loc[weather_mask,'p'],method='holm')[1]
    save_table(reg,'modelo_recuentos_diarios')
    (ROOT/'reports/modelo_estadistico.txt').write_text(model.summary().as_text(),encoding='utf-8')
    # Check sensitivity to the chosen rain threshold and lag length.
    sensitivity=[]
    for threshold,lag in [(1.,3),(1.,14),(.1,7)]:
        ds=daily.copy(); ds['grupo_meteo']=meteo_group(ds,threshold)
        fit=smf.glm(formula,ds,family=sm.families.Poisson()).fit(cov_type='HAC',cov_kwds={'maxlags':lag})
        for term in fit.params.index:
            if 'grupo_meteo' in term:
                sensitivity.append([threshold,lag,term,np.exp(fit.params[term]),*np.exp(fit.conf_int().loc[term]),fit.pvalues[term]])
    save_table(pd.DataFrame(sensitivity,columns=['umbral_precipitacion_mm','retardos_HAC','termino','razon_recuentos','ic95_inferior','ic95_superior','p']),'sensibilidad')
    st={'dias':len(daily),'dispersion_pearson':float(model.pearson_chi2/model.df_resid),
        'autocorrelacion_residuos_lag1':float(pd.Series(model.resid_pearson).autocorr()),
        'modelo_convergencia':bool(model.converged),
        'diferencia_proporcion_precipitacion_seco':float(byweather.loc['Precipitacion','proporcion_con_lesiones']-byweather.loc['Seco','proporcion_con_lesiones']),
        'diferencia_ic95':np.quantile(diff,[.025,.975]).tolist(),
        'diferencia_ic95_bloques_7dias':np.quantile(block_diffs,[.025,.975]).tolist(),
        'modelo_meteo':reg.loc[weather_mask].to_dict('records'),
        'contrastes':exploratory.to_dict('records')}
    (ROOT/'reports/estadistica.json').write_text(json.dumps(st,indent=2,ensure_ascii=False),encoding='utf-8')
    return daily,byweather,st

def plots_and_tables(d,daily,weather):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
        'figure.facecolor':'white','axes.titleweight':'bold','axes.labelcolor':'#334155','savefig.dpi':160})
    def finish(name):
        plt.figtext(.01,.005,'Fuentes: City of Chicago; Open-Meteo (ERA5). Elaboración propia. 2024.',fontsize=7,color='#64748B')
        plt.tight_layout(rect=[0,.03,1,1]); plt.savefig(FIG/f'{name}.png'); plt.close()
    monthly=summarize(d,['mes']); save_table(monthly,'por_mes')
    hourly=summarize(d,['hora']); save_table(hourly,'por_hora')
    weekday=summarize(d,['dia_semana_num','dia_semana']);save_table(weekday,'por_dia_semana')
    streets=summarize(d,['via']).sort_values('accidentes',ascending=False);save_table(streets,'por_via')
    save_table(d.select_dtypes('number').describe(percentiles=[.01,.25,.5,.75,.99]).T.reset_index(names='variable'),'descriptivos')
    cats=[]
    for col in ['weather_condition','lighting_condition','roadway_surface_cond','first_crash_type','prim_contributory_cause','most_severe_injury']:
        f=d[col].value_counts(dropna=False).rename_axis('categoria').reset_index(name='n');f.insert(0,'variable',col);cats.append(f)
    save_table(pd.concat(cats,ignore_index=True),'frecuencias_categoricas')
    plt.figure(figsize=(9,4)); plt.plot(MONTHS,monthly.accidentes,marker='o',color='#2457A7');plt.title('Accidentes registrados por mes');plt.ylabel('Accidentes');finish('01_evolucion_mensual')
    plt.figure(figsize=(9,4));plt.bar(hourly.hora,hourly.accidentes,color='#2457A7');plt.xticks(range(0,24,2));plt.title('Accidentes por hora local');plt.xlabel('Hora');plt.ylabel('Accidentes');finish('02_horarios')
    heat=pd.crosstab(d.dia_semana_num,d.hora).reindex(index=range(7),columns=range(24),fill_value=0)
    save_table(heat.reset_index(),'matriz_dia_hora')
    plt.figure(figsize=(11,4));plt.imshow(heat,aspect='auto',cmap='Blues');plt.yticks(range(7),DAYS);plt.xticks(range(24));plt.colorbar(label='Accidentes');plt.title('Concentración por día de la semana y hora');plt.xlabel('Hora local');finish('03_dia_hora')
    plt.figure(figsize=(9,5));z=streets.head(10).iloc[::-1];plt.barh(z.via,z.accidentes,color='#2457A7');plt.title('Diez vías con más accidentes registrados');plt.xlabel('Accidentes; no ajustado por longitud ni tráfico');finish('04_vias')
    plt.figure(figsize=(8,4));plt.boxplot([daily.loc[daily.grupo_meteo.eq(g),'accidentes'] for g in WEATHER],tick_labels=WEATHER,showmeans=True);plt.title('Distribución de accidentes diarios por meteorología');plt.ylabel('Accidentes por día');finish('05_meteorologia_diaria')
    plt.figure(figsize=(8,4));p=weather.proporcion_con_lesiones*100
    plt.errorbar(WEATHER,p,yerr=[p-weather.ic95_inferior*100,weather.ic95_superior*100-p],fmt='o',capsize=7,color='#2457A7');plt.title('Accidentes con lesiones: proporción e IC del 95 %');plt.ylabel('% entre registros con lesiones conocidas');finish('06_lesiones_incertidumbre')
    plt.figure(figsize=(8,4));plt.scatter(daily.precipitation_sum,daily.accidentes,alpha=.55,color='#2457A7');plt.xlabel('Precipitación diaria (mm)');plt.ylabel('Accidentes por día');plt.title('Precipitación y accidentes diarios');finish('07_precipitacion')
    plt.figure(figsize=(9,4));z=d.first_crash_type.value_counts().head(8).iloc[::-1];plt.barh(z.index,z.values,color='#2457A7');plt.title('Tipos de primera colisión más frecuentes');plt.xlabel('Accidentes');finish('08_tipo_colision')
    corr=daily[['accidentes','con_lesiones','temperature_2m_mean','precipitation_sum','snowfall_sum','wind_speed_10m_max']].corr(method='spearman')
    save_table(corr.reset_index(),'correlaciones_diarias_spearman')
    return streets

def export_dashboard(d,daily,streets):
    # Additive summaries; each dimension is a separate view, never sum views together.
    records=[]
    for dim,col in [('Hora','hora'),('Dia','dia_semana_num'),('Via','via'),('Total',None)]:
        t=d.copy() if col is None else d
        if dim=='Via':
            t=d.copy()
            t['via']=t.via.where(t.via.isin(streets.via.head(10)), 'OTRAS VIAS')
        if col is None: t=t.assign(categoria='Total');col='categoria'
        a=summarize(t,['mes','grupo_meteo',col]).rename(columns={col:'categoria'})
        a['dimension']=dim
        a['categoria']=a.categoria.astype(str)
        records.extend(a[['mes','grupo_meteo','dimension','categoria','accidentes','con_lesiones','lesion_conocida','personas_lesionadas','fallecidos']].to_dict('records'))
    summary=pd.DataFrame(records)
    summary.to_csv(PROC/'resumen_dashboard.csv',index=False)
    weather_days=daily.groupby(['mes','grupo_meteo']).size().reset_index(name='dias')
    weather_days.to_csv(PROC/'dias_dashboard.csv',index=False)
    payload={'headers':summary.columns.tolist(),'rows':summary.astype(object).where(summary.notna(),None).values.tolist(),
        'days':weather_days.values.tolist(),'top_streets':streets.via.head(10).tolist(),
        'checks':[]}
    for month,group in [('Todos','Todos'),('01','Todos'),('Todos','Nieve'),('07','Precipitacion'),('07','Nieve')]:
        f=d
        wd=daily
        if month!='Todos':f=f[f.mes.eq(int(month))];wd=wd[wd.mes.eq(int(month))]
        if group!='Todos':f=f[f.grupo_meteo.eq(group)];wd=wd[wd.grupo_meteo.eq(group)]
        payload['checks'].append({'month':month,'group':group,'n':len(f),'injured':float(f.injuries_total.sum()),
            'with_injury':float(f.con_lesiones.sum()),'known':int(f.lesion_conocida.sum()),'days':len(wd)})
    (PROC/'dashboard.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def dictionary(d):
    meta=json.loads((RAW/'chicago_metadata.json').read_text())
    descriptions={c['fieldName']:c.get('description','') for c in meta['columns']}
    derived={
      'fecha':'Fecha local del accidente. Clave de unión con meteorología diaria.',
      'mes':'Mes local (1-12), derivado de crash_date.', 'hora':'Hora local (0-23), derivada de crash_date.',
      'dia_semana_num':'Lunes=0 a domingo=6. Recalculado para evitar confundir codificación original.',
      'dia_semana':'Nombre del día local.', 'via':'Dirección y nombre de vía. No representa un tramo homogéneo.',
      'con_lesiones':'1 si injuries_total>0, 0 si es cero; ausente si se desconoce. Incluye lesiones mortales.',
      'con_lesion_grave_o_mortal':'1 si lesiones incapacitantes + mortales >0; ausente si faltan componentes.',
      'lesion_conocida':'1 cuando injuries_total no es ausente.',
      'horas_hasta_aviso':'Diferencia aviso policial - accidente, en horas. Diferencias negativas pasan a ausente.',
      'temperature_2m_mean':'Temperatura media diaria a 2 m (°C), ERA5 vía Open-Meteo.',
      'temperature_2m_max':'Temperatura máxima diaria a 2 m (°C).',
      'temperature_2m_min':'Temperatura mínima diaria a 2 m (°C).',
      'precipitation_sum':'Precipitación total diaria (mm), incluye equivalente en agua de nieve.',
      'rain_sum':'Lluvia diaria (mm).', 'snowfall_sum':'Nevada diaria (cm). No es profundidad de nieve acumulada.',
      'wind_speed_10m_max':'Velocidad máxima diaria del viento a 10 m (km/h).',
      'wind_gusts_10m_max':'Racha máxima diaria (km/h).',
      'grupo_meteo':'Nieve si snowfall_sum>=0.1 cm; si no, Precipitacion si precipitation_sum>=1 mm; resto Seco. No indica tiempo exacto del accidente.'}
    data=[]
    for c in d.columns:
        source='City of Chicago' if c in COLS else 'Open-Meteo / ERA5' if c in derived and c not in ['fecha','mes','hora','dia_semana_num','dia_semana','via','con_lesiones','con_lesion_grave_o_mortal','lesion_conocida','horas_hasta_aviso','grupo_meteo'] else 'Derivada'
        data.append([c,str(d[c].dtype),source,derived.get(c,descriptions.get(c,''))])
    pd.DataFrame(data,columns=['variable','tipo','origen','definicion']).to_csv(ROOT/'docs/diccionario_datos.csv',index=False)

def main():
    for p in [PROC,TABLES,FIG,ROOT/'docs']: p.mkdir(parents=True,exist_ok=True)
    d,w,qa=clean_join()
    print('Unión validada:',qa['filas_finales'],qa['columnas_finales'],flush=True)
    daily,weather,st=stats_analysis(d,w)
    streets=plots_and_tables(d,daily,weather)
    export_dashboard(d,daily,streets);dictionary(d)
    overview={'accidentes':len(d),'columnas':len(d.columns),'con_lesiones':int(d.con_lesiones.sum()),
      'lesion_conocida':int(d.lesion_conocida.sum()),'personas_lesionadas_incluye_mortales':int(d.injuries_total.sum()),
      'fallecidos':int(d.injuries_fatal.sum()),'mes_max':int(d.mes.value_counts().idxmax()),
      'hora_max':int(d.hora.value_counts().idxmax()),'via_max':str(streets.iloc[0].via),
      'meteo':weather.reset_index().to_dict('records')}
    (ROOT/'reports/resumen.json').write_text(json.dumps(overview,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(overview,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
