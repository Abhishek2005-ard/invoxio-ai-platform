import os
files_info = []
for root, dirs, files in os.walk('agents'):
    if '.venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            files_info.append((path, len(lines)))

files_info.sort(key=lambda x: x[1], reverse=True)
for path, count in files_info:
    print(f"{path}: {count} lines")
