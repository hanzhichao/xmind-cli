import json
from pathlib import Path

from ..core.models import Workbook


class JsonConverter:
    @staticmethod
    def to_xmind(json_content: str) -> Workbook:
        data = json.loads(json_content)
        return Workbook.from_dict(data)

    @staticmethod
    def from_xmind(workbook: Workbook) -> str:
        data = workbook.to_dict()
        return json.dumps(data, ensure_ascii=False, indent=2)
