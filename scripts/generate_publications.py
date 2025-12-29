#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class BibEntry:
    entry_type: str
    citekey: str
    fields: Dict[str, str]
    raw: str = ""


def _strip_wrapping_braces(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == "{" and value[-1] == "}":
        return value[1:-1].strip()
    return value


def _collapse_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _unescape_basic_latex(value: str) -> str:
    # Minimal, conservative cleanup for common BibTeX exports.
    value = value.replace("\\&", "&")
    value = value.replace("\\%", "%")
    value = value.replace("\\_", "_")
    value = value.replace("\\$", "$")
    value = value.replace("{", "").replace("}", "")
    return value


def _parse_author_list(value: str) -> List[str]:
    value = _collapse_ws(_strip_wrapping_braces(value))
    if not value:
        return []
    parts = [p.strip() for p in value.split(" and ") if p.strip()]
    normalized: List[str] = []
    for p in parts:
        # Handle "Last, First" -> "First Last"
        if "," in p:
            last, first = [x.strip() for x in p.split(",", 1)]
            p = f"{first} {last}".strip()
        normalized.append(_unescape_basic_latex(p))
    return normalized


def _yaml_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def _slugify(value: str, max_len: int = 60) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    if not value:
        return "item"
    return value[:max_len].rstrip("-")


def parse_bibtex(text: str) -> List[BibEntry]:
    entries: List[BibEntry] = []
    i = 0
    n = len(text)

    def skip_ws(idx: int) -> int:
        while idx < n and text[idx].isspace():
            idx += 1
        return idx

    while i < n:
        i = skip_ws(i)
        if i >= n:
            break
        if text[i] != "@":
            i += 1
            continue

        entry_start = i
        i += 1
        i = skip_ws(i)
        start = i
        while i < n and (text[i].isalpha() or text[i] in "-_"):
            i += 1
        entry_type = text[start:i].strip().lower()
        i = skip_ws(i)
        if i >= n or text[i] not in "{(":
            i = entry_start + 1
            continue
        open_ch = text[i]
        close_ch = "}" if open_ch == "{" else ")"
        i += 1

        i = skip_ws(i)
        start = i
        while i < n and text[i] not in ",\n\r":
            i += 1
        citekey = text[start:i].strip()
        while i < n and text[i] != ",":
            if text[i] == close_ch:
                break
            i += 1
        if i < n and text[i] == ",":
            i += 1

        fields: Dict[str, str] = {}

        while i < n:
            i = skip_ws(i)
            if i >= n:
                break
            if text[i] == close_ch:
                i += 1
                break
            if text[i] == ",":
                i += 1
                continue

            # field name
            start = i
            while i < n and (text[i].isalnum() or text[i] in "_-:"):
                i += 1
            name = text[start:i].strip().lower()
            i = skip_ws(i)
            if i >= n or text[i] != "=":
                # Skip until comma/close
                while i < n and text[i] not in f",{close_ch}":
                    i += 1
                continue
            i += 1
            i = skip_ws(i)
            if i >= n:
                break

            # field value
            if text[i] in "{":
                depth = 0
                start = i
                while i < n:
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    i += 1
                raw = text[start:i]
            elif text[i] == '"':
                i += 1
                start = i
                while i < n:
                    if text[i] == '"' and text[i - 1] != "\\":
                        break
                    i += 1
                raw = text[start:i]
                i += 1
            else:
                start = i
                while i < n and text[i] not in f",{close_ch}\n\r":
                    i += 1
                raw = text[start:i]

            raw = _collapse_ws(raw)
            raw = raw.strip().rstrip(",")
            raw = _strip_wrapping_braces(raw)
            raw = raw.strip('"')
            fields[name] = raw

        raw_entry = text[entry_start:i].strip()
        if citekey:
            entries.append(
                BibEntry(
                    entry_type=entry_type, citekey=citekey, fields=fields, raw=raw_entry
                )
            )

    return entries


def _date_for_entry(fields: Dict[str, str]) -> dt.date:
    date_str = fields.get("date", "").strip()
    if date_str:
        try:
            return dt.date.fromisoformat(date_str[:10])
        except ValueError:
            pass
    year = fields.get("year", "").strip()
    if year.isdigit():
        return dt.date(int(year), 1, 1)
    return dt.date.today()


def _venue_for_entry(fields: Dict[str, str]) -> str:
    return (
        fields.get("booktitle")
        or fields.get("journal")
        or fields.get("publisher")
        or fields.get("howpublished")
        or ""
    ).strip()


_VENUE_STOPWORDS = {
    "and",
    "of",
    "the",
    "for",
    "in",
    "on",
    "to",
    "a",
    "an",
    "with",
}

_VENUE_WORD_ABBR = {
    "academy": "Acad.",
    "analysis": "Anal.",
    "applications": "Appl.",
    "application": "Appl.",
    "behaviour": "Behav.",
    "behavior": "Behav.",
    "communications": "Commun.",
    "computer": "Comput.",
    "conference": "Conf.",
    "engineering": "Eng.",
    "environment": "Environ.",
    "environmental": "Environ.",
    "information": "Inf.",
    "intelligent": "Intell.",
    "international": "Int.",
    "journal": "J.",
    "letters": "Lett.",
    "management": "Manag.",
    "national": "Natl.",
    "proceedings": "Proc.",
    "research": "Res.",
    "science": "Sci.",
    "society": "Soc.",
    "systems": "Syst.",
    "technology": "Technol.",
    "transportation": "Transp.",
    "transactions": "Trans.",
    "university": "Univ.",
}


def abbreviate_venue(venue: str) -> str:
    venue = _collapse_ws(_strip_wrapping_braces(venue))
    if not venue:
        return ""

    # If it already looks abbreviated, keep it.
    if "." in venue:
        return venue

    out: List[str] = []
    for raw in venue.split():
        tok = raw
        trailing = ""
        while tok and tok[-1] in ",:;":
            trailing = tok[-1] + trailing
            tok = tok[:-1]

        core = tok.strip("()[]{}")
        if not core:
            continue
        low = core.lower()
        if low in _VENUE_STOPWORDS:
            continue

        if core.isupper() and 2 <= len(core) <= 6:
            out.append(core + trailing)
            continue
        if re.fullmatch(r"[A-Z]", core):
            out.append(core + trailing)
            continue

        repl = _VENUE_WORD_ABBR.get(low)
        out.append((repl or core) + trailing)

    return " ".join(out)


def _tags_for_entry(fields: Dict[str, str]) -> List[str]:
    keywords = fields.get("keywords", "").strip()
    if not keywords:
        return []
    parts = re.split(r"[;,]", keywords)
    tags = [_collapse_ws(_unescape_basic_latex(p)) for p in parts if _collapse_ws(p)]
    # Stable unique while preserving order
    seen = set()
    out: List[str] = []
    for t in tags:
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append(t)
    return out


def _links_for_entry(fields: Dict[str, str]) -> Dict[str, str]:
    links: Dict[str, str] = {}

    url = fields.get("url", "").strip()
    if url:
        links["project"] = url

    eprint = fields.get("eprint", "").strip()
    eprint_type = fields.get("eprinttype", "").strip().lower()
    if eprint and eprint_type == "arxiv":
        links["pdf"] = f"https://arxiv.org/abs/{eprint}"

    pdf = fields.get("pdf", "").strip()
    if pdf:
        if pdf.lower().startswith("10."):
            links["pdf"] = f"https://doi.org/{pdf}"
        else:
            links["pdf"] = pdf

    doi = fields.get("doi", "").strip()
    if doi and "pdf" not in links:
        if doi.lower().startswith("http"):
            links["pdf"] = doi
        else:
            links["pdf"] = f"https://doi.org/{doi}"

    code = fields.get("code", "").strip() or fields.get("github", "").strip()
    if code:
        links["code"] = code

    return links


def render_markdown(entry: BibEntry) -> str:
    f = entry.fields
    title = _unescape_basic_latex(_collapse_ws(f.get("title", entry.citekey)))
    authors = _parse_author_list(f.get("author", ""))
    venue_full = _unescape_basic_latex(_collapse_ws(_venue_for_entry(f)))
    venue = abbreviate_venue(venue_full)
    date = _date_for_entry(f)
    year = f.get("year", str(date.year)).strip()
    abstract = _unescape_basic_latex(f.get("abstract", "")).strip()
    tags = _tags_for_entry(f)
    links = _links_for_entry(f)

    lines: List[str] = []
    lines.append("---")
    lines.append(f'title: {_yaml_quote(title)}')
    lines.append(f"date: {date.isoformat()}")
    desc = _collapse_ws(abstract)[:160]
    lines.append(f"# description: {_yaml_quote(desc)}")
    if authors:
        lines.append("authors:")
        for a in authors:
            lines.append(f"  - {_yaml_quote(a)}")
    if venue:
        lines.append(f"venue: {_yaml_quote(venue)}")
    if year:
        if year.isdigit():
            lines.append(f"year: {year}")
        else:
            lines.append(f"year: {_yaml_quote(year)}")
    if tags:
        lines.append("tags:")
        for t in tags:
            lines.append(f"  - {_yaml_quote(t)}")
    if links:
        lines.append("links:")
        for k in ("pdf", "code", "project"):
            if k in links:
                lines.append(f"  {k}: {_yaml_quote(links[k])}")
    lines.append("---")
    lines.append("")

    lines.append("## Citation")
    lines.append("")
    lines.append("```bibtex")
    bib = entry.raw.strip() or f"@{entry.entry_type}{{{entry.citekey}, ...}}"
    lines.append(bib.rstrip())
    lines.append("```")

    if abstract:
        lines.append("---")
        lines.append("")
        lines.append("## Abstract")
        lines.append("")
        lines.append(abstract)
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Hugo publication bundles from BibTeX."
    )
    parser.add_argument(
        "--bib",
        default="bibliography/publications.bib",
        help="Path to a .bib file, or '-' to read BibTeX from stdin.",
    )
    parser.add_argument(
        "--entry",
        help="Inline BibTeX string (overrides --bib).",
    )
    parser.add_argument("--out", default="content/publications")
    parser.add_argument(
        "--clean-generated",
        action="store_true",
        help="Delete previously generated bundles (directories with a .generated_from_bib marker file).",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.clean_generated:
        for child in out_dir.iterdir():
            marker = child / ".generated_from_bib"
            if marker.is_file():
                shutil.rmtree(child)
                continue
            index_md = child / "index.md"
            if not index_md.is_file():
                continue
            txt = index_md.read_text(encoding="utf-8", errors="replace")
            if "generated_from_bib: true" in txt:
                shutil.rmtree(child)

    if args.entry:
        text = args.entry
    elif args.bib == "-":
        text = sys.stdin.read()
    else:
        bib_path = Path(args.bib)
        if not bib_path.exists():
            raise SystemExit(f"BibTeX not found: {bib_path}")
        text = bib_path.read_text(encoding="utf-8", errors="replace")
    entries = parse_bibtex(text)

    created = 0
    for entry in entries:
        title = entry.fields.get("title", entry.citekey)
        slug = _slugify(_unescape_basic_latex(title))
        year = entry.fields.get("year", "").strip()
        dirname = entry.citekey
        if not re.match(r"^[a-zA-Z0-9._-]+$", dirname):
            dirname = f"{year}-{slug}" if year else slug

        bundle_dir = out_dir / dirname
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "index.md").write_text(
            render_markdown(entry), encoding="utf-8", newline="\n"
        )
        (bundle_dir / ".generated_from_bib").write_text(
            f"{entry.citekey}\n", encoding="utf-8", newline="\n"
        )
        created += 1

    print(f"Generated {created} publication bundle(s) into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
