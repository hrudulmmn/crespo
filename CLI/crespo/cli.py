

import sys
import os
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich.align import Align
from rich import print as rprint
from rich.tree import Tree
from rich import box
from contextlib import contextmanager

console = Console()

# ─── Cresbee pixel art renderer ───────────────────────────────────────────────

def _clickable(path: str) -> Text:
    path = str(path)
    uri = Path(path).resolve().as_uri()
    t = Text(path, style="#8c64dc")
    t.stylize(f"link {uri}")
    return t

def _ansi_fg(r, g, b): return f"\033[38;2;{r};{g};{b}m"
def _ansi_bg(r, g, b): return f"\033[48;2;{r};{g};{b}m"
RESET = "\033[0m"


def render_cresbee(image_path: str, width: int = 38) -> list[str]:
    """
    Render Cresbee PNG as half-block (▀) terminal art.
    Uses NEAREST resampling for sharp pixel-art edges.
    Alpha threshold 80 keeps only solid pixels — no blurry anti-alias halo.
    Returns a list of ANSI strings, one per terminal row.
    Falls back to ASCII art on any error.
    """
    try:
        from PIL import Image
        import numpy as np
 
        img = Image.open(image_path).convert("RGBA")
        arr = np.array(img).copy()
 
        # ── strip near-black background ──────────────────────────────────────
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        bg = (r < 22) & (g < 22) & (b < 22)
        arr[bg, 3] = 0
 
        clean = Image.fromarray(arr, "RGBA")
        bbox  = clean.getbbox()
        if not bbox:
            return _fallback_cresbee()
 
        cropped = clean.crop(bbox)
 
        # ── resize with NEAREST for hard pixel-art edges ─────────────────────
        aspect    = cropped.height / cropped.width
        px_height = int(width * aspect)
        # must be even for ▀/▄ pairing
        if px_height % 2:
            px_height += 1
 
        resized = cropped.resize((width, px_height), Image.NEAREST)
        px      = np.array(resized)
 
        ALPHA_THRESH = 80   # pixels below this alpha → transparent
 
        lines = []
        for y in range(0, px_height, 2):
            row = ""
            for x in range(width):
                top = px[y,     x]
                bot = px[y + 1, x] if (y + 1) < px_height else (0, 0, 0, 0)
 
                t_on = int(top[3]) >= ALPHA_THRESH
                b_on = int(bot[3]) >= ALPHA_THRESH
 
                if t_on and b_on:
                    tr, tg, tb = int(top[0]), int(top[1]), int(top[2])
                    br, bg_c, bb = int(bot[0]), int(bot[1]), int(bot[2])
                    row += (
                        _ansi_fg(tr, tg, tb)
                        + _ansi_bg(br, bg_c, bb)
                        + "▀"
                        + RESET
                    )
                elif t_on:
                    tr, tg, tb = int(top[0]), int(top[1]), int(top[2])
                    row += _ansi_fg(tr, tg, tb) + "▀" + RESET
                elif b_on:
                    br, bg_c, bb = int(bot[0]), int(bot[1]), int(bot[2])
                    row += _ansi_fg(br, bg_c, bb) + "▄" + RESET
                else:
                    row += " "
            lines.append(row)
 
        return lines
 
    except Exception:
        return _fallback_cresbee()


def _fallback_cresbee() -> list[str]:
    """ASCII fallback when PIL unavailable or image missing."""
    return [
        "  \033[38;2;130;110;200m╭──╮ ╭──╮\033[0m",
        " \033[38;2;100;200;140m╭╯\033[0m\033[38;2;130;110;200m  ╰─╯  \033[0m\033[38;2;100;200;140m╰╮\033[0m",
        " \033[38;2;100;200;140m│\033[0m  \033[1;37m◉\033[0m    \033[1;37m◉\033[0m  \033[38;2;100;200;140m│\033[0m",
        " \033[38;2;100;200;140m│\033[0m    \033[38;2;130;110;200m──\033[0m    \033[38;2;100;200;140m│\033[0m",
        " \033[38;2;100;200;140m╰──┬\033[0m\033[38;2;255;200;50m████\033[0m\033[38;2;100;200;140m┬──╯\033[0m",
        "    \033[38;2;100;200;140m│\033[0m\033[38;2;255;200;50m 🍯 \033[0m\033[38;2;100;200;140m│\033[0m",
        "    \033[38;2;100;200;140m╰────╯\033[0m",
    ]


def print_cresbee(image_path: str | None = None, width: int = 34):
    """Print Cresbee to terminal."""
    path = image_path or "cresbee.png"
    lines = render_cresbee(path, width=width)
    for line in lines:
        print(line)
    print("\033[0m", end="")


