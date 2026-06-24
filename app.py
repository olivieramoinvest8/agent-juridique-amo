def recherche_brave(query):
    """Fait une recherche web avec Brave Search"""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {"q": query, "count": 5, "lang": "fr", "country": "FR"}
    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=10
        )
        data = response.json()
        resultats = []
        for r in data.get("web", {}).get("results", []):
            resultats.append(f"- {r.get('title', '')}: {r.get('description', '')}")
        return "\n".join(resultats)
    except Exception as e:
        return f"Erreur recherche: {str(e)}"
