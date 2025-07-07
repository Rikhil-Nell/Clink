from ddgs import DDGS

def search_indian_scope(query, max_results=10):
    # region='in-en' restricts results to India (English)
    with DDGS() as ddgs:
        results = ddgs.text(query, region='in-en', safesearch='Moderate', max_results=max_results)
        return list(results)

def main():
    print("DuckDuckGo Indian Search")
    query = input("Enter your search query: ").strip()
    if not query:
        print("No query entered. Exiting.")
        return

    print(f"\nSearching for '{query}' (India only)...\n")
    try:
        results = search_indian_scope(query)
        if not results:
            print("No results found.")
            return
        for i, res in enumerate(results, 1):
            print(f"{i}. {res['title']}\n   {res['href']}\n")
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    main()