# ─── Header ───────────────────────────────────────────────────────────────────

def print_header(image_path: str | None = None):
    """Full startup header with Cresbee + branding."""
    console.print()
    console.print(Rule(style="#8c64dc"))

    # Cresbee on left, branding on right
    cresbee_lines = render_cresbee(image_path or "cresbee.png", width=30)

    # build branding text
    brand_lines = [
        "",
        "\033[1;38;2;100;200;140m  ██████╗██████╗ ███████╗███████╗██████╗  ██████╗ \033[0m",
        "\033[38;2;100;200;140m ██╔════╝ ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗\033[0m",
        "\033[38;2;110;180;160m ██║      ██████╔╝█████╗  ███████╗██████╔╝██║   ██║\033[0m",
        "\033[38;2;120;160;180m ██║      ██╔══██╗██╔══╝  ╚════██║██╔═══╝ ██║   ██║\033[0m",
        "\033[38;2;130;110;200m ╚██████╗ ██║  ██║███████╗███████║██║     ╚██████╔╝\033[0m",
        "\033[38;2;140;100;220m  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝      ╚═════╝ \033[0m",
        "",
        "\033[38;2;100;200;140m  Crisp repos. Sharp AI.\033[0m",
        "\033[38;2;90;90;120m  Give AI the blueprint, not the code.\033[0m",
        "",
        "\033[38;2;100;200;140m  v1.0.14\033[0m  \033[38;2;90;90;120m•  MIT License  •  pip install crespo\033[0m",
    ]

    # print side by side
    max_lines = max(len(cresbee_lines), len(brand_lines))

    for i in range(max_lines):
        left = cresbee_lines[i] if i < len(cresbee_lines) else ""
        right = brand_lines[i] if i < len(brand_lines) else ""
        # pad left column to fixed width (accounting for ANSI codes)
        visible_len = len(left.encode("utf-8").decode("utf-8"))
        # rough padding — cresbee art is ~30 chars wide
        print(f"  {left}   {right}")

    print("\033[0m")

    # separator
    console.print(
        Rule(style="#8c64dc"),
    )


