from playwright.sync_api import sync_playwright
import os

def generate_pdf():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Load HTML file
        html_path = f"file://{os.path.abspath('/app/app/SYSTEM_ARCHITECTURE.html')}"
        print(f"Loading: {html_path}")
        page.goto(html_path)
        
        # Wait for Mermaid diagrams to render
        page.wait_for_selector('.mermaid svg', timeout=10000)
        
        # Generate PDF
        pdf_path = '/app/app/SYSTEM_ARCHITECTURE.pdf'
        page.pdf(
            path=pdf_path,
            format='A4',
            print_background=True,
            margin={'top': '20mm', 'bottom': '20mm', 'left': '20mm', 'right': '20mm'}
        )
        
        print(f"Successfully generated PDF at: {pdf_path}")
        browser.close()

if __name__ == "__main__":
    generate_pdf()
