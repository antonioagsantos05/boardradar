"""Compatibility entry point for the current v3 source validator."""
import json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
spec=spec_from_file_location('poc_validation',Path(__file__).with_name('validate-poc-data.py'))
module=module_from_spec(spec);spec.loader.exec_module(module)
print(json.dumps(module.validate(),ensure_ascii=False,indent=2))
