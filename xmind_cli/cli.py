import typer
from pathlib import Path
from rich.console import Console
from rich.tree import Tree

from .core.models import Topic, Workbook, Sheet
from .core.parser import XMindParser
from .core.builder import XMindBuilder
from .converters.markdown import MarkdownConverter
from .converters.json_conv import JsonConverter
from .converters.excel import ExcelConverter
from .converters.html import HTMLConverter

app = typer.Typer(help="A full-featured CLI tool for parsing, creating, and converting XMind files.")
console = Console()

# Skeleton mapping
SKELETON_MAP = {
    "mindmap": "org.xmind.ui.map.unbalanced",
    "logic-right": "org.xmind.ui.logic.right",
    "org-chart": "org.xmind.ui.org-chart.down",
    "tree-right": "org.xmind.ui.tree.right",
    "fishbone-left": "org.xmind.ui.fishbone.leftHeading",
}

def _print_topic_tree(topic: Topic, tree: Tree):
    for child in topic.children:
        branch = tree.add(f"[cyan]{child.title}[/cyan]")
        _print_topic_tree(child, branch)


@app.command()
def parse(file: Path = typer.Argument(..., help="Path to the .xmind file"),
          format: str = typer.Option("text", help="Output format: text or json")):
    """Parse an XMind file and display its structure."""
    if not file.exists():
        console.print(f"[red]Error: File {file} does not exist.[/red]")
        raise typer.Exit(1)
        
    try:
        workbook = XMindParser.parse_file(file)
        
        if format == "json":
            json_str = JsonConverter.from_xmind(workbook)
            console.print_json(json_str)
        else:
            for sheet in workbook.sheets:
                tree = Tree(f"[bold green]{sheet.root_topic.title}[/bold green] (Sheet: {sheet.title})")
                _print_topic_tree(sheet.root_topic, tree)
                console.print(tree)
                console.print()
                
    except Exception as e:
        console.print(f"[red]Failed to parse {file}: {e}[/red]")
        raise typer.Exit(1)


def _apply_styles(workbook: Workbook, skeleton: str, bg_color: str, font: str, rainbow: bool, compact: bool):
    """Apply styles to the given workbook's first sheet."""
    if not workbook.sheets:
        return
        
    sheet = workbook.sheets[0]
    
    if skeleton and skeleton in SKELETON_MAP:
        sheet.root_topic.structure_class = SKELETON_MAP[skeleton]
        
    if bg_color or font or rainbow or compact:
        sheet.theme = sheet.theme or {}
        sheet.style_properties = sheet.style_properties or {}
        
        if compact:
            sheet.compact_layout = "Second"
            
        if bg_color:
            sheet.style_properties["svg:fill"] = bg_color
            
        if font:
            sheet.theme["global"] = sheet.theme.get("global", {})
            sheet.theme["global"]["properties"] = sheet.theme["global"].get("properties", {})
            sheet.theme["global"]["properties"]["fo:font-family"] = font
            
        if rainbow:
            sheet.style_properties["multi-line-colors"] = "#F9423A #F6A04D #F3D321 #00BC7B #486AFF #4D49BE"
            sheet.style_properties["line-tapered"] = "none"


