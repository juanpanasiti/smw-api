import glob
import re


def process_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()

    modified = False
    in_def = False
    for i in range(len(lines)):
        line = lines[i]

        # Start of function def
        if re.match(r"^\s*(async\s+)?def\s+[a-zA-Z0-9_]+\(", line):
            in_def = True

        if in_def:
            # Check if this line closes the def
            # It ends with "):" possibly with some trailing whitespace
            if re.search(r"\):\s*$", line):
                lines[i] = re.sub(r"\):\s*$", ") -> Any:\n", line)
                modified = True
                in_def = False
            elif re.search(r"\)\s*->", line):
                # already has a return type
                in_def = False

    content = "".join(lines)
    if modified:
        if "from typing import " in content and "Any" not in content:
            content = content.replace("from typing import ", "from typing import Any, ", 1)
        elif "from typing import Any" not in content:
            content = "from typing import Any\n" + content
        with open(filepath, "w") as f:
            f.write(content)


for filepath in glob.glob("src/routes/*.py"):
    process_file(filepath)

print("Fixed routes")
