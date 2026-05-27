from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
)
from core.material_loader import load_materials

class ParamPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("选择材料："))
        self.mat_combo = QComboBox()
        materials = load_materials()
        for mat in materials:
            self.mat_combo.addItem(mat["name"], mat)
        layout.addWidget(self.mat_combo)

        self.run_btn = QPushButton("开始仿真")
        self.run_btn.clicked.connect(self.on_run)
        layout.addWidget(self.run_btn)

        self.setLayout(layout)

    def on_run(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "提示", "前端：已收集参数，等待后端对接")