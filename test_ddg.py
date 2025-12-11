from duckduckgo_search import DDGS
import time

def test_search():
    ddgs = DDGS()
    queries = ["Tata Steel stock news", "TCS stock news", "Reliance stock news", "Infosys stock news"]
    
    # Re-writing the loop to try text() with backend='html'
    for q in queries:
        print(f"Searching for {q} (backend='html')...")
        try:
            # backend='html' is supported in text()
            results = ddgs.text(q, region="in-en", backend="html", max_results=5)
            print(f"Found {len(results)} results")
            for r in results:
                print(f" - {r['title']} ({r['href']})")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    test_search()
