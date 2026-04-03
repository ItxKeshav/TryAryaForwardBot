import ast
import os

plugins_dir = r"c:\Users\User\Downloads\AryaBotNew\TryAryaBot\plugins"
output_file = r"c:\Users\User\Downloads\AryaBotNew\TryAryaBot\tmp_analysis_out.txt"

with open(output_file, 'w', encoding='utf-8') as out:
    for filename in os.listdir(plugins_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(plugins_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                funcs = []
                handlers = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        funcs.append(node.name)
                        # Check decorators
                        for dec in node.decorator_list:
                            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                                if dec.func.attr in ['on_message', 'on_callback_query']:
                                    handlers.append((node.name, dec.func.attr))
                            elif isinstance(dec, ast.Attribute):
                                if dec.attr in ['on_message', 'on_callback_query']:
                                    handlers.append((node.name, dec.attr))
                
                out.write(f'\n--- {filename} ---\n')
                out.write(f'Total functions: {len(funcs)}\n')
                out.write(f'Handlers: {handlers}\n')
                
            except Exception as e:
                out.write(f'Error reading {filename}: {e}\n')
