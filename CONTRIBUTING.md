# Contributing

Contributions are welcome through issues and pull requests.

## Development setup

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src/cmr_volume_analysis
```

Please add tests for behavioural changes. Test data should be synthetic, openly licensed, or otherwise suitable for public redistribution. Do not submit patient data or confidential institutional data.
