def recherche_brave(query):
    """Fait une recherche web avec DuckDuckGo"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            headers=headers,
            params=params,
            timeout=10
        )
        data = response.json()
        resultats = []
        for r in data.get("RelatedTopics", [])[:5]:
            if "Text" in r:
                resultats.append(f"- {r.get('Text', '')}")
        if not resultats:
            resultats.append(f"Recherche effectuée sur: {query}")
        return "\n".join(resultats)
    except Exception as e:
        return f"Erreur recherche: {str(e)}"
