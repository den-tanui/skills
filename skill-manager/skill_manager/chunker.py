from __future__ import annotations
import ctypes
import re
from pathlib import Path
from typing import Dict, List, Optional

from .models import Chunk


_CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs",
                    ".sh", ".bash", ".java", ".c", ".h", ".cpp", ".hpp"}


def chunk_file(file_path: str) -> List[Chunk]:
    """Parse a file and return a list of Chunks using tree-sitter."""
    path = Path(file_path)
    if not path.exists():
        return []

    ext = path.suffix.lower()
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if ext in (".md", ".mdx"):
        return _chunk_markdown(content, file_path)
    elif ext in _CODE_EXTENSIONS:
        return _chunk_code(content, file_path, ext)
    else:
        return _chunk_fallback(content, file_path)


def _chunk_markdown(content: str, file_path: str) -> List[Chunk]:
    """Chunk markdown: extract frontmatter, split by h2, extract fenced code blocks."""
    chunks: List[Chunk] = []
    rel_path = _relative_path(file_path)

    # Extract YAML frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    body = content
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        chunks.append(Chunk(
            chunk_type="frontmatter",
            content=fm_text,
            content_preview=fm_text[:200],
            file_path=rel_path,
        ))
        body = content[frontmatter_match.end():]

    # Split body by h2 headings (## Title)
    sections = re.split(r"\n(##\s+.+)\n", "\n" + body)
    current_heading = ""
    current_text = ""

    for i, part in enumerate(sections):
        part = part.strip()
        if not part:
            continue
        if part.startswith("## "):
            if current_text.strip():
                _split_markdown_section(chunks, current_heading, current_text, rel_path)
            current_heading = part[3:].strip()
            current_text = ""
        else:
            current_text = part + "\n"

    if current_text.strip():
        _split_markdown_section(chunks, current_heading, current_text, rel_path)

    return chunks


def _split_markdown_section(chunks: List[Chunk], heading: str, text: str, rel_path: str):
    """Split a markdown section into prose + code block chunks."""
    heading_normalized = heading.lower().replace(" ", "-")
    section_type = f"section:{heading_normalized}" if heading else "section:body"

    code_blocks = list(re.finditer(r"```(\w*)\n(.*?)```", text, re.DOTALL))

    if not code_blocks:
        chunks.append(Chunk(
            chunk_type=section_type,
            section_heading=heading,
            content=text.strip(),
            file_path=rel_path,
        ))
        return

    last_end = 0
    for cb in code_blocks:
        lang = cb.group(1) or "text"
        before = text[last_end:cb.start()].strip()
        if before:
            chunks.append(Chunk(
                chunk_type=section_type,
                section_heading=heading,
                content=before,
                file_path=rel_path,
            ))
        code_content = cb.group(0)
        chunks.append(Chunk(
            chunk_type=f"code_block:{lang}",
            section_heading=heading,
            content=code_content,
            file_path=rel_path,
        ))
        last_end = cb.end()

    remaining = text[last_end:].strip()
    if remaining:
        chunks.append(Chunk(
            chunk_type=section_type,
            section_heading=heading,
            content=remaining,
            file_path=rel_path,
        ))


# Tree-sitter configuration and code chunking
_TS_CONFIG: Dict[str, Dict] = {
    ".py": {
        "lang": "python",
        "query": """
            (function_definition) @def
            (class_definition) @def
            (decorated_definition) @def
        """,
    },
    ".js": {
        "lang": "javascript",
        "query": """
            (function_declaration) @def
            (class_declaration) @def
            (lexical_declaration) @def
            (variable_declaration) @def
        """,
    },
    ".jsx": {"lang": "javascript", "query": """
            (function_declaration) @def
            (class_declaration) @def
            (lexical_declaration) @def
            (variable_declaration) @def
        """},
    ".ts": {
        "lang": "typescript",
        "query": """
            (function_declaration) @def
            (class_declaration) @def
            (interface_declaration) @def
            (type_alias_declaration) @def
            (arrow_function) @def
        """,
    },
    ".tsx": {"lang": "typescript", "query": """
            (function_declaration) @def
            (class_declaration) @def
            (interface_declaration) @def
            (type_alias_declaration) @def
            (arrow_function) @def
        """},
    ".go": {
        "lang": "go",
        "query": """
            (function_declaration) @def
            (method_declaration) @def
            (type_declaration) @def
        """,
    },
    ".rs": {
        "lang": "rust",
        "query": """
            (function_item) @def
            (struct_item) @def
            (impl_item) @def
            (trait_item) @def
            (enum_item) @def
        """,
    },
    ".sh": {
        "lang": "bash",
        "query": """
            (function_definition) @def
        """,
    },
    ".bash": {"lang": "bash", "query": """
            (function_definition) @def
        """},
}

