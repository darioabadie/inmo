# Plan de Migración Arquitectónica Incremental

Este plan está diseñado para migrar la base de código de `inmobiliaria` hacia una arquitectura modular, escalable y mantenible. Cada paso puede ser ejecutado de forma independiente y secuencial por una LLM o desarrollador.

---

## 1. Preparación y limpieza
- [ ] Eliminar carpetas vacías o sin uso (ej: `pagos/`).
- [ ] Crear carpeta principal `inmobiliaria/` si no existe.
- [ ] Mover `app.py` a `inmobiliaria/main.py`.

## 2. Modularización inicial
- [ ] Crear archivos:
    - `inmobiliaria/models.py` (entidades y dataclasses)
    - `inmobiliaria/services/` (carpeta para lógica de negocio y acceso externo)
    - `inmobiliaria/utils.py` (funciones auxiliares)
    - `inmobiliaria/config.py` (constantes y parámetros)
- [ ] Actualizar imports en `main.py` para reflejar la nueva estructura.

## 3. Separación de responsabilidades
- [ ] Extraer funciones de acceso a Google Sheets a `services/google_sheets.py`.
- [ ] Extraer funciones de inflación y cálculos a `services/inflation.py` y `services/calculations.py`.
- [ ] Definir entidades principales en `models.py` usando dataclasses o clases tipadas.

## 4. Refactorización del flujo principal
- [ ] Limpiar `main.py` para que sólo orqueste el flujo, delegando lógica a servicios y modelos.
- [ ] Documentar con docstrings y comentarios cada módulo y función.

## 5. Actualización de tests
- [ ] Reubicar y actualizar tests para reflejar la nueva estructura.
- [ ] Crear tests unitarios para cada módulo nuevo.

## 6. Documentación
- [ ] Actualizar `README.md` con la nueva estructura y el flujo de ejecución.
- [ ] Documentar el propósito de cada módulo y carpeta.

## 7. Validación incremental
- [ ] Validar la funcionalidad tras cada paso usando los tests existentes.
- [ ] Corregir errores y actualizar dependencias según sea necesario.

---

**Notas:**
- Cada paso puede ser ejecutado y validado de forma independiente.
- Se recomienda usar control de versiones (git) y realizar commits por cada paso.
- Mantener la compatibilidad funcional en todo momento.

---

Este plan está optimizado para ser interpretado y ejecutado por una LLM o desarrollador humano, permitiendo una migración segura y ordenada.
