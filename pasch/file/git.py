from .file import File
from .text import TextFile

type GitSection = str | tuple[str, str]
type GitValue = bool | int | str


def _format_header(section: GitSection) -> str:
    if isinstance(section, str):
        title, subsection = section, None
    else:
        title, subsection = section

    # Section names are case-insensitive. Only alphanumeric characters, `-` and
    # `.` are allowed in section names. However, the `[section.subsection]`
    # syntax is deprecated, so we don't allow `.` in section names.
    assert title
    assert all(c.isascii() and (c.isalnum() or c == "-") for c in title)
    section = title.lower()

    if subsection is None:
        return f"[{section}]"

    # Subsection names are case sensitive and can contain any characters
    # except newline and the null byte. Doublequote `"` and backslash can
    # be included by escaping them as `\"` and `\\`, respectively.
    assert subsection
    for c in subsection:
        assert c not in {"\n", "\0"}

    escaped = "".join({'"': '\\"', "\\": "\\\\"}.get(c, c) for c in subsection)
    return f'[{section} "{escaped}"]'


def _format_name(name: str) -> str:
    # The variable names are case-insensitive, allow only alphanumeric
    # characters and `-`, and must start with an alphabetic character.
    assert name
    assert all(c.isascii() and (c.isalnum() or c == "-") for c in name)
    assert name[0].isalpha()

    return name


def _format_value(value: GitValue) -> str:
    # https://git-scm.com/docs/git-config#_values
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)

    # If a value needs to contain leading or trailing whitespace characters, it
    # must be enclosed in double quotation marks (`"`). Inside double quotation
    # marks, double quote (`"`) and backslash (`\`) characters must be escaped:
    # use `\"` for `"` and `\\` for `\`.
    #
    # The following escape sequences (beside `\"` and `\\`) are recognized: `\n`
    # for newline character (NL), `\t` for horizontal tabulation (HT, TAB) and
    # `\b` for backspace (BS). Other char escape sequences (including octal
    # escape sequences) are invalid.
    escapes = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\t": "\\t", "\b": "\\b"}
    escaped = "".join(escapes.get(c, c) for c in value)
    return f'"{escaped}"'


class GitFile(File):
    """
    A `.gitconfig` file.

    <https://git-scm.com/docs/git-config#_configuration_file>
    """

    def __init__(self, data: dict[GitSection, dict[str, GitValue]] = {}) -> None:
        self.data = data

    def set(self, section: GitSection, name: str, value: GitValue) -> None:
        self.data.setdefault(section, {})[name] = value

    def to_text(self) -> TextFile:
        file = TextFile()

        for section, values in sorted(self.data.items()):
            # Separate sections with an empty line
            if file.data:
                file.append("")

            file.append(_format_header(section))
            for name, value in sorted(values.items()):
                file.append(f"    {_format_name(name)} = {_format_value(value)}")

        file.tag(comment="#")
        return file

    def to_bytes(self) -> bytes:
        return self.to_text().to_bytes()
