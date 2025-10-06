"""Utility to convert a Markdown table into a bullet-friendly layout for LLM prompts."""

from typing import Iterable, List, Sequence, Tuple

TABLE_MD = """
| Name | Role | Location |
| ---- | ---- | -------- |
| Alice | Engineer | Berlin |
| Bob | Designer | Oslo |
"""

SKIP_COLUMNS: Sequence[int] = []  # 1-based column indices to skip from the output.


def split_row(line: str) -> List[str]:
    """Split a Markdown table row into stripped cell values."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    """Return True when the line is a Markdown separator (--- style)."""
    stripped = line.strip().strip("|")
    stripped = (
        stripped.replace("|", "")
        .replace("-", "")
        .replace(":", "")
        .replace(" ", "")
    )
    return not stripped


def parse_markdown_table(md_table: str) -> Tuple[List[str], List[List[str]]]:
    """Parse the Markdown table and return headers with row data."""
    lines = [line.strip() for line in md_table.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Markdown table must include header and separator lines.")

    headers = split_row(lines[0])
    rows: List[List[str]] = []

    for line in lines[1:]:
        if is_separator(line):
            continue
        row = split_row(line)
        if len(row) != len(headers):
            raise ValueError("Row length does not match header length.")
        rows.append(row)

    if not rows:
        raise ValueError("Markdown table does not contain any data rows.")

    return headers, rows


def column_value_repr(header: str, value: str) -> str:
    """Return a display string respecting empty header/value combinations."""
    header = header.strip()
    value = value.strip()
    if not header:
        return value
    if not value:
        return header
    return f"{header} = {value}"


def format_as_bullets(headers: List[str], rows: List[List[str]], skip_columns: Iterable[int]) -> str:
    """Convert parsed table data into a bullet list representation."""
    skip_set = {col_idx - 1 for col_idx in skip_columns}
    invalid = [idx for idx in skip_set if idx < 0 or idx >= len(headers)]
    if invalid:
        raise ValueError(f"Skip columns out of range: {[i + 1 for i in invalid]}")

    included_indices = [idx for idx, _ in enumerate(headers) if idx not in skip_set]

    if not included_indices:
        raise ValueError("All columns were skipped; cannot produce output.")

    first_index, *other_indices = included_indices
    output_lines = []

    for row in rows:
        first_value = row[first_index]
        first_field = column_value_repr(headers[first_index], first_value)
        if not first_field:
            continue
        output_lines.append(f"- {first_field}")
        for idx in other_indices:
            header = headers[idx]
            value = row[idx]
            field = column_value_repr(header, value)
            if not field:
                continue
            output_lines.append(f"  - {field}")

    return "\n".join(output_lines)


def main() -> None:
    headers, rows = parse_markdown_table(TABLE_MD)
    bullets = format_as_bullets(headers, rows, SKIP_COLUMNS)
    print(bullets)


if __name__ == "__main__":
    main()
