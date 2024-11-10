# This file is in part derived from superqt CodeSyntaxHighlight
# (see https://github.com/pyapp-kit/superqt/blob/ac4adf523442e14049a56c012eeb23d0c2c3d314/src/superqt/utils/_code_syntax_highlight.py)
# Original Copyright (c) 2021, Talley Lambert, originally licensed under BSD-3-Clause

from qtpy import QtGui

import os
import collections

import pygments
from pygments import formatter
from pygments import lexers

from typstwriter import util

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


def get_lexer_by_name(name):
    """Get a lexer by name, if not found return “Null” lexer."""
    for lexer_name, _, _, _ in lexers.get_all_lexers(plugins=False):
        if lexer_name == name:
            return lexers.find_lexer_class(name)()
    return lexers.TextLexer()


def get_lexer_name_by_filename(path):
    """
    Get the name of a lexer for a filename.

    This is a simplified(but faster) alternative to pygments get_lexer_for_filename.
    """
    if not path:
        return None

    filename = os.path.basename(path)
    for name, _, filenames, _ in lexers.get_all_lexers(plugins=False):
        for f in filenames:
            if lexers._fn_matches(filename, f):
                return name
    return None


def available_lexers():
    """Return a list with the names of all available lexers."""
    return [name for name, _, _, _ in lexers.get_all_lexers(plugins=False)]


class QTextCharFormatter(formatter.Formatter):
    """pygments formatter using QTextCharFormat."""

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(**kwargs)
        self.token_map = collections.defaultdict(QtGui.QTextCharFormat)
        for token, _ in self.style:
            self.token_map[token] = self.get_format(token)

    def get_format(self, token):
        """Get QTextCharFormat for a token."""
        style = self.style.style_for_token(token)

        text_char_format = QtGui.QTextCharFormat()
        text_char_format.setFontFamilies(["monospace"])
        if style.get("color"):
            text_char_format.setForeground(QtGui.QColor(f"#{style['color']}"))
        if style.get("bgcolor"):
            text_char_format.setBackground(QtGui.QColor(f"#{style['bgcolor']}"))
        if style.get("bold"):
            text_char_format.setFontWeight(QtGui.QFont.Bold)
        if style.get("italic"):
            text_char_format.setFontItalic(True)
        if style.get("underline"):
            text_char_format.setFontUnderline(True)
        if style.get("border"):
            # TODO: implement border highlighting
            pass

        return text_char_format

    def format(self, tokensource, outfile):
        """
        Format the given token stream.

        `outfile` is needed from parent class, but is unused.
        """
        for token, value in tokensource:
            yield (self.token_map[token], util.qstring_length(value))


class CodeSyntaxHighlight(QtGui.QSyntaxHighlighter):
    """Generic syntax highlighter making use of pygments."""

    def __init__(self, parent, lexer, theme):
        """Init."""
        super().__init__(parent)
        self.formatter = QTextCharFormatter(style=theme)
        self.lexer = lexer

    @property
    def font_color(self):
        """Font color."""
        return self.formatter.style.styles[pygments.token.Token]

    @property
    def background_color(self):
        """Background color."""
        return self.formatter.style.background_color

    @property
    def highlight_color(self):
        """Highlight color."""
        return self.formatter.style.highlight_color

    @property
    def line_number_color(self):
        """Line number color."""
        return self.formatter.style.line_number_color

    @property
    def line_number_background_color(self):
        """Line number background color."""
        return self.formatter.style.line_number_background_color

    @property
    def line_number_special_color(self):
        """Line number special color."""
        return self.formatter.style.line_number_special_color

    @property
    def line_number_special_background_color(self):
        """Line number special background color."""
        return self.formatter.style.line_number_special_background_color

    def highlightBlock(self, text):  # This is an overriding function # noqa: N802
        """Highlight the given text block."""
        format_list = self.formatter.format(pygments.lex(text, self.lexer), None)
        start = 0
        for format, length in format_list:
            self.setFormat(start, length, format)
            start += length
