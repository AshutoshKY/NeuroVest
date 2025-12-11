import markdown
import os

# Read the markdown file
with open('/app/app/SYSTEM_ARCHITECTURE.md', 'r') as f:
    text = f.read()

# Convert to HTML
html_content = markdown.markdown(
    text,
    extensions=['tables', 'fenced_code', 'nl2br']
)

# Post-process to fix Mermaid diagrams
# Convert <pre><code class="language-mermaid">...</code></pre> to <div class="mermaid">...</div>
import re
def replace_mermaid(match):
    content = match.group(1)
    # Unescape HTML entities
    content = content.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    return f'<div class="mermaid">{content}</div>'

html_content = re.sub(
    r'<pre><code class="language-mermaid">(.*?)</code></pre>',
    replace_mermaid,
    html_content,
    flags=re.DOTALL
)

# HTML Template with CSS for printing and Mermaid support
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>System Architecture</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
            background: white;
        }}
        @media print {{
            body {{
                padding: 0;
                margin: 0;
            }}
            @page {{
                size: A4;
                margin: 20mm;
            }}
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 30px; }}
        code {{ background: #f8f9fa; padding: 2px 5px; border-radius: 3px; font-family: Consolas, monospace; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #e9ecef; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .mermaid {{ margin: 20px 0; text-align: center; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

# Write HTML file
with open('/app/app/SYSTEM_ARCHITECTURE.html', 'w') as f:
    f.write(html_template)

print("Successfully generated SYSTEM_ARCHITECTURE.html")
