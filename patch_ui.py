import re

with open('front-end/index.html', 'r') as f:
    html = f.read()

# Remove uploadArea
html = re.sub(
    r'\s*<div class="upload-area glass" id="uploadArea">.*?</div>',
    '',
    html,
    flags=re.DOTALL
)

with open('front-end/index.html', 'w') as f:
    f.write(html)

with open('front-end/style.css', 'r') as f:
    css = f.read()

# Add solid background to upload-modal-panel
css = css.replace('.upload-modal-panel {', '.upload-modal-panel {\n    background: #1e1e2e;\n    border: 1px solid rgba(255,255,255,0.1);')

with open('front-end/style.css', 'w') as f:
    f.write(css)

print("UI Patched")
