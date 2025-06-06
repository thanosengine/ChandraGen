import re

from chandragen.formatters.registry import register_line_formatter
from chandragen.formatters.types import FormatterFlags as Flags
from chandragen.formatters.types import LineFormatter


# Internal line formatters:
# Markdown Converters
@register_line_formatter
class StripInlineMarkdown(LineFormatter):
    def __init__(self):
        super().__init__(
            "strip_inline_md_formatting",
            """
    Strip inline markdown formatting:
    
    Strips all inline markdown bold and italic sequences
    naive approach, may cause issues.
    does not affect preformatted text/codeblocks
            """,
            ["md", "mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        if flags.in_preformat:
            return line
        # set up a regex method to remove inline markdown
        inline_md_replacements = {
            "*": "",
            "**": "",
            "***": "",
            "_": "",
            "__": "",
            "___": "",
        }
        inline_md_pattern = re.compile("|".join(re.escape(old) for old in inline_md_replacements))
        # regex it all out
        return f"{line[0:2]}{inline_md_pattern.sub(lambda match: inline_md_replacements[match.group(0)], line[2:])}"


@register_line_formatter
class StripHTMLComments(LineFormatter):
    def __init__(self):
        super().__init__(
            "strip_html_comments",
            """
    Strip HTML Comments
    
    Removes all lines starting with "<!--" and ending with "-->"
        """,
            ["md", "mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        if line.startswith("<!--") and line.endswith("-->\n"):
            return ""
        return line


@register_line_formatter
class ConvertBulletPointLinks(LineFormatter):
    def __init__(self):
        super().__init__(
            "convert_bullet_point_links",
            """
    Convert Bullet Point Links
    
    takes markdown style links immediately following a bullet point,
    and converts them into a gemini link-line.
            """,
            ["md", "mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        # Convert "- [label](url)" markdown link lines to "=> url label" gemtext links
        if line.startswith("- ["):
            # strip the first 3 characters "- [" off the line, then break it in half at the ](
            link = line[3:].split("](")
            # Since we have to flip the fields around, we also need to strip the newline and add one at the end.
            return f"=> {link[1].replace(')\n', '')} {link[0]}\n"
        return line


@register_line_formatter
class ConvertInlineLinks(LineFormatter):
    def __init__(self):
        super().__init__(
            "convert_inline_links",
            """
    Convert Inline Links
    
    Find inline markdown links, replace them with `<label>(below)`
    and then add a converted gemini link-line to the line buffer
        """,
            ["md", "mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        if line.startswith("- ["):
            # This is a bullet point link, there's a dedicated formatter for those. leave it alone.
            return line
        link_regex = re.compile(r"\[(?P<label>[^\\]+)\]\((?P<url>[^)]+)\)")
        matches: list[tuple[str, str, int, int]] = []
        for match in link_regex.finditer(line):
            label = match.group("label")
            url = match.group("url")
            start = match.start()
            end = match.end()
            matches.append((label, url, start, end))
        if not matches:
            return line
        flags.buffer_until_empty_line += [f"=> {url} {label}\n" for label, url, _start, _end in matches]

        formatted_string: str = ""
        last_index: int = 0
        for label, _url, start, end in matches:
            formatted_string += line[last_index:start]
            formatted_string += f"{label} (see below) "
            last_index = end

        return formatted_string + line[last_index:]


@register_line_formatter
class NormalizeCodeBlocks(LineFormatter):
    def __init__(self):
        super().__init__(
            "normalize_code_blocks",
            """
    Normalize codeblocks
    
    Strip out any characters defining a language on a code-block
    ensures compatibility with the gemini preformatted text block standard.
            """,
            ["md", "mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        return line if not line.startswith("```") else "```\n"


# MDX Converter
@register_line_formatter
class StripImportsExports(LineFormatter):
    def __init__(self):
        super().__init__(
            "strip_imports_exports",
            """
    Strip Imports and Exports
    
    Remove the line if it's a JSX import or export.
            """,
            ["mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        if line.strip().startswith(("import ", "export ")):
            return ""
        return line


@register_line_formatter
class StripJSXTags(LineFormatter):
    def __init__(self):
        super().__init__(
            "strip_jsx_tags",
            """
    Strip JSX Tags
    
    Naively remove lines starting with < and containing > that aren't DOCTYPE or HTML style comments.
    This should also remove some HTML tags, but not very well.
    Note: This formatter may cause isues with some multi-line formatting
            """,
            ["mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        clean_line = line.strip()
        if clean_line.startswith("<") and ">" in clean_line and not clean_line.startswith(("<!--", "<!DOCTYPE")):
            return ""
        return line


@register_line_formatter
class StripJSXExpressions(LineFormatter):
    def __init__(self):
        super().__init__(
            "strip_jsx_expressions",
            """
    Strip JSX expressions
    
    Naively strips out anything enclosed by curly braces.
    This will probably break your site.
    If you want to substitute them properly, set up a plugin formatter that does so, see the plugin example :3
        """,
            ["mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        return re.sub(r"{.*?}", "", line)


@register_line_formatter
class ConvertKnownMDXComponents(LineFormatter):
    def __init__(self):
        super().__init__(
            "convert_known_mdx_components",
            """
    Convert Known MDX components
    
    If a line is an MDX note or warning, replace with a basic NOTE: or WARNING:
            """,
            ["mdx"],
        )

    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    def apply(self, line: str, flags: Flags) -> str:
        component_map = {"<Note>": "NOTE:", "</Note>": "", "<Warning>": "WARNING:", "</Warning>": ""}
        for jsx, gem in component_map.items():
            line = line.replace(jsx, gem)
        return line
