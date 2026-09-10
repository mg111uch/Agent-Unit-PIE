"""Export kernel unit-schema dataclasses to unit_schema.json.

Single source of truth: run `conda run -n myenv python
codebase/kernel/schemas/export_json.py` after dataclass changes. The
artifact is checked in and version-bumped only when dataclasses change.
Stdlib only.
"""
import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_VERSION = "1.0.0"
CLASSES = ("UnitIdentity", "UnitState", "UnitResources", "UnitTraits",
           "UnitBehavior", "UnitSignalRef", "UnitRelation", "UnitMemory",
           "UnitMetadata", "UnitSchema")


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "kernel_unit_schema", HERE / "unit_schema.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses need host module registered
    spec.loader.exec_module(mod)
    fields = {}
    for name in CLASSES:
        cls = getattr(mod, name)
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"{name} is not a dataclass")
        fields[name] = sorted(f.name for f in dataclasses.fields(cls))
    top = sorted(f.name for f in dataclasses.fields(mod.UnitSchema))
    artifact = {"schema_version": SCHEMA_VERSION,
                "fields": dict(sorted(fields.items())),
                "required": top}
    out = HERE / "unit_schema.json"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out} schema_version={SCHEMA_VERSION}")


if __name__ == "__main__":
    main()
