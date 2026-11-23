"""Mise en forme du texte affiché dans le terminal."""

import os


def table(headers: list[str], rows: list[list[object]], right: set[int] | None = None) -> str:
    """Tableau texte aligné ; les colonnes dont l'indice est dans right sont à droite."""
    right = right or set()
    cells = [headers] + [[str(cell) for cell in row] for row in rows]
    widths = [max(len(line[i]) for line in cells) for i in range(len(headers))]
    lines = []
    for line in cells:
        parts = []
        for i, cell in enumerate(line):
            parts.append(cell.rjust(widths[i]) if i in right else cell.ljust(widths[i]))
        lines.append("   ".join(parts).rstrip())
    return "\n".join(lines)


def clear_screen() -> None:
    """Efface le terminal, sous Windows comme sous Linux."""
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="", flush=True)