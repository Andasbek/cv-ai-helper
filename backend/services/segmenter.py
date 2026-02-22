import re

# Section keywords mapped to canonical section names
SECTION_PATTERNS = [
    ("contacts", [
        r"contact(s|\ info(rmation)?)?",
        r"personal\ (info(rmation)?|details?)",
        r"phone|email|linkedin|github|address",
    ]),
    ("summary", [
        r"(professional\ )?summary",
        r"(about|objective|profile|overview)(\ me)?",
        r"career\ (objective|profile|summary)",
    ]),
    ("skills", [
        r"(technical\ |core\ |key\ )?skills?",
        r"technologies?",
        r"competenc(y|ies)",
        r"expertise",
        r"tools?\ (and\ technologies?)?",
    ]),
    ("experience", [
        r"(work|professional|employment)\ (experience|history)",
        r"experience",
        r"positions?\ held",
        r"career\ history",
    ]),
    ("education", [
        r"education(al\ background)?",
        r"academic(s|\ background)?",
        r"degrees?",
        r"qualifications?",
        r"university|college|school",
    ]),
    ("projects", [
        r"projects?",
        r"portfolio",
        r"personal\ projects?",
        r"open[ -]source",
    ]),
    ("certifications", [
        r"certifications?",
        r"certificates?",
        r"licenses?",
        r"credentials?",
        r"courses?",
        r"training",
    ]),
    ("languages", [
        r"languages?",
        r"linguistic(s)?",
    ]),
]


def _build_pattern():
    """Build a compiled regex that matches any section header."""
    all_keywords = []
    for _, patterns in SECTION_PATTERNS:
        all_keywords.extend(patterns)
    joined = "|".join(all_keywords)
    # Match a line that IS a section header: short, has one of our keywords,
    # optionally ending with colon, possibly in ALL CAPS
    return re.compile(
        rf"^[ \t]*(?P<header>(?:{joined})[:\s]*)[ \t]*$",
        re.IGNORECASE | re.MULTILINE,
    )


_SECTION_RE = _build_pattern()


def _classify_header(header_text: str) -> str:
    text = header_text.lower().strip()
    for section_name, patterns in SECTION_PATTERNS:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return section_name
    return "other"


def segment_cv(text: str) -> dict[str, str]:
    """
    Split CV text into named sections.
    Returns dict: section_name -> content string.
    The first block (before any recognised header) is treated as 'contacts'.
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {}
    current_section = "contacts"
    sections[current_section] = []

    for line in lines:
        match = _SECTION_RE.match(line)
        if match:
            header_text = match.group("header")
            section_name = _classify_header(header_text)
            current_section = section_name
            if section_name not in sections:
                sections[section_name] = []
            # Don't add the header line itself to content
        else:
            sections.setdefault(current_section, []).append(line)

    # Clean up each section
    result = {}
    for name, content_lines in sections.items():
        content = "\n".join(content_lines).strip()
        if content:
            result[name] = content

    return result
