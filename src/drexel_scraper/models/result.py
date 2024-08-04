from dataclasses import dataclass

@dataclass
class Result:
    ok: bool
    errors: list[str]