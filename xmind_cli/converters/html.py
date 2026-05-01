from pathlib import Path
from ..core.models import Workbook
from .markdown import MarkdownConverter

class HTMLConverter:
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XMind to HTML (Markmap)</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
        }
        #markmap {
            width: 100%;
            height: 100%;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib"></script>
</head>
<body>
    <svg id="markmap"></svg>
    <script>
        const markdown = `{markdown_content}`;
        const { Markmap, loadCSS, loadJS } = window.markmap;
        const { Transformer } = window.markmap;
        
        const transformer = new Transformer();
        const { root, features } = transformer.transform(markdown);
        const { styles, scripts } = transformer.getUsedAssets(features);
        
        if (styles) loadCSS(styles);
        if (scripts) loadJS(scripts, { getMarkmap: () => window.markmap });
        
        Markmap.create('#markmap', null, root);
    </script>
</body>
</html>"""

    @classmethod
    def from_xmind(cls, workbook: Workbook, output_path: str | Path):
        output_path = Path(output_path)
        md_content = MarkdownConverter.from_xmind(workbook)
        # Escape backticks and backslashes for JS string interpolation
        safe_md = md_content.replace("\\", "\\\\").replace("`", "\\`")
        
        html_content = cls.HTML_TEMPLATE.replace("{markdown_content}", safe_md)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
