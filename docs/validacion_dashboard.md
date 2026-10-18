# Validación de la entrega

Revisión: 6 de octubre de 2026.

## Datos

Las ocho pruebas de `tests/test_integridad.py` pasan. Comprueban claves únicas y mínimos, huellas de los originales, calendario y unión, umbrales meteorológicos, lesiones desconocidas reconciliación de los resúmenes, fidelidad del CSV meteorológico y conservación de sus ocho variables. El conjunto final conserva 112.057 accidentes y 55 columnas.

La reproducción completa desde los originales coincide en los 21 CSV de datos y tablas, los tres archivos de resultados JSON y los ocho gráficos. Se comprobaron las 55 columnas del conjunto final. La auditoría adicional superó 27 controles. Esto comprueba integridad y coherencia; no permite excluir errores existentes en los registros del proveedor.

## Dashboard

Se han recalculado las 52 combinaciones de los selectores: año completo o cada uno de los 12 meses, cruzados con Todos, Seco, Precipitacion y Nieve.

Los controles se obtuvieron de forma independiente a partir del CSV completo y del calendario meteorológico. En cada combinación se comprobaron accidentes, accidentes con lesiones, registros con lesiones conocidas, personas lesionadas, fallecidos, días y ambas tasas. También se compararon los 12 valores mensuales, los 24 horarios, los siete días de semana y las cifras de las diez vías. Todos coinciden.

| Selección | Accidentes | Personas con lesiones | Días |
|---|---:|---:|---:|
| Año completo, todos | 112.057 | 25.706 | 366 |
| Enero, todos | 8.235 | 1.559 | 31 |
| Año completo, nieve | 7.650 | 1.361 | 25 |
| Julio, precipitación | 3.986 | 985 | 13 |
| Julio, nieve | 0 | 0 | 0 |

Sin denominador, el porcentaje y la media muestran `n.a.`. El porcentaje anual es 18.443 / 111.808 = 16,4952 %, mostrado con un decimal en el dashboard.

Se han revisado las cuatro hojas. El archivo guardado conserva cuatro gráficos nativos vinculados a fórmulas, dos desplegables y ninguna celda con error de cálculo almacenado. Las tres gráficas de barras tienen el eje de valores comenzando en cero. Se ha vuelto a importar el archivo exportado y se ha comprobado de nuevo el total y la respuesta al filtro sin datos.

Las pruebas de recálculo y las vistas se realizaron con un motor de cálculo independiente. No se ha comprobado el archivo en Microsoft Excel de escritorio en esta revisión. Para verificarlo allí, abrirlo con cálculo automático, comprobar 112.057 accidentes sin filtros y seleccionar julio y Nieve: deben aparecer cero accidentes y `n.a.` en las tasas.

## Informe y publicación

El PDF se ha renderizado y revisado visualmente. Los encabezados se mantienen junto al texto que introducen. Los datos originales no se han modificado.

El paquete local está preparado. La publicación en GitHub y el envío a ThePower no se han realizado en esta revisión.
