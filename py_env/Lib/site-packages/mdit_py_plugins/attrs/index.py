from typing import List, Optional

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from markdown_it.token import Token

from .parse import ParseError, parse


def attrs_plugin(
    md: MarkdownIt,
    *,
    after=("image", "code_inline", "link_close", "span_close"),
    spans=False,
    span_after="link",
):
    """Parse inline attributes that immediately follow certain inline elements::

        ![alt](https://image.com){#id .a b=c}

    This syntax is inspired by
    `Djot spans
    <https://htmlpreview.github.io/?https://github.com/jgm/djot/blob/master/doc/syntax.html#inline-attributes>`_.

    Inside the curly braces, the following syntax is possible:

    - `.foo` specifies foo as a class.
      Multiple classes may be given in this way; they will be combined.
    - `#foo` specifies foo as an identifier.
      An element may have only one identifier;
      if multiple identifiers are given, the last one is used.
    - `key="value"` or `key=value` specifies a key-value attribute.
       Quotes are not needed when the value consists entirely of
       ASCII alphanumeric characters or `_` or `:` or `-`.
       Backslash escapes may be used inside quoted values.
    - `%` begins a comment, which ends with the next `%` or the end of the attribute (`}`).

    Multiple attribute blocks are merged.

    :param md: The MarkdownIt instance to modify.
    :param after: The names of inline elements after which attributes may be specified.
        This plugin does not support attributes after emphasis, strikethrough or text elements,
        which all require post-parse processing.
    :param spans: If True, also parse attributes after spans of text, encapsulated by `[]`.
        Note Markdown link references take precedence over this syntax.
    :param span_after: The name of an inline rule after which spans may be specified.
    """

    def _attr_rule(state: StateInline, silent: bool):
        if state.pending or not state.tokens:
            return False
        token = state.tokens[-1]
        if token.type not in after:
            return False
        try:
            new_pos, attrs = parse(state.src[state.pos :])
        except ParseError:
            return False
        token_index = _find_opening(state.tokens, len(state.tokens) - 1)
        if token_index is None:
            return False
        state.pos += new_pos + 1
        if not silent:
            attr_token = state.tokens[token_index]
            if "class" in attrs and "class" in token.attrs:
                attrs["class"] = f"{attr_token.attrs['class']} {attrs['class']}"
            attr_token.attrs.update(attrs)
        return True

    if spans:
        md.inline.ruler.after(span_after, "span", _span_rule)
    md.inline.ruler.push("attr", _attr_rule)


def _find_opening(tokens: List[Token], index: int) -> Optional[int]:
    """Find the opening token index, if the token is closing."""
    if tokens[index].nesting != -1:
        return index
    level = 0
    while index >= 0:
        level += tokens[index].nesting
        if level == 0:
            return index
        index -= 1
    return None


def _span_rule(state: StateInline, silent: bool):
    if state.srcCharCode[state.pos] != 0x5B:  # /* [ */
        return False

    maximum = state.posMax
    labelStart = state.pos + 1
    labelEnd = state.md.helpers.parseLinkLabel(state, state.pos, False)

    # parser failed to find ']', so it's not a valid span
    if labelEnd < 0:
        return False

    pos = labelEnd + 1

    # check not at end of inline
    if pos >= maximum:
        return False

    try:
        new_pos, attrs = parse(state.src[pos:])
    except ParseError:
        return False

    pos += new_pos + 1

    if not silent:
        state.pos = labelStart
        state.posMax = labelEnd
        token = state.push("span_open", "span", 1)
        token.attrs = attrs
        state.md.inline.tokenize(state)
        token = state.push("span_close", "span", -1)

    state.pos = pos
    state.posMax = maximum
    return True
