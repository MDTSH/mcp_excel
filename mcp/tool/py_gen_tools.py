import os

from mcp.tool.args_def import tool_def

cur_folder = os.path.split(os.path.realpath(__file__))[0] + "/"
py_file = "tools_main.py"
# py_file = "test.py"
fs = open(cur_folder + py_file, "w")

s_import = """
from mcp.tool.args_def import tool_def
"""

s_line = '\n\n\n'
fs.write(s_import)
fs.write(s_line)

for key in tool_def.item_dict:
    item_def = tool_def.get_item(key)
    init_func_name = item_def.key
    fmt = item_def.get_fmt()
    init_py = f"def {init_func_name}(*args):\n\treturn tool_def.tool_create('{init_func_name}', args)"
    print(init_py)
    fs.write(init_py)
    fs.write(s_line)

fs.close()
