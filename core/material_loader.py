import json
import os

def load_materials():
    """从materials目录加载所有材料JSON"""
    mat_dir = os.path.join(os.path.dirname(__file__), "../materials")
    all_mats = []
    for fname in os.listdir(mat_dir):
        if fname.endswith(".json"):
            path = os.path.join(mat_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_mats.append(data)
    return all_mats