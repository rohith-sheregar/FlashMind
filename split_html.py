import os
import re

html_path = r"d:\PROJECTS\FlashMind\backend_flask\static\index.html"
css_dir = r"d:\PROJECTS\FlashMind\backend_flask\static\css"
js_dir = r"d:\PROJECTS\FlashMind\backend_flask\static\js"

os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract script
script_pattern = re.compile(r'<script>(.*?)</script>', re.DOTALL)
scripts = script_pattern.findall(content)

# We want the main script, there might be multiple (like the config script). 
# The main one has "mermaid.initialize" and "isLoginMode".
main_script = None
for s in scripts:
    if 'mermaid.initialize' in s or 'isLoginMode' in s:
        main_script = s
        break

# Extract style
style_pattern = re.compile(r'<style>(.*?)</style>', re.DOTALL)
styles = style_pattern.findall(content)
main_style = styles[0] if styles else None

if main_script and main_style:
    # Write to files
    import time
    version = int(time.time())
    
    with open(os.path.join(css_dir, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(main_style.strip())
        
    with open(os.path.join(js_dir, 'app.js'), 'w', encoding='utf-8') as f:
        f.write(main_script.strip())
        
    # Replace in HTML
    # We replace the literal tags with links
    # For style:
    content = content.replace(f'<style>{main_style}</style>', f'<link rel="stylesheet" href="/static/css/style.css?v={version}">')
    
    # For script:
    content = content.replace(f'<script>{main_script}</script>', f'<script src="/static/js/app.js?v={version}"></script>')
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Successfully split HTML into CSS and JS!")
else:
    print("Could not find main script or style tags")
