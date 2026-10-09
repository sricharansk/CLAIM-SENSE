"""Split policy wording into clause chunks that keep page, section and clause metadata."""
import re
from dataclasses import dataclass

PAGE_RE = re.compile(r"<!--\s*page:\s*(\d+)\s*-->")
SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+(.+)$")
CLAUSE_RE = re.compile(r"^###\s+(\d+\.\d+)\s+(.+)$")
# Plain-text headings as they appear in extracted PDF text: "2. Coverage" and "2.2 Room Rent Limit".
TEXT_SECTION_RE = re.compile(r"^(\d{1,2})\.\s+([A-Z][A-Za-z ,&/()'-]{2,80})$")
TEXT_CLAUSE_RE = re.compile(r"^(\d{1,2}\.\d{1,2})\s+([A-Z][^.]{1,100})$")


@dataclass
class ClauseChunk:
    clause_ref: str
    title: str
    section: str
    page: int
    text: str


def parse_policy_markdown(markdown: str) -> list[ClauseChunk]:
    chunks: list[ClauseChunk] = []
    page, section = 1, ""
    current: dict | None = None
    body: list[str] = []

    def flush():
        if current is not None:
            text = " ".join(line.strip() for line in body if line.strip())
            if text:
                chunks.append(ClauseChunk(current["ref"], current["title"], current["section"], current["page"], text))

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if m := PAGE_RE.search(line):
            page = int(m.group(1))
            continue
        if m := SECTION_RE.match(line):
            flush()
            current, body = None, []
            section = f"{m.group(1)}. {m.group(2).strip()}"
            continue
        if m := CLAUSE_RE.match(line):
            flush()
            current, body = {"ref": m.group(1), "title": m.group(2).strip(), "section": section, "page": page}, []
            continue
        if current is not None and not line.startswith("#"):
            body.append(line)
    flush()
    return chunks


def parse_policy_pages(pages: list[str]) -> list[ClauseChunk]:
    """Same chunking for extracted PDF text, one string per page; the page number is the PDF page."""
    lines = []
    for n, text in enumerate(pages, start=1):
        lines.append(f"<!-- page: {n} -->")
        for raw in text.splitlines():
            line = raw.strip()
            if m := TEXT_SECTION_RE.match(line):
                lines.append(f"## {m.group(1)}. {m.group(2)}")
            elif m := TEXT_CLAUSE_RE.match(line):
                lines.append(f"### {m.group(1)} {m.group(2)}")
            else:
                lines.append(line)
    return parse_policy_markdown("\n".join(lines))
