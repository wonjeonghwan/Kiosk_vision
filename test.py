import os

def print_project_structure(base_path, indent=0):
    for item in os.listdir(base_path):
        full_path = os.path.join(base_path, item)
        if os.path.isdir(full_path):
            print("  " * indent + f"📁 {item}/")
            print_project_structure(full_path, indent + 1)
        else:
            print("  " * indent + f"📄 {item}")

# 예: 여기에 네 프로젝트 최상위 폴더 경로를 넣어
print_project_structure("C:/Jeonghwan/4zo")
