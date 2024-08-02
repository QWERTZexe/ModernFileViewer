from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class KotlinHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "as", "as?", "break", "class", "continue", "do", "else", "false", "for", "fun", "if", "in", "interface",
            "is", "null", "object", "package", "return", "super", "this", "throw", "true", "try", "typealias", "val",
            "var", "when", "while", "by", "catch", "constructor", "delegate", "dynamic", "field", "file", "finally",
            "get", "import", "init", "param", "property", "receiver", "set", "setparam", "where", "actual", "abstract",
            "annotation", "companion", "const", "crossinline", "data", "enum", "expect", "external", "final", "infix",
            "inline", "inner", "internal", "lateinit", "noinline", "open", "operator", "out", "override", "private",
            "protected", "public", "reified", "sealed", "suspend", "tailrec", "vararg"
        ]
        for word in keywords:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((QRegularExpression(pattern), keyword_format))

        # String format
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        # Comment format
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\b'), number_format))

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), function_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.highlightStrings(text)
        self.highlightComments(text)

    def highlightStrings(self, text):
        expressions = [
            QRegularExpression(r'\".*?\"'),
            QRegularExpression(r"\'.*?\'"),
            QRegularExpression(r'""".*?"""', QRegularExpression.PatternOption.DotMatchesEverythingOption)
        ]
        for expression in expressions:
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.string_format)

    def highlightComments(self, text):
        single_line_comment_exp = QRegularExpression(r'//[^\n]*')
        multi_line_comment_exp = QRegularExpression(r'/\*.*?\*/', QRegularExpression.PatternOption.DotMatchesEverythingOption)

        it = single_line_comment_exp.globalMatch(text)
        while it.hasNext():
            match = it.next()
            start = match.capturedStart()
            if self.format(start) != self.string_format:
                self.setFormat(start, match.capturedLength(), self.comment_format)

        it = multi_line_comment_exp.globalMatch(text)
        while it.hasNext():
            match = it.next()
            start = match.capturedStart()
            if self.format(start) != self.string_format:
                self.setFormat(start, match.capturedLength(), self.comment_format)

        # Handle multi-line comments that span multiple blocks
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = text.find("/*")

        while start_index >= 0:
            end_index = text.find("*/", start_index)
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + 2
            self.setFormat(start_index, comment_length, self.comment_format)
            start_index = text.find("/*", start_index + comment_length)