def print_usage():
    """Print usage panel."""
    console.print(
        Panel(
            Text.from_markup(
                "[bold green]Usage[/bold green]\n"
                "  [cyan]crespo[/cyan] [purple]<path|url>[/purple] "
                "[[green]--mode[/green] structure|summary|concat] "
                "[[green]--output[/green] file.xml]\n\n"
                "[bold green]Examples[/bold green]\n"
                "  [green]crespo[/green] ./myproject\n"
                "  [green]crespo[/green] ./myproject [green]--mode[/green] summary\n"
                "  [green]crespo[/green] [green]--git[/green] https://github.com/user/repo\n"
                "  [green]crespo[/green] ./myproject [green]--mode[/green] concat "
                "[green]--output[/green] full.xml\n\n"
                "[bold green]Modes[/bold green]\n"
                "  [green]structure[/green] :\tAST skeleton only — ~84% token reduction  "
                "[dim](default)[/dim]\n"
                "  [purple]summary[/purple] :\tstructure + AI function descriptions via Groq\n"
                "  [cyan]concat[/cyan] :\tfull source + secrets redacted + structure header\n\n"
                "[bold green]Options[/bold green]\n"
                "  [green]--mode[/green]      structure | summary | concat\n"
                "  [green]--output[/green]    Output filename  [dim](default: blueprint.xml)[/dim]\n"
                "  [green]--groq[/green]      Groq API key for summary mode [dim]or set CRESPO_GROQ_KEY env var[/dim]\n"
                "  [green]--git[/green]       Using git URL.\n"
                "  [green]--help[/green]      Show this message"
            ),
            title="[bold green]Crespo[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


# ─── Scan phase ───────────────────────────────────────────────────────────────

def print_scan_start(source: str, mode: str):
    """Print scan start info."""
    mode_colors = {
        "structure": "green",
        "summary": "purple",
        "concat": "cyan",
    }
    color = mode_colors.get(mode, "green")
    console.print(
        f"  [dim]Source[/dim]  [white]{Path(source).resolve()}[/white]"
    )
    console.print(
        f"  [dim]Mode[/dim]    [{color}]{mode}[/{color}]"
    )
    console.print(Rule(title="[green][b]DETAILS[/b][/green]",style="#8c64dc"))


LANG_COLORS = {
    "py": "blue", "js": "yellow", "ts": "cyan",
    "jsx": "yellow", "tsx": "cyan", "rs": "red",
    "go": "cyan", "java": "red", "c": "green", "cpp": "green",
}

def _lang_badge(lang: str) -> str:
    color = LANG_COLORS.get(lang, "white")
    return f"[{color}]{lang}[/{color}]"

def _ext(relpath: str) -> str:
    return Path(relpath).suffix.lstrip(".")


# ── Style 1: Classic Rich Tree (├── branches) ─────────────────────────────────

def print_tree_classic(found: list[str],root:str = "project"):
    """Builds a Rich Tree with ├── / └── branch lines."""
    tree = Tree(f"[bold green]{root}[/bold green]")
    nodes: dict[str, Tree] = {}

    def get_dir_node(parts: tuple) -> Tree:
        if not parts:
            return tree
        if parts in nodes:
            return nodes[parts]
        parent = get_dir_node(parts[:-1])
        node = parent.add(f"[#8c64dc][b]{parts[-1]}[b][/#8c64dc]")
        nodes[parts] = node
        return node

    for relpath in sorted(found):
        p = Path(relpath)
        lang = _ext(relpath)
        parent = get_dir_node(p.parts[:-1])
        parent.add(f"{p.name}  {_lang_badge(lang)}")

    console.print(Panel(tree,box=box.SIMPLE,border_style="dim"))


# ─── Parse phase ──────────────────────────────────────────────────────────────

def run_with_progress(files: list[dict], label: str = "Parsing") -> None:
    """Show progress bar while parsing files."""
    with Progress(
        SpinnerColumn(style="green"),
        TextColumn("  [green]{task.description}[/green]"),
        BarColumn(bar_width=30, style="green", complete_style="bright_green"),
        TaskProgressColumn(),
        TextColumn("[dim]{task.fields[filename]}[/dim]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            label,
            total=len(files),
            filename=""
        )
        for file in files:
            name = Path(file.get("relpath", "")).name
            progress.update(task, advance=1, filename=name)
            time.sleep(0.1)  # remove this in real implementation

    console.print()
    console.print(Rule(style="#8c64dc"))
    console.print(f"  [green]✓[/green]  [dim]Parsed {len(files)} files[/dim]")
    console.print(Rule(style="#8c64dc"))


def run_summary_progress(files: list[dict]) -> None:
    """Show Groq API call progress for summary mode."""
    print_rule()
    console.print("  [purple]Calling Groq API...[/purple]")
    console.print()

    with Progress(
        SpinnerColumn(style="purple"),
        TextColumn("  [purple]{task.description}[/purple]"),
        BarColumn(bar_width=25, style="purple", complete_style="bright_magenta"),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Summarising", total=len(files))
        for file in files:
            name = Path(file.get("relpath", "")).name
            progress.update(task, description=f"summarising {name}", advance=1)
            time.sleep(0.08)

    console.print(f"  [purple]✓[/purple]  [dim]Summaries generated[/dim]")


# ─── Security phase ───────────────────────────────────────────────────────────

def print_security_result(secrets_found: int, files_scanned: int):
    """Print security scan result."""
    if secrets_found == 0:
        console.print(
            f"  [green]✓[/green]  [dim]Security scan — {files_scanned} files — "
            f"no secrets detected[/dim]"
        )
    else:
        console.print(
            f"  [yellow]⚠[/yellow]  [yellow]Security scan — "
            f"{secrets_found} secret(s) redacted[/yellow]"
        )


# ─── Stats ────────────────────────────────────────────────────────────────────

def print_token_stats(
    original_tokens: int,
    output_tokens: int,
    mode: str,
    output_file: str,
    elapsed: float,
    extra_stats: dict | None = None,
):
    """Print final token statistics table."""
    reduction = round((1 - output_tokens / max(original_tokens, 1)) * 100)

    console.print(Rule(title="[green][b]ANALYSIS[/b][/green]",style="#8c64dc"))
    console.print()

    # stats table
    table = Table(
        box=box.ROUNDED,
        padding=(0, 2),
        border_style="green",
    )
    table.add_column("Metric", style="dim", width=20)
    table.add_column("Value", justify="right")

    table.add_row(
        "Original Tokens",
        f"[red]{original_tokens:,}[/red]"
    )
    table.add_row(
        "Crespo Output",
        f"[green]{output_tokens:,}[/green]"
    )
    table.add_row(
        "Token Reduction",
        f"[bold purple]{reduction}%[/bold purple]"
    )
    table.add_row(
        "Mode",
        f"[cyan]{mode}[/cyan]"
    )

    if extra_stats:
        for k, v in extra_stats.items():
            table.add_row(k, str(v))

    table.add_row("", "")
    table.add_row(
        "Output File",
        _clickable(output_file)
    )
    table.add_row(
        "Time Elapsed",
        f"[dim]{elapsed:.1f}s[/dim]"
    )

    console.print(Align(table, align="center", pad=True))

    # reduction bar
    console.print()
    bar_width = 40
    remaining = max(1, int(bar_width * (1 - output_tokens / max(original_tokens, 1))))
    empty = bar_width - remaining

    console.print(Align(
        f"  [dim]Original[/dim]  "
        f"[red]{'█' * bar_width}[/red]  "
        f"[cyan]{original_tokens:,}[/cyan]",align="center")
    )
    console.print("\n")
    console.print(Align(
        f"  [dim]Crespo[/dim]  "
        f"[green]{'█' * empty}[/green][dim]{'░' * remaining}[/dim]  "
        f"[green]{output_tokens:,}[/green]",align="center")
    )
    console.print()

    # done
    saved = Text()
    saved.append("Blueprint saved → ", style="green")
    saved.append_text(_clickable(output_file))
    console.print(Align(saved,align="center"))
    console.print(Rule(style="#8c64dc"))


# ─── Error / warning helpers ──────────────────────────────────────────────────

def print_error(message: str):
    console.print(f"\n  [red]✗[/red]  [red]{message}[/red]\n")


def print_warning(message: str):
    console.print(f"  [yellow]⚠[/yellow]  [yellow]{message}[/yellow]")

def print_loc(output_file):
    saved = Text()
    saved.append("Blueprint saved → ", style="green")
    saved.append_text(_clickable(output_file))
    console.print(Align(saved, "center"))
    console.print(Rule(style="#8c64dc"))


def print_info(message: str):
    console.print(Align(f"  [dim]{message}[/dim]","center"))


def print_groq_fallback():
    """Warn when Groq rate limit hit and falling back to structure."""
    console.print()
    console.print(
        Panel(
            "[yellow]Groq rate limit reached.[/yellow]\n"
            "Remaining files will use [green]structure mode[/green] "
            "(no summaries).\n"
            "[dim]Files already summarised are preserved.[/dim]",
            border_style="yellow",
            padding=(0, 2),
        )
    )
    console.print()


def print_no_groq_key():
    """Warn when no Groq key and falling back."""
    console.print()
    console.print(
        Panel(
            "[yellow]No Groq API key found.[/yellow]\n"
            "Falling back to [green]structure mode[/green].\n\n"
            "[dim]To use summary mode:[/dim]\n"
            "  [green]export CRESPO_GROQ_KEY=your_key_here[/green]\n"
            "  [dim]Get a free key at[/dim] [cyan]https://console.groq.com[/cyan]",
            border_style="yellow",
            padding=(0, 2),
        )
    )
    console.print()

@contextmanager  
def summary_progress_context(total_files: int):
    """
    Context manager that keeps the Groq spinner alive until the caller exits.
    Yields an `advance(n)` callable so batch completions can tick the bar.
    
    Usage:
        with cli.summary_progress_context(len(files)) as advance:
            for chunk in batches:
                summaries = summariser.summarise_files_batch(chunk)
                advance(len(chunk))
    """
    print_rule()
    console.print("  [purple]Calling Groq API...[/purple]")
    console.print()

    with Progress(
        SpinnerColumn(style="purple"),
        TextColumn("  [purple]{task.description}[/purple]"),
        TaskProgressColumn(),
        TextColumn("[dim]{task.fields[current]}[/dim]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            "Summarising",
            total=total_files,
            current=""
        )

        def advance(n: int, label: str = ""):
            progress.update(task, advance=n, current=label)

        yield advance   # caller runs here; progress bar stays alive

    console.print(f"  [purple]✓[/purple]  [dim]Summaries generated[/dim]")

def print_rule():
    console.print(Rule(style="#8c64cd"))

@contextmanager
def parse_progress_context(total_files: int):
    with Progress(
        SpinnerColumn(style="green"),
        TextColumn("  [green]{task.description}[/green]"),
        BarColumn(bar_width=30, style="green", complete_style="bright_green"),
        TaskProgressColumn(),
        TextColumn("[dim]{task.fields[filename]}[/dim]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Parsing", total=total_files, filename="")

        def advance(filename: str = ""):
            progress.update(task, advance=1, filename=filename)

        yield advance

    print_rule()
    console.print(f"  [green]✓[/green]  [dim]Parsed {total_files} files[/dim]")
    print_rule()