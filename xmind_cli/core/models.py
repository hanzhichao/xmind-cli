import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


def generate_id() -> str:
    """Generate a random ID for XMind elements."""
    return str(uuid.uuid4())


@dataclass
class Topic:
    title: str
    id: str = field(default_factory=generate_id)
    children: List['Topic'] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Common styles
    structure_class: Optional[str] = None
    style_properties: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced metadata
    labels: List[str] = field(default_factory=list)
    markers: List[Dict[str, str]] = field(default_factory=list)
    notes: Optional[Dict[str, Any]] = None
    href: Optional[str] = None
    image_path: Optional[str] = None
    extensions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to internal dict representation."""
        data = {
            "title": self.title,
            "id": self.id,
            "children": [child.to_dict() for child in self.children],
            "attributes": self.attributes
        }
        if self.structure_class:
            data["structureClass"] = self.structure_class
        if self.style_properties:
            data["style"] = {"properties": self.style_properties}
            
        if self.labels:
            data["labels"] = self.labels
        if self.markers:
            data["markers"] = self.markers
        if self.notes:
            data["notes"] = self.notes
        if self.href:
            data["href"] = self.href
        if self.extensions:
            data["extensions"] = self.extensions
            
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Topic':
        """Create from internal dict representation."""
        children = [cls.from_dict(c) for c in data.get("children", [])]
        attributes = data.get("attributes", {})
        
        topic = cls(
            title=data.get("title", ""),
            id=data.get("id", generate_id()),
            children=children,
            attributes=attributes,
            structure_class=data.get("structureClass")
        )
        
        style_data = data.get("style", {})
        if isinstance(style_data, dict):
            topic.style_properties = style_data.get("properties", {})
            
        return topic


@dataclass
class Sheet:
    title: str
    root_topic: Topic
    id: str = field(default_factory=generate_id)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    theme: Dict[str, Any] = field(default_factory=dict)
    style_properties: Dict[str, Any] = field(default_factory=dict)
    compact_layout: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "title": self.title,
            "id": self.id,
            "root_topic": self.root_topic.to_dict(),
            "attributes": self.attributes
        }
        if self.theme:
            data["theme"] = self.theme
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sheet':
        root_topic_data = data.get("root_topic", {})
        return cls(
            title=data.get("title", "Map 1"),
            id=data.get("id", generate_id()),
            root_topic=Topic.from_dict(root_topic_data),
            attributes=data.get("attributes", {}),
            theme=data.get("theme", {})
        )


@dataclass
class Workbook:
    sheets: List[Sheet] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sheets": [sheet.to_dict() for sheet in self.sheets]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workbook':
        sheets = [Sheet.from_dict(s) for s in data.get("sheets", [])]
        return cls(sheets=sheets)
