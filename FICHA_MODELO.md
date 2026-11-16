# Ficha del modelo: scoring de «Paga en plazos»

| Campo | Valor |
|---|---|
| Uso previsto | Decidir en el checkout si se concede un pago en 3, 6 o 12 cuotas (150 a 2.000 €) |
| Uso no previsto | Préstamos a vendedores, tarjetas, límites de crédito revolvente |
| Clasificación | Sistema de alto riesgo (Reglamento UE 2024/1689, anexo III, 5.b) |
| Variable objetivo | Impago de 90 días en los 6 primeros meses (EBA/GL/2016/07). La 1.1.0 se entrena con FPD a 30 días y se escala a PD |
| Algoritmo | Tramos con WoE y regresión logística (IRLS) |
| Variables | Antigüedad, compras 12 m, impagos previos, importe, DTI, edad, dispositivo nuevo, score de fraude, plazo, devoluciones, sin historial, ingresos; canal de creadores desde la 1.1.0 |
| Variables excluidas | Sexo, nacionalidad, código postal fino |
| Reglas previas | Dos o más impagos en buró, DTI ≥ 60 %, bloqueo del motor de fraude |
| Decisión | A-C aprobar, D contraoferta, E (PD ≥ 8 %) rechazar con motivos |
| Rendimiento 1.0.0 | Gini 0,521 y KS 0,400 fuera de tiempo; PD media 2,08 % frente a impago 2,04 % |
| Monitorización | PSI y CSI mensuales; impago implícito por FPD por canal; Gini trimestral; p95 de latencia |
| Supervisión humana | Revisión en 48 horas a petición del cliente; comité de modelos para cada release |
| Limitaciones conocidas | La edad produce una brecha de aprobación en menores de 25; la 1.1.0 ordena peor la cartera antigua (Gini 0,40 frente a 0,47) |
| Datos | Dataset sintético reproducible (`bnpl/simulacion.py`, semilla 2026) |
