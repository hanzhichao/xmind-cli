import re
from pathlib import Path
from typing import List, Tuple, Optional

from ..core.models import Workbook, Sheet, Topic


class MarkdownConverter:
    @staticmethod
    @staticmethod
    def _parse_metadata(lines: List[str], topic: Topic):
        """Parse tasks, styling, metadata tags, and notes from a block of lines."""
        if not lines:
            return
            
        title_line = lines[0]
        meta_lines = lines[1:]
        
        # 1. Strip optional leading "- " or "* " if they accidentally got included (e.g. from headings)
        title_line = re.sub(r'^[-*+]\s+', '', title_line)
        
        # 2. Parse Task markers
        task_match = re.match(r'^\[([ xX])\]\s+(.*)', title_line)
        if task_match:
            status = task_match.group(1).lower()
            title_line = task_match.group(2)
            if status == 'x':
                topic.extensions.append({
                    "provider": "org.xmind.ui.task",
                    "content": {"status": "done"}
                })
            else:
                topic.extensions.append({
                    "provider": "org.xmind.ui.task",
                    "content": {"status": "todo"}
                })
                
        # 3. Parse inline images: ![Alt](URL)
        # MUST DO THIS BEFORE LINKS!
        img_match = re.search(r'!\[.*?\]\((.*?)\)', title_line)
        if img_match:
            topic.image_path = img_match.group(1)
            title_line = title_line[:img_match.start()] + title_line[img_match.end():]

        # 4. Parse inline links: [Text](URL)
        link_match = re.search(r'(?<!\!)\[(.*?)\]\((.*?)\)', title_line)
        if link_match:
            title_line = title_line[:link_match.start()] + link_match.group(1) + title_line[link_match.end():]
            topic.href = link_match.group(2)
            
        # 5. Parse styling: **, *, ~~ (Must wrap the whole remaining text or be extracted)
        title_stripped = title_line.strip()
        bold_match = re.match(r'^\*\*(.*?)\*\*$', title_stripped)
        italic_match = re.match(r'^\*(.*?)\*$', title_stripped)
        strike_match = re.match(r'^~~(.*?)~~$', title_stripped)
        
        if bold_match:
            title_line = bold_match.group(1)
            topic.style_properties["fo:font-weight"] = "700"
        elif italic_match:
            title_line = italic_match.group(1)
            topic.style_properties["fo:font-style"] = "italic"
        elif strike_match:
            title_line = strike_match.group(1)
            topic.style_properties["fo:text-decoration"] = "line-through"
            
        # Parse metadata from all lines except blockquotes
        non_note_lines = [title_line] + [l for l in meta_lines if not l.strip().startswith(">")]
        full_text = " ".join(non_note_lines)
        
        # Tags (case-insensitive, can be Tags: or Labels:)
        tags_match = re.search(r'(?i)\b(?:Tags|Labels):\s*(.*?)(?:;|$)', full_text)
        if tags_match:
            raw_tags = tags_match.group(1)
            topic.labels.extend([t.strip() for t in raw_tags.split(',') if t.strip()])
            title_line = re.sub(r'(?i)\b(?:Tags|Labels):\s*(.*?)(?:;|$)', '', title_line)
            
        # Marks / Markers
        marks_match = re.search(r'(?i)\b(?:Marks|Markers):\s*(.*?)(?:;|$)', full_text)
        if marks_match:
            raw_marks = marks_match.group(1)
            for m in raw_marks.split(','):
                if m.strip():
                    topic.markers.append({"markerId": m.strip()})
            title_line = re.sub(r'(?i)\b(?:Marks|Markers):\s*(.*?)(?:;|$)', '', title_line)
            
        # Notes from blockquotes
        note_lines = []
        for line in meta_lines:
            line_s = line.strip()
            if line_s.startswith(">"):
                # if there is space after >, remove one space.
                if line_s.startswith("> "):
                    note_lines.append(line_s[2:])
                else:
                    note_lines.append(line_s[1:])
                
        if note_lines:
            plain_text = "\n".join(note_lines)
            
            # Simple Markdown to HTML for Note
            html_text = plain_text
            # Bold
            html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
            # Italic
            html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
            # Link
            html_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html_text)
            # Wrap in div
            html_text = f"<div>{html_text}</div>"
            
            topic.notes = {
                "plain": {"content": plain_text + "\n"},
                "realHTML": {"content": html_text}
            }
            
        topic.title = title_line.strip(' ;').strip()

    @staticmethod
    def to_xmind(md_content: str) -> Workbook:
        """Parse markdown content into a Workbook."""
        import yaml
        
        lines = md_content.splitlines()
        
        # Extract YAML front matter if present
        xmind_config = {}
        if lines and lines[0].strip() == "---":
            end_idx = -1
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    end_idx = i
                    break
            if end_idx != -1:
                yaml_str = "\n".join(lines[1:end_idx])
                try:
                    front_matter = yaml.safe_load(yaml_str)
                    if front_matter and "xmind" in front_matter:
                        xmind_config = front_matter["xmind"]
                except Exception:
                    pass
                lines = lines[end_idx+1:]
        
        stack: List[Tuple[float, Topic]] = []
        root_topic = Topic(title="Central Topic")
        stack.append((0, root_topic))
        
        # Group lines into blocks
        blocks = [] # List of (level, [lines])
        current_block = []
        current_level = -1
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            heading_match = re.match(r'^(#+)\s+(.*)', line_stripped)
            list_match = re.match(r'^(\s*)[-*+]\s+(.*)', line)
            
            if heading_match:
                if current_block:
                    blocks.append((current_level, current_block))
                current_level = len(heading_match.group(1))
                current_block = [heading_match.group(2).strip()]
            elif list_match:
                if current_block:
                    blocks.append((current_level, current_block))
                indent = len(list_match.group(1))
                
                # Determine base level
                base_level = 0
                for s_lvl, _ in reversed(blocks):
                    if s_lvl.is_integer():
                        base_level = s_lvl
                        break
                        
                current_level = base_level + 0.1 + (indent * 0.1)
                current_block = [list_match.group(2).strip()]
            else:
                # It's a continuation line (metadata or note)
                if current_block:
                    current_block.append(line_stripped)
                    
        if current_block:
            blocks.append((current_level, current_block))
            
        # Process blocks
        for level, block_lines in blocks:
            new_topic = Topic(title="")
            MarkdownConverter._parse_metadata(block_lines, new_topic)
            
            while stack and stack[-1][0] >= level:
                stack.pop()
                
            if stack:
                parent = stack[-1][1]
                parent.children.append(new_topic)
            
            stack.append((level, new_topic))
                
        if len(root_topic.children) == 1 and root_topic.title == "Central Topic":
            root_topic = root_topic.children[0]
            
        wb = Workbook(sheets=[Sheet(title="Map 1", root_topic=root_topic)])
        wb.sheets[0].attributes["xmind_config"] = xmind_config
        return wb

    @staticmethod
    def from_xmind(workbook: Workbook) -> str:
        """Convert Workbook to markdown content."""
        if not workbook.sheets:
            return ""
            
        sheet = workbook.sheets[0]
        lines = []
        
        def traverse(topic: Topic, depth: int):
            # We'll use headings for first 3 levels, then lists
            if depth <= 3:
                prefix = "#" * depth
                lines.append(f"{prefix} {topic.title}")
            else:
                indent = "  " * (depth - 4)
                lines.append(f"{indent}- {topic.title}")
                
            for child in topic.children:
                traverse(child, depth + 1)
                
        traverse(sheet.root_topic, 1)
        return "\n".join(lines)
