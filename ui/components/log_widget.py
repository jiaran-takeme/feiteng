from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel
)
from PyQt6.QtCore import Qt, QDateTime

class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # 标题
        title = QLabel("仿真日志")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        # 日志显示框
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)  # 只读
        self.log_edit.setStyleSheet("background-color: #f8f8f8;")
        layout.addWidget(self.log_edit)

    def append_log(self, msg):
        """添加日志信息（带时间戳）"""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        log_msg = f"[{timestamp}] {msg}\n"
        self.log_edit.append(log_msg)
        # 自动滚动到底部
        self.log_edit.verticalScrollBar().setValue(
            self.log_edit.verticalScrollBar().maximum()
        )