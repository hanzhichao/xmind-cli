import json
import pytest
from pathlib import Path
from xmind_cli.core.models import Topic, Sheet, Workbook
from xmind_cli.core.builder import XMindBuilder
from xmind_cli.core.parser import XMindParser
from xmind_cli.converters.markdown import MarkdownConverter

def test_models_to_dict():
    root = Topic(title="Root")
    child = Topic(title="Child")
    root.children.append(child)
    root.labels = ["test"]
    root.href = "https://example.com"
    
    data = root.to_dict()
    assert data["title"] == "Root"
    assert len(data["children"]) == 1
    assert data["labels"] == ["test"]
    assert data["href"] == "https://example.com"

def test_markdown_advanced_parsing():
    md = """---
xmind:
  skeleton: logic-right
  compact: true
---
# Root
## **Bold Node**
  Tags: tag1, tag2
  Markers: priority-1
  > This is a rich note
## [Link Node](https://google.com)
## - [ ] Task Node
## FastAPI ![](./fast-api.png)
"""
    # Create a dummy image for parsing test
    img_path = Path("fast-api.png")
    img_path.write_text("dummy")
    
    try:
        workbook = MarkdownConverter.to_xmind(md)
        sheet = workbook.sheets[0]
        root = sheet.root_topic
        
        assert root.title == "Root"
        assert sheet.attributes["xmind_config"]["skeleton"] == "logic-right"
        
        bold_node = root.children[0]
        assert bold_node.title == "Bold Node"
        assert bold_node.style_properties["fo:font-weight"] == "700"
        assert "tag1" in bold_node.labels
        assert bold_node.markers[0]["markerId"] == "priority-1"
        assert "rich note" in bold_node.notes["plain"]["content"]
        
        link_node = root.children[1]
        assert link_node.title == "Link Node"
        assert link_node.href == "https://google.com"
        
        task_node = root.children[2]
        assert task_node.extensions[0]["content"]["status"] == "todo"
        
        img_node = root.children[3]
        assert img_node.image_path == "./fast-api.png"
    finally:
        if img_path.exists():
            img_path.unlink()

def test_xmind_to_markdown():
    root = Topic(title="Root")
    child = Topic(title="Child 1")
    root.children.append(child)
    workbook = Workbook(sheets=[Sheet(title="Map", root_topic=root)])
    
    md = MarkdownConverter.from_xmind(workbook)
    assert "# Root" in md
    assert "## Child 1" in md

def test_builder_and_parser(tmp_path):
    root = Topic(title="Root Topic")
    root.children.append(Topic(title="Child Topic"))
    workbook = Workbook(sheets=[Sheet(title="Map 1", root_topic=root)])
    workbook.sheets[0].compact_layout = "Second"
    
    file_path = tmp_path / "test.xmind"
    XMindBuilder.build_file(workbook, file_path)
    
    assert file_path.exists()
    
    parsed_workbook = XMindParser.parse_file(file_path)
    assert len(parsed_workbook.sheets) == 1
    parsed_root = parsed_workbook.sheets[0].root_topic
    
    assert parsed_root.title == "Root Topic"
    assert len(parsed_root.children) == 1
    assert parsed_root.children[0].title == "Child Topic"
