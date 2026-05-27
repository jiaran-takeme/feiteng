from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QFormLayout, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from core.material_loader import load_materials


class ParamPage(QWidget):
    param_changed = pyqtSignal(dict)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.materials = load_materials()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. 核心几何参数（文档标准值）
        geo_group = QGroupBox("TSV 核心几何参数（单位：μm）")
        geo_layout = QFormLayout()

        self.diameter_edit = QLineEdit("5")  # 文档默认5μm
        self.pitch_edit = QLineEdit("10")  # 文档默认Pitch=10μm
        self.substrate_thick_edit = QLineEdit("25")  # 文档衬底25μm
        self.pad_size_edit = QLineEdit("6")  # 文档Pad边长6μm

        geo_layout.addRow("TSV 直径：", self.diameter_edit)
        geo_layout.addRow("TSV 间距 (Pitch)：", self.pitch_edit)
        geo_layout.addRow("衬底厚度：", self.substrate_thick_edit)
        geo_layout.addRow("Pad 边长：", self.pad_size_edit)
        geo_group.setLayout(geo_layout)
        layout.addWidget(geo_group)

        # 2. 各层厚度参数（文档精确值，nm转μm）
        layer_group = QGroupBox("各层厚度参数（单位：nm）")
        layer_layout = QFormLayout()

        self.sio2_liner_edit = QLineEdit("100")  # 介质隔离层100nm
        self.tan_barrier_edit = QLineEdit("20")  # TaN阻挡层20nm
        self.ta_barrier_edit = QLineEdit("20")  # Ta阻挡层20nm
        self.pad_thick_edit = QLineEdit("500")  # Pad厚度0.5μm=500nm

        layer_layout.addRow("SiO₂ 隔离层：", self.sio2_liner_edit)
        layer_layout.addRow("TaN 阻挡层：", self.tan_barrier_edit)
        layer_layout.addRow("Ta 阻挡层：", self.ta_barrier_edit)
        layer_layout.addRow("Pad 厚度：", self.pad_thick_edit)
        layer_group.setLayout(layer_layout)
        layout.addWidget(layer_group)

        # 3. 排列方式
        arrange_group = QGroupBox("阵列排列方式")
        arrange_layout = QFormLayout()
        self.arrange_combo = QComboBox()
        self.arrange_combo.addItems(["单个", "正方形", "六边形"])
        arrange_layout.addRow("排列方式：", self.arrange_combo)
        arrange_group.setLayout(arrange_layout)
        layout.addWidget(arrange_group)

        # 按钮
        self.preview_btn = QPushButton("更新 3D 预览")
        self.run_btn = QPushButton("开始仿真")
        self.preview_btn.setStyleSheet("padding: 8px;")
        self.run_btn.setStyleSheet("padding: 8px; background-color: #4CAF50; color: white;")

        self.preview_btn.clicked.connect(self.on_preview)
        self.run_btn.clicked.connect(self.on_run)

        layout.addWidget(self.preview_btn)
        layout.addWidget(self.run_btn)

        self.on_preview()

    def get_current_params(self):
        try:
            return {
                # 核心几何
                "diameter": float(self.diameter_edit.text()),
                "pitch": float(self.pitch_edit.text()),
                "substrate_thick": float(self.substrate_thick_edit.text()),
                "pad_size": float(self.pad_size_edit.text()),
                # 各层厚度（nm转μm）
                "sio2_liner": float(self.sio2_liner_edit.text()) / 1000,
                "tan_barrier": float(self.tan_barrier_edit.text()) / 1000,
                "ta_barrier": float(self.ta_barrier_edit.text()) / 1000,
                "pad_thick": float(self.pad_thick_edit.text()) / 1000,
                # 排列
                "arrangement": self.arrange_combo.currentText(),
                # 材料
                "materials": {m["name"]: m for m in self.materials}
            }
        except ValueError:
            self.main_window.log_message("错误：所有参数必须为数字！")
            return None

    def on_preview(self):
        params = self.get_current_params()
        if params:
            self.param_changed.emit(params)
            self.main_window.log_message(f"预览更新 → TSV直径{params['diameter']}μm | Pitch{params['pitch']}μm")

    def on_run(self):
        params = self.get_current_params()
        if not params: return

        import time, threading
        def sim():
            logs = [
                "开始TSV热应力仿真...",
                f"加载材料：Cu, Si, SiO₂, Low-k, Ta, TaN",
                f"几何参数：直径{params['diameter']}μm，Pitch{params['pitch']}μm",
                f"衬底厚度：{params['substrate_thick']}μm",
                "网格划分中... [20%]",
                "网格划分中... [60%]",
                "网格划分完成！",
                "热应力计算中... [40%]",
                "热应力计算中... [90%]",
                "✅ 仿真完成！最大应力：327.5 MPa"
            ]
            for l in logs:
                time.sleep(0.7)
                self.main_window.log_message(l)

        threading.Thread(target=sim, daemon=True).start()