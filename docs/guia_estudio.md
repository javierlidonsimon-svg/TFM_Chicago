# Cómo entender y explicar este proyecto

## Recorrido recomendado

1. Lee el resumen del informe y abre el Excel sin filtros. Localiza los 112.057 accidentes.
2. Selecciona enero y después Nieve. Comprueba que cambian los indicadores y las gráficas.
3. Abre src/analisis.py en Visual Studio Code y sigue clean_join: lectura, reglas y unión.
4. Comprueba que merge usa validate='many_to_one'. La meteorología tiene una fila por día.
5. Sigue stats_analysis: primero crea una serie diaria; después compara días y ajusta el modelo.
6. Ejecuta las pruebas. Lee el mensaje de cada prueba para saber qué verifica.

## Preguntas que debes poder responder

**¿Qué representa una fila?** En el conjunto final, un accidente registrado. En la serie estadística meteorológica, un día del calendario.

**¿Por qué dos fuentes?** Chicago aporta los incidentes y Open-Meteo aporta medidas meteorológicas independientes del juicio del agente. Se complementan mediante la fecha local.

**¿Cómo evitas duplicar accidentes al unir?** Exigiendo fechas únicas en meteorología y una relación muchos a uno. También verificamos recuentos y claves antes y después.

**¿Por qué no borras todos los registros incompletos?** Perderíamos información y podríamos introducir sesgos. Tratamos la ausencia según el indicador: una lesión desconocida no equivale a cero.

**¿Qué significa el 16,50 %?** Aproximadamente 18.443 accidentes con alguna lesión divididos por 111.808 accidentes cuyo total de lesiones está informado. No es el porcentaje de personas lesionadas.

**¿Qué es EDA?** Explorar calidad, distribuciones, frecuencias, relaciones y anomalías antes de interpretar resultados. Las tablas y gráficos permiten comprobarlo.

**¿Qué diferencia hay entre media y mediana?** La media suma accidentes diarios y divide por días. La mediana es el valor central; cambia menos ante días extremos.

**¿Por qué ajustar por mes y día de la semana?** El tráfico y la meteorología cambian con el calendario. Una comparación bruta puede mezclar esos patrones. El ajuste reduce algunas diferencias, sin eliminar toda confusión.

**¿Por qué usar 366 días en la estadística?** Los accidentes de un mismo día comparten la medida meteorológica. Tratar cada accidente como una medida independiente inflaría artificialmente el tamaño de la muestra.

**¿Qué significa una razón de recuentos de 1,126?** En el modelo ajustado, el recuento esperado se multiplica aproximadamente por 1,126 frente al grupo de referencia, manteniendo iguales las otras variables del modelo. No es una tasa por conductor ni una probabilidad individual.

**¿Qué significa que un intervalo contenga 1?** En una razón de recuentos, 1 representa ausencia de diferencia. El intervalo de precipitación es compatible con aumentos y reducciones pequeños.

**¿Qué son los errores robustos HAC?** Ajustan el cálculo de incertidumbre para permitir heterogeneidad y cierta correlación temporal. No corrigen sesgos del diseño ni confusión no medida.

**¿Qué es el bootstrap?** Repetir el cálculo sobre remuestreos de los datos para aproximar su variabilidad. Se remuestrean días, y también bloques de siete días, para respetar mejor cómo se agrupan los datos.

**¿Cuál es la principal limitación?** No conocemos cuántos vehículos circularon. Más accidentes puede significar más viajes, más riesgo o ambas cosas. La meteorología diaria de una cuadrícula tampoco describe cada lugar y hora.

**¿Qué recomendarías?** Revisar ubicaciones y horarios con alta carga registrada, añadir aforos y varios años, y contrastar la asociación con nieve antes de atribuir causas o diseñar medidas específicas.

## Ejercicio de comprobación

Selecciona julio y Nieve en el dashboard. Si no hay días que cumplan los filtros, deben aparecer cero accidentes y «n.a.» en los indicadores que requieren denominador. Explica por qué mostrar 0 % sería distinto de decir «no hay datos aplicables».

No memorices términos estadísticos sin entenderlos. Empieza por las tablas, relaciona cada cifra con sus registros y después lee el modelo como una comparación ajustada, no como prueba de causalidad.
