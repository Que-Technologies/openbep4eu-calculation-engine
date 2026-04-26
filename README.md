# openbep4eu-calculation-engine

openbep4eu python core calculation engine for building energy performance workflows, including building-as-such models.

## Installation

### From source

```bash
git clone https://github.com/Que-Technologies/openbep4eu-calculation-engine
cd openbep4eu-calculation-engine
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Usage

```python
from openbep4eu.building_as_such.thermal_needs import run_energy_simulation
```

## Project structure

```
src/
└── openbep4eu/
    ├── building_as_such/
    │   ├── models/
    │   └── thermal_needs.py
    └── utils.py
```

## Development
```bash
python -m pip install -e .
```

## License

This project is licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.

You may obtain a copy of the License at:
https://www.mozilla.org/en-US/MPL/2.0/

## Status
Under active development.

