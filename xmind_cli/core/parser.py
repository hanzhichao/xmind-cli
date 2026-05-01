import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List

from .models import Workbook, Sheet, Topic


class XMindParser:
    @staticmethod
    def _parse_topic(data: Dict[str, Any]) -> Topic:
        title = data.get("title", "")
        topic_id = data.get("id", "")
        topic = Topic(title=title, id=topic_id)
        
        children_data = data.get("children", {})
        if isinstance(children_data, dict):
            # XMind ZEN structure: {"attached": [ ... ]}
            attached_children = children_data.get("attached", [])
            for child_data in attached_children:
                topic.children.append(XMindParser._parse_topic(child_data))
        elif isinstance(children_data, list):
            # Fallback or simplified structure
            for child_data in children_data:
                topic.children.append(XMindParser._parse_topic(child_data))
                
        # Store raw data in attributes for things we might have missed
        topic.attributes = {k: v for k, v in data.items() if k not in ("title", "id", "children")}
        return topic

    @staticmethod
    def _parse_sheet(data: Dict[str, Any]) -> Sheet:
        title = data.get("title", "Map")
        sheet_id = data.get("id", "")
        root_topic_data = data.get("rootTopic", {})
        root_topic = XMindParser._parse_topic(root_topic_data)
        
        sheet = Sheet(title=title, id=sheet_id, root_topic=root_topic)
        sheet.attributes = {k: v for k, v in data.items() if k not in ("title", "id", "rootTopic")}
        return sheet

    @classmethod
    def parse_file(cls, file_path: str | Path) -> Workbook:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'content.json' in z.namelist():
                with z.open('content.json') as f:
                    content_data = json.loads(f.read().decode('utf-8'))
            else:
                raise ValueError("Only modern XMind ZEN files (content.json) are supported.")
                
        workbook = Workbook()
        if isinstance(content_data, list):
            for sheet_data in content_data:
                workbook.sheets.append(cls._parse_sheet(sheet_data))
                
        return workbook

