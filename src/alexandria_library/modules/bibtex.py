import requests

def get_bibtex_from_books(title_query):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"intitle:{title_query}", "maxResults": 1}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if "items" not in data or not data["items"]:
        return None
    book = data["items"][0]["volumeInfo"]
    title = book.get("title")
    authors = " and ".join(book.get("authors", []))
    publisher = book.get("publisher")
    year = book.get("publishedDate", "").split("-")[0]
    isbn = None
    for idd in book.get("industryIdentifiers", []):
        if idd.get("type") in ("ISBN_13", "ISBN_10"):
            isbn = idd.get("identifier")
            break
    key = (authors.split()[0] if authors else "book") + (year or "")
    bibtex = f"@book{{{key},\n  title={{ {title} }},\n  author={{ {authors} }},\n  publisher={{ {publisher} }},\n  year={{ {year} }},\n  isbn={{ {isbn} }}\n}}"
    return bibtex

if __name__ == "__main__":
    bib = get_bibtex_from_books("Introduction to Logic - Routledge 2016")
    print(bib)

