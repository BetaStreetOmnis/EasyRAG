"""Field list plugin"""
from contextlib import contextmanager
from typing import Tuple

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock


def fieldlist_plugin(md: MarkdownIt):
    """Field lists are mappings from field names to field bodies, based on the
    `reStructureText syntax
    <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#field-lists>`_.

    .. code-block:: md

        :name *markup*:
        :name1: body content
        :name2: paragraph 1

                paragraph 2
        :name3:
          paragraph 1

          paragraph 2

    A field name may consist of any characters except colons (":").
    Inline markup is parsed in field names.

    The field name is followed by whitespace and the field body.
    The field body may be empty or contain multiple body elements.
    The field body is aligned either by the start of the body on the first line or,
    if no body content is on the first line, by 2 spaces.
    """
    md.block.ruler.before(
        "paragraph",
        "fieldlist",
        _fieldlist_rule,
        {"alt": ["paragraph", "reference", "blockquote"]},
    )


def parseNameMarker(state: StateBlock, startLine: int) -> Tuple[int, str]:
    """Parse field name: `:name:`

    :returns: position after name marker, name text
    """
    start = state.bMarks[startLine] + state.tShift[startLine]
    pos = start
    maximum = state.eMarks[startLine]

    # marker should have at least 3 chars (colon + character + colon)
    if pos + 2 >= maximum:
        return -1, ""

    # first character should be ':'
    if state.src[pos] != ":":
        return -1, ""

    # scan name length
    name_length = 1
    found_close = False
    for ch in state.src[pos + 1 :]:
        if ch == "\n":
            break
        if ch == ":":
            # TODO backslash escapes
            found_close = True
            break
        name_length += 1

    if not found_close:
        return -1, ""

    # get name
    name_text = state.src[pos + 1 : pos + name_length]

    # name should contain at least one character
    if not name_text.strip():
        return -1, ""

    return pos + name_length + 1, name_text


@contextmanager
def set_parent_type(state: StateBlock, name: str):
    """Temporarily set parent type to `name`"""
    oldParentType = state.parentType
    state.parentType = name
    yield
    state.parentType = oldParentType


def _fieldlist_rule(state: StateBlock, startLine: int, endLine: int, silent: bool):
    # adapted from markdown_it/rules_block/list.py::list_block

    # if it's indented more than 3 spaces, it should be a code block
    if state.sCount[startLine] - state.blkIndent >= 4:
        return False

    posAfterName, name_text = parseNameMarker(state, startLine)
    if posAfterName < 0:
        return False

    # For validation mode we can terminate immediately
    if silent:
        return True

    # start field list
    token = state.push("field_list_open", "dl", 1)
    token.attrSet("class", "field-list")
    token.map = listLines = [startLine, 0]

    # iterate list items
    nextLine = startLine

    with set_parent_type(state, "fieldlist"):

        while nextLine < endLine:

            # create name tokens
            token = state.push("fieldlist_name_open", "dt", 1)
            token.map = [startLine, startLine]
            token = state.push("inline", "", 0)
            token.map = [startLine, startLine]
            token.content = name_text
            token.children = []
            token = state.push("fieldlist_name_close", "dt", -1)

            # set indent positions
            pos = posAfterName
            maximum = state.eMarks[nextLine]
            offset = (
                state.sCount[nextLine]
                + posAfterName
                - (state.bMarks[startLine] + state.tShift[startLine])
            )

            # find indent to start of body on first line
            while pos < maximum:
                ch = state.srcCharCode[pos]

                if ch == 0x09:  # \t
                    offset += 4 - (offset + state.bsCount[nextLine]) % 4
                elif ch == 0x20:  # \s
                    offset += 1
                else:
                    break

                pos += 1

            contentStart = pos

            # set indent for body text
            if contentStart >= maximum:
                # no body on first line, so use constant indentation
                # TODO adapt to indentation of subsequent lines?
                indent = 2
            else:
                indent = offset

            # Run subparser on the field body
            token = state.push("fieldlist_body_open", "dd", 1)
            token.map = itemLines = [startLine, 0]

            # change current state, then restore it after parser subcall
            oldTShift = state.tShift[startLine]
            oldSCount = state.sCount[startLine]
            oldBlkIndent = state.blkIndent

            state.tShift[startLine] = contentStart - state.bMarks[startLine]
            state.sCount[startLine] = offset
            state.blkIndent = indent

            state.md.block.tokenize(state, startLine, endLine)

            state.blkIndent = oldBlkIndent
            state.tShift[startLine] = oldTShift
            state.sCount[startLine] = oldSCount

            token = state.push("fieldlist_body_close", "dd", -1)

            nextLine = startLine = state.line
            itemLines[1] = nextLine

            if nextLine >= endLine:
                break

            contentStart = state.bMarks[startLine]

            # Try to check if list is terminated or continued.
            if state.sCount[nextLine] < state.blkIndent:
                break

            # if it's indented more than 3 spaces, it should be a code block
            if state.sCount[startLine] - state.blkIndent >= 4:
                break

            # get next field item
            posAfterName, name_text = parseNameMarker(state, startLine)
            if posAfterName < 0:
                break

        # Finalize list
        token = state.push("field_list_close", "dl", -1)
        listLines[1] = nextLine
        state.line = nextLine

    return True
