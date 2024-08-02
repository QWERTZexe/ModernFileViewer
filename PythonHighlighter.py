from PyQt6.QtCore import QRegularExpression 
from PyQt6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QFont

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else", "except",
                    "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None",
                    "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield"]
        for word in keywords:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((QRegularExpression(pattern), keyword_format))

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))

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
            QRegularExpression(r"\'.*?\'")
        ]
        for expression in expressions:
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.string_format)

    def highlightComments(self, text):
        expression = QRegularExpression(r'#[^\n]*')
        it = expression.globalMatch(text)
        while it.hasNext():
            match = it.next()
            start = match.capturedStart()
            if self.format(start) != self.string_format:
                self.setFormat(start, match.capturedLength(), self.comment_format)