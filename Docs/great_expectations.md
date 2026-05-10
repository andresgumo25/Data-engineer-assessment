Great Expectations (skeleton)

Este documento explica cómo integrar Great Expectations (GE) o una alternativa ligera para checks de calidad de datos.

Opciones:
1) Great Expectations (completo):
   - pip install great_expectations
   - Inicializar: great_expectations init
   - Crear un datasource que apunte a la DB Postgres (o usar el connector SQLAlchemy)
   - Crear expectation suites y validar tablas (companies, jobs, skills, job_skills).

2) Alternativa ligera con Pandera (incluida en requirements.txt):
   - Usar tools/great_expectations/run_basic_checks.py que ejecuta checks SQL simples (no requiere GE)
   - Recomendado para CI rápido y como primer paso antes de invertir en GE completo.

Ejecutar checks básicos (ejemplo):
- python tools/great_expectations/run_basic_checks.py

Extensión sugerida:
- Añadir un job en CI que ejecute las suites de Great Expectations y publique los resultados.
- Almacenar artefactos (validations) en el run artifacts o en S3.

Nota: Great Expectations añade mucha funcionalidad (data docs, validators, batch requests). Si querés, puedo inicializar un proyecto GE mínimo y añadir una suite de ejemplo para la tabla `jobs`.