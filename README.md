# uafeg-baseline

> **Este repositorio implementa unicamente los baselines convencionales de la
> tesis "Grafos de evidencia multimodal conscientes de incertidumbre para la
> verificacion robusta de reclamos de seguros vehiculares". NO contiene la
> contribucion basada en Evidence Graph (GAT/GATv2, reliability-gated message
> passing, agentes, RL, entity/collusion graph, etc.).**

Estos baselines representan como se puede resolver el problema hoy con
tecnicas existentes (NLI sobre la narrativa + deteccion/segmentacion de danio
sobre la imagen + fusion mediante reglas o un clasificador convencional),
para poder comparar objetivamente contra la contribucion de la tesis en una
etapa posterior.

## Baselines

| Nombre | Descripcion | Fase | Estado |
|--------|-------------|------|--------|
| B0 | Rule engine determinista (reglas configurables, sin grafos) | 4 | pendiente |
| B1 | Solo narrativa (NLI) | 2 | pendiente |
| B2 | Solo evidencia visual (deteccion/segmentacion de danio) | 3 | pendiente |
| B3 | Solo forense (cuando el modelo este disponible) | 8 | pendiente (opcional) |
| B4 | Late fusion (concatenacion de features + clasificador) | 5 | pendiente |

## Estado del proyecto

- **FASE 1 (repo + entorno + schemas + dataset manifest + tests): implementada.**
- FASE 2-8: estructura de carpetas y archivos creada como stubs (ver
  docstring de un lineas en cada archivo), implementacion pendiente.

## Salida del baseline

Cada instancia de verificacion (`Claim`) se clasifica en una de tres
etiquetas: `SUPPORTED`, `SUSPICIOUS`, `INSUFFICIENT`.

## Entorno

- Python 3.11 (requerido por compatibilidad con PyTorch/Transformers/Ultralytics).
- Los comandos de este README son para **bash** (Linux/macOS). Si trabajas en
  Windows PowerShell, el equivalente es el mismo `python`/`pip`/`pytest` pero
  con `.venv\Scripts\Activate.ps1` para activar el entorno virtual.

### Setup

```bash
cd uafeg-baseline
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

PowerShell equivalente para activar el entorno (una vez creado el venv):

```powershell
.venv\Scripts\Activate.ps1
```

### Dataset

Ver `data/README.md` para instrucciones de descarga manual y ubicacion del
dataset de Humans in the Loop.

### Tests

```bash
pytest -v
```

> Nota (entornos con ROS2 sourced, p. ej. `/opt/ros/humble/setup.bash` en
> `~/.bashrc`): si `pytest` falla con `ModuleNotFoundError: No module named
> 'lark'` al arrancar, es porque `$PYTHONPATH` apunta a paquetes de ROS2 que
> registran un plugin de pytest (`launch_testing`) y pytest lo autocarga
> aunque no tenga nada que ver con este proyecto. Solucion: `unset
> PYTHONPATH` en la shell (o `env -u PYTHONPATH pytest -v`) antes de correr
> los tests dentro del venv de este proyecto.

### Entrenamiento / evaluacion / demo

Se documentaran en el README a medida que se completen las fases 2-7.

## Reproducibilidad

- Seed global y proporciones de split en `configs/baseline.yaml`.
- Taxonomia canonica de danio y mapping del dataset en `configs/labels.yaml`.
- `requirements.txt` versionado; tras validar el entorno, generar
  `requirements.lock` con `pip freeze > requirements.lock` (no se versiona en git).
- Ni datasets ni pesos de modelos se versionan en git (ver `.gitignore`).
