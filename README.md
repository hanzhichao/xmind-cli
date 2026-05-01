# XMind CLI

A full-featured command-line interface tool to parse, create, and convert XMind files in Python. Supports modern `.xmind` files (XMind ZEN and newer).

## Installation

```bash
pip install python-xmind-cli
```

## Usage

### 1. Parse an XMind file
```bash
xmind-cli parse example.xmind
```

### 2. Create a new XMind file
```bash
xmind-cli create example.xmind --title "Root Topic"
```

### 3. Convert formats
```bash
# Convert Markdown to XMind
xmind-cli convert doc.md out.xmind

# Convert XMind to Excel (with custom headers and level filtering)
xmind-cli convert in.xmind out.xlsx --headers "Module,Feature,Test Case" --start-level 2

# Convert XMind to Markdown/JSON/HTML
xmind-cli convert in.xmind out.md
xmind-cli convert in.xmind out.json
xmind-cli convert in.xmind out.html
```

## Advanced Features

### Markdown YAML Configuration
You can embed XMind styling parameters directly into your Markdown files using a YAML front-matter block.

```markdown
---
xmind:
  skeleton: logic-right
  bg-color: "#0096BFFF"
  font: Andale Mono
  rainbow: true
  compact: true
---
# Python Frameworks
...
```

### Node Formatting & Metadata
The Markdown parser supports rich node attributes:
- **Style**: `**Bold**`, `*Italic*`, `~~Strikethrough~~` (applied to the entire node).
- **Tasks**: `- [ ]` (todo), `- [x]` (done).
- **Metadata**: Inline or multi-line `Tags: a, b`, `Markers: priority-1`.
- **Notes**: Blockquotes `> This is a note` (supports rich text conversion).
- **Links & Images**: `[Title](Link)` for hyperlinks, `![](path/to/img.png)` for embedded images.

## Development

### Running Tests
```bash
pytest
```