@app.command()
def create(file: Path = typer.Argument(..., help="Path to the new .xmind file"),
           title: str = typer.Option("Central Topic", help="Title of the root topic"),
           content: str = typer.Option(None, help="Markdown content to populate the tree"),
           skeleton: str = typer.Option("mindmap", help=f"Layout skeleton: {', '.join(SKELETON_MAP.keys())}"),
           bg_color: str = typer.Option(None, help="Background color hex code (e.g., #FFFFFF)"),
           font: str = typer.Option(None, help="Global font family"),
           rainbow: bool = typer.Option(False, help="Enable rainbow branches"),
           compact: bool = typer.Option(False, help="Enable compact layout")):
    """Create a new XMind file. If --content is omitted, will read from stdin or interactively prompt."""
    import sys
    
    # Content resolution
    if content is None:
        if not sys.stdin.isatty():
            # Read from pipeline
            content = sys.stdin.read().strip()
        else:
            # Interactive prompt
            console.print("[yellow]Please enter Markdown content for your mind map (Press Ctrl+D when finished):[/yellow]")
            try:
                content = sys.stdin.read().strip()
            except KeyboardInterrupt:
                raise typer.Exit(0)
    
    if file.exists():
        console.print(f"[yellow]Warning: File {file} already exists. It will be overwritten.[/yellow]")
        
    try:
        # Build base workbook
        if content:
            workbook = MarkdownConverter.to_xmind(content)
            sheet = workbook.sheets[0]
            if title != "Central Topic":
                sheet.root_topic.title = title
        else:
            root_topic = Topic(title=title)
            sheet = Sheet(title="Map 1", root_topic=root_topic)
            workbook = Workbook(sheets=[sheet])
            
        # Apply Styling
        _apply_styles(workbook, skeleton, bg_color, font, rainbow, compact)
            
        XMindBuilder.build_file(workbook, file)
        console.print(f"[green]Successfully created {file}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to create {file}: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def convert(input_file: Path = typer.Argument(..., help="Input file path"),
            output_file: Path = typer.Argument(..., help="Output file path"),
            skeleton: str = typer.Option(None, help=f"Layout skeleton: {', '.join(SKELETON_MAP.keys())}"),
            bg_color: str = typer.Option(None, help="Background color hex code (e.g., #FFFFFF)"),
            font: str = typer.Option(None, help="Global font family"),
            rainbow: bool = typer.Option(False, help="Enable rainbow branches"),
            compact: bool = typer.Option(False, help="Enable compact layout"),
            headers: str = typer.Option(None, help="Comma-separated headers for Excel export (e.g., Level1,Level2)"),
            start_level: int = typer.Option(1, help="Starting level for Excel export (e.g., 2 to skip root)")):
    """Convert between XMind and other formats (.md, .json, .xlsx, .html)."""
    if not input_file.exists():
        console.print(f"[red]Error: Input file {input_file} does not exist.[/red]")
        raise typer.Exit(1)
        
    in_ext = input_file.suffix.lower()
    out_ext = output_file.suffix.lower()
    
    try:
        # Load Workbook
        workbook = None
        if in_ext == ".xmind":
            workbook = XMindParser.parse_file(input_file)
        elif in_ext == ".md":
            with open(input_file, "r", encoding="utf-8") as f:
                workbook = MarkdownConverter.to_xmind(f.read())
        elif in_ext == ".json":
            with open(input_file, "r", encoding="utf-8") as f:
                workbook = JsonConverter.to_xmind(f.read())
        else:
            console.print(f"[red]Unsupported input format: {in_ext}[/red]")
            raise typer.Exit(1)
            
        # Apply styles if output is .xmind
        if out_ext == ".xmind":
            if workbook.sheets:
                xmind_config = workbook.sheets[0].attributes.get("xmind_config", {})
                
                # Command line args take precedence over markdown yaml config
                final_skeleton = skeleton or xmind_config.get("skeleton")
                final_bg_color = bg_color or xmind_config.get("bg-color")
                final_font = font or xmind_config.get("font")
                final_rainbow = rainbow if rainbow else xmind_config.get("rainbow", False)
                final_compact = compact if compact else xmind_config.get("compact", False)
                
                _apply_styles(workbook, final_skeleton, final_bg_color, final_font, final_rainbow, final_compact)
                
                # Remove xmind_config attribute from sheet so it doesn't leak into json
                workbook.sheets[0].attributes.pop("xmind_config", None)
            
        # Export Workbook
        if out_ext == ".xmind":
            XMindBuilder.build_file(workbook, output_file)
        elif out_ext == ".md":
            md_content = MarkdownConverter.from_xmind(workbook)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_content)
        elif out_ext == ".json":
            json_content = JsonConverter.from_xmind(workbook)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_content)
        elif out_ext == ".xlsx":
            ExcelConverter.from_xmind(workbook, output_file, headers=headers, start_level=start_level)
        elif out_ext == ".html":
            HTMLConverter.from_xmind(workbook, output_file)
        elif out_ext == ".png":
            PNGConverter.from_xmind(workbook, output_file)
        else:
            console.print(f"[red]Unsupported output format: {out_ext}[/red]")
            raise typer.Exit(1)
            
        console.print(f"[green]Successfully converted {input_file} to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Conversion failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
