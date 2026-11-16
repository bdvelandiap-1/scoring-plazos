Feature: Decisión de «Paga en plazos» en el checkout

  Scenario: SLA de la API en streaming
    Given la API de scoring 1.x desplegada con dos réplicas
      And el tráfico de pico de Black Friday, cinco veces el de un día normal
    When el checkout pide una decisión
    Then el p95 de latencia es de 150 ms o menos y la disponibilidad del mes de 99,9 % o más
      And si no hay respuesta en 300 ms, el checkout oculta los plazos y la compra sigue

  Scenario: Mora NPL
    Given una versión candidata con su política de corte
    When se proyecta la cartera a seis meses con la PD calibrada de la última cosecha
    Then el NPL proyectado queda en el 4 % o menos
      And ningún grado aprobado tiene una PD calibrada media por encima del 8,6 % de equilibrio

  Scenario: EBITDA de la línea
    Given la cosecha del último mes puntuada con la versión vigente y con la candidata
    When se calcula comisión - pérdida esperada - fondeo - costes variables
    Then la candidata no empeora ese resultado en más de un 5 %
      And el EBITDA de la línea vuelve a ser positivo en los seis meses siguientes al despliegue

  Scenario: Churn tras contraoferta o rechazo
    Given un cliente que recibe una contraoferta o un rechazo
    When se le comunica la decisión en el checkout
    Then recibe hasta tres motivos comprensibles y, si es contraoferta, la alternativa concreta
      And el churn a 180 días de quienes reciben contraoferta no supera en más de 3 puntos al de los aprobados

  Scenario: Intervención humana
    Given un rechazo automático
    When el cliente pide revisión humana
    Then un analista de riesgos la resuelve en 48 horas como máximo
      And la decisión y su motivo quedan registrados con la versión del modelo (rsk_modelo_ver)

  Scenario: Disparador de hotfix
    Given dos lecturas mensuales seguidas con impago implícito / PD >= 1,50 en un canal
      And al menos 1.000 préstamos en cada cosecha
    When se cierra el segundo mes
    Then se abre una rama hotfix con la recalibración del canal
      And está en producción en tres días hábiles como máximo
    But un solo mes en rojo, como el de enero, no abre hotfix
