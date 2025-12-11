#!/usr/bin/env python3
"""
Generate PDFs from Markdown files using Playwright
"""
import asyncio
import markdown
import os

async def generate_pdf(html_path: str, pdf_path: str):
    """Generate PDF from HTML file using Playwright"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Load the HTML file
        await page.goto(f"file://{html_path}")
        await page.wait_for_load_state("networkidle")
        
        # Generate PDF
        await page.pdf(
            path=pdf_path,
            format="A4",
            margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"},
            print_background=True
        )
        
        await browser.close()
        print(f"✅ Generated: {pdf_path}")

def md_to_html(md_content: str, title: str) -> str:
    """Convert markdown to styled HTML"""
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'toc', 'nl2br']
    )
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #333;
            max-width: 100%;
            padding: 20px;
        }}
        h1 {{
            color: #1a365d;
            border-bottom: 3px solid #3182ce;
            padding-bottom: 8px;
            font-size: 22pt;
        }}
        h2 {{
            color: #2c5282;
            border-bottom: 2px solid #90cdf4;
            padding-bottom: 5px;
            margin-top: 25px;
            font-size: 16pt;
            page-break-after: avoid;
        }}
        h3 {{
            color: #2b6cb0;
            font-size: 12pt;
            margin-top: 20px;
        }}
        h4 {{
            color: #3182ce;
            font-size: 11pt;
        }}
        code {{
            background-color: #f0f4f8;
            border: 1px solid #d1d5db;
            border-radius: 3px;
            padding: 1px 4px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 8pt;
        }}
        pre {{
            background-color: #1e293b;
            color: #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            overflow-x: auto;
            font-size: 8pt;
            line-height: 1.4;
            page-break-inside: avoid;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        pre code {{
            background: none;
            border: none;
            padding: 0;
            color: #e2e8f0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }}
        th {{
            background: linear-gradient(135deg, #3182ce, #2c5282);
            color: white;
            padding: 8px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            border: 1px solid #e2e8f0;
            padding: 6px 8px;
        }}
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        blockquote {{
            border-left: 4px solid #ed8936;
            background-color: #fffaf0;
            padding: 12px 15px;
            margin: 15px 0;
            border-radius: 0 6px 6px 0;
        }}
        ul, ol {{
            margin-left: 15px;
        }}
        li {{
            margin: 4px 0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 25px 0;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

async def main():
    base_dir = "/Volumes/AshDrive/prjts/stockmarket"
    
    files = [
        ("STOXO_DEEP_ARCHITECTURE_ANALYSIS.md", "STOXO_DEEP_ARCHITECTURE_ANALYSIS.pdf"),
        ("STOXO_API_ENDPOINTS_ANALYSIS.md", "STOXO_API_ENDPOINTS_ANALYSIS.pdf"),
    ]
    
    for md_file, pdf_file in files:
        md_path = os.path.join(base_dir, md_file)
        pdf_path = os.path.join(base_dir, pdf_file)
        html_path = os.path.join(base_dir, md_file.replace('.md', '_temp.html'))
        
        if not os.path.exists(md_path):
            print(f"❌ File not found: {md_path}")
            continue
        
        print(f"📄 Processing: {md_file}")
        
        # Read markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert to HTML
        title = md_file.replace('.md', '').replace('_', ' ')
        html_content = md_to_html(md_content, title)
        
        # Save temporary HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate PDF
        await generate_pdf(html_path, pdf_path)
        
        # Clean up temp file
        os.remove(html_path)
    
    print("\n🎉 PDF generation complete!")

if __name__ == "__main__":
    asyncio.run(main())
