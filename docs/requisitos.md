# Matriz de requisitos del proyecto

Revisión frente al enunciado y a la guía de README facilitados. Fecha: 6 de octubre de 2026.

| Requisito de ThePower | Estado y evidencia |
|---|---|
| Dos conjuntos de dos fuentes distintas, en formato tabular | Verificado: Chicago CSV y Open-Meteo CSV en data/raw. El segundo es una exportación fiel del JSON original, también incluido, sin limpieza ni cambios de valores. |
| Originales incluidos | Verificado: data/raw, URL y SHA-256 en manifest.json; unidades y huellas de la exportación meteorológica en exportacion_csv_meteo.json. |
| Unión de las fuentes | Verificado: src/analisis.py, unión muchos a uno por fecha; ninguna fila multiplicada ni sin meteorología. |
| Al menos 50.000 filas y 20 columnas | Verificado: 112.057 filas y 55 columnas; reports/calidad.json y diccionario. |
| Limpieza y transformación | Verificado: tipos, fechas, claves, nulos, lesiones, coordenadas y reglas documentadas. |
| Python y Pandas | Verificado: código ejecutado de nuevo desde los originales; resultados reproducidos. |
| Visual Studio Code | Pendiente de confirmar el uso efectivo del editor. El README contiene instrucciones; estas no acreditan que se haya utilizado. |
| Análisis exhaustivo | Verificado: descripción temporal, territorial, meteorológica y de lesiones; ocho figuras, contrastes, modelo ajustado, intervalos y sensibilidad. |
| Dashboard operativo | Verificado mediante recálculo independiente de 52 combinaciones, fórmulas y cuatro gráficos. Pendiente de prueba final en Excel de escritorio. |
| Informe explicativo | Verificado: reports/informe.md y PDF con objetivos, metodología, resultados, conclusiones y limitaciones. |
| README conforme a la guía | Verificado: título, descripción, estructura, instalación, reproducción, resultados, próximos pasos, contribuciones, responsable y fuentes; informe incorporado. |
| Organización del repositorio | Verificado: data, src, reports, dashboard, docs y tests. |
| Publicación en GitHub | Pendiente de revisión y autorización para publicar. |
| Programa obligatorio y proyectos previos aprobados | Pendiente de confirmación académica del alumno; no verificable con estos archivos. |
| Entrega en ThePower | Pendiente de publicación, revisión y autorización para enviar. |

No se han añadido como requisitos una defensa oral, presentación o modelo predictivo: no aparecían en el material facilitado. No se considera completada la entrega mientras existan pasos pendientes.