_PARSER_CACHE: Dict[str, tuple] = {}
_LANGUAGE_LIB = None


def _get_language_lib():
    """Load the tree-sitter languages shared library."""
    global _LANGUAGE_LIB
    if _LANGUAGE_LIB is None:
        try:
            from tree_sitter_languages import core
            lib_path = Path(core.__file__).parent / "languages.so"
            _LANGUAGE_LIB = ctypes.CDLL(str(lib_path))
        except Exception:
            return None
    return _LANGUAGE_LIB


def _get_parser(lang: str):
    """Get or create a tree-sitter parser for the given language."""
    if lang not in _PARSER_CACHE:
        try:
            lib = _get_language_lib()
            if lib is None:
                return None
            from tree_sitter import Language, Parser

            func_name = f"tree_sitter_{lang}"
            func = getattr(lib, func_name, None)
            if func is None:
                return None
            func.restype = ctypes.c_void_p
            ptr = func()

            language = Language(ptr)
            parser = Parser(language)
            _PARSER_CACHE[lang] = (language, parser)
        except Exception:
            return None
    return _PARSER_CACHE[lang]


def _extract_def_name(node, content: str) -> str:
    """Extract the name of a function/class definition from its AST node."""
    for child in node.children:
        if child.type in ("name", "identifier", "function_name", "type"):
            return content[child.start_byte:child.end_byte]
    name_match = re.search(r"(?:def|class|func|fn|function)\s+(\w+)",
                           content[node.start_byte:node.start_byte + 200])
    return name_match.group(1) if name_match else ""


def _chunk_code(content: str, file_path: str, ext: str) -> List[Chunk]:
    """Chunk code files using tree-sitter AST."""
    config = _TS_CONFIG.get(ext)
    if not config:
        return _chunk_fallback(content, file_path)

    lang_name = config["lang"]
    parser_result = _get_parser(lang_name)
    if parser_result is None:
        return _chunk_fallback(content, file_path)

    language, parser = parser_result

    try:
        tree = parser.parse(bytes(content, "utf-8"))
    except Exception:
        return _chunk_fallback(content, file_path)

    root = tree.root_node

    rel_path = _relative_path(file_path)
    parent_dir = Path(file_path).parent.name if Path(file_path).parent else ""
    base_type = "script_file" if parent_dir in ("scripts", "script") else "reference_file"

    # Run query to find definitions
    from tree_sitter import Query
    from tree_sitter._binding import QueryCursor

    try:
        query = Query(language, config["query"])
    except Exception:
        return _chunk_fallback(content, file_path)

    cursor = QueryCursor(query)
    cursor.match_limit = 1000

    def_nodes: list = []
    try:
        for pattern_idx, captures_dict in cursor.matches(root):
            for node in captures_dict.get("def", []):
                # Only include top-level definitions (skip nested: methods, inner funcs)
                if node.parent and node.parent.type in ("module", "program", "source_file"):
                    def_nodes.append(node)
    except Exception:
        return _chunk_fallback(content, file_path)

    if not def_nodes:
        return _chunk_fallback(content, file_path)

    def_nodes.sort(key=lambda n: n.start_byte)

    chunks: List[Chunk] = []
    for node in def_nodes:
        chunk_content = content[node.start_byte:node.end_byte].strip()
        name = _extract_def_name(node, content)

        chunks.append(Chunk(
            chunk_type=base_type,
            section_heading=name or "",
            content=chunk_content,
            file_path=rel_path,
        ))

    return chunks if chunks else _chunk_fallback(content, file_path)


def _chunk_fallback(content: str, file_path: str) -> List[Chunk]:
    """Fallback: full file as one chunk for small files, line-based for large."""
    rel_path = _relative_path(file_path)
    lines = content.split("\n")
    if len(lines) <= 100:
        return [Chunk(
            chunk_type="reference_file",
            content=content,
            file_path=rel_path,
        )]
    chunks = []
    chunk_size = 50
    overlap = 10
    for i in range(0, len(lines), chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        chunk_text = "\n".join(chunk_lines)
        chunks.append(Chunk(
            chunk_type="reference_file",
            content=chunk_text,
            file_path=rel_path,
        ))
    return chunks


def _relative_path(file_path: str) -> str:
    """Extract a meaningful relative path hint."""
    return Path(file_path).name
