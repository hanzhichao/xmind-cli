import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List

from .models import Workbook, Sheet, Topic


import hashlib
import os

class XMindBuilder:
    @staticmethod
    def _build_topic(topic: Topic, resources_map: Dict[str, bytes]) -> Dict[str, Any]:
        data = {
            "id": topic.id,
            "title": topic.title,
        }
        
        # Add preserved attributes
        for k, v in topic.attributes.items():
            if k not in data:
                data[k] = v
                
        if topic.structure_class:
            data["structureClass"] = topic.structure_class
            
        if topic.style_properties:
            data["style"] = {
                "id": f"{topic.id}-style",
                "properties": topic.style_properties
            }
            
        if topic.labels:
            data["labels"] = topic.labels
        if topic.markers:
            data["markers"] = topic.markers
        if topic.notes:
            data["notes"] = topic.notes
        if topic.href:
            data["href"] = topic.href
        if topic.extensions:
            data["extensions"] = topic.extensions
            
        if topic.image_path and os.path.exists(topic.image_path):
            with open(topic.image_path, "rb") as f:
                img_bytes = f.read()
            img_hash = hashlib.sha256(img_bytes).hexdigest()
            # Try to get extension, fallback to png
            ext = os.path.splitext(topic.image_path)[1].lower()
            if not ext:
                ext = ".png"
            res_path = f"resources/{img_hash}{ext}"
            resources_map[res_path] = img_bytes
            
            data["image"] = {"src": f"xap:{res_path}"}
                
        if topic.children:
            data["children"] = {
                "attached": [XMindBuilder._build_topic(child, resources_map) for child in topic.children]
            }
            
        return data

    @staticmethod
    def _build_sheet(sheet: Sheet, resources_map: Dict[str, bytes]) -> Dict[str, Any]:
        data = {
            "id": sheet.id,
            "title": sheet.title,
            "rootTopic": XMindBuilder._build_topic(sheet.root_topic, resources_map)
        }
        
        if sheet.theme:
            data["theme"] = sheet.theme
            
        if sheet.style_properties:
            data["style"] = {
                "id": f"{sheet.id}-style",
                "properties": sheet.style_properties
            }
            
        if sheet.compact_layout:
            data["compactLayoutModeLevel"] = sheet.compact_layout
            
        # Add preserved attributes
        for k, v in sheet.attributes.items():
            if k not in data:
                data[k] = v
                
        return data

    @classmethod
    def build_file(cls, workbook: Workbook, output_path: str | Path):
        output_path = Path(output_path)
        
        resources_map: Dict[str, bytes] = {}
        content_data = [cls._build_sheet(sheet, resources_map) for sheet in workbook.sheets]
        
        manifest_data = {
            "file-entries": {
                "content.json": {},
                "metadata.json": {}
            }
        }
        
        for res_path in resources_map:
            manifest_data["file-entries"][res_path] = {}
        
        metadata_data = {
            "creator": {
                "name": "xmind-cli"
            }
        }
        
        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('content.json', json.dumps(content_data, ensure_ascii=False).encode('utf-8'))
            z.writestr('manifest.json', json.dumps(manifest_data, ensure_ascii=False).encode('utf-8'))
            z.writestr('metadata.json', json.dumps(metadata_data, ensure_ascii=False).encode('utf-8'))
            
            for res_path, img_bytes in resources_map.items():
                z.writestr(res_path, img_bytes)

