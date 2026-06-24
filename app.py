import anthropic
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
app = Flask(__name__)

HTML_PAGE = (
    "<!DOCTYPE html>"
    "<html lang='fr'>"
    "<head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
    "<title>Juriste AMO Invest</title>"
    "<style>"
    "* { margin: 0; padding: 0; box-sizing: border-box; }"
    "body { font-family: Segoe UI, sans-serif; background: #f0f4f8; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }"
    ".header { text-align: center; margin-bottom: 30px; }"
    ".header h1 { color: #1a365d; font-size: 28px; margin-bottom: 8px; }"
    ".header p { color: #4a5568; font-size: 15px; }"
    ".chat-container { width: 100%; max-width: 800px; background: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }"
    ".messages { height: 500px; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }"
    ".message { max-width: 80%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; }"
    ".user-msg { background: #1a365d; color: white; align-self: flex-end; }"
    ".assistant-msg { background: #f7fafc; color: #2d3748; align-self: flex-start; border: 1px solid #e2e8f0; }"
    ".loading-msg { background: #f7fafc; color: #718096; align-self: flex-start; border: 1px solid #e2e8f0; font-style: italic; }"
    ".input-zone { padding: 20px; border-top: 1px solid #e2e8f0; display: flex; gap: 12px; }"
    "textarea { flex: 1; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 14px; resize: none; height: 60px; font-family: inherit; outline: none; }"
    "textarea:focus { border-color: #1a365d; }"
    ".send-btn { background: #1a365d; color: white; border: none; border-radius: 10px; padding: 0 24px; font-size: 14px; font-weight: 600; cursor: pointer; }"
    ".send-btn:hover { background: #2a4a7f; }"
    ".send-btn:disabled { background: #a0aec0; cursor: not-allowed; }"
    ".veille-btn { margin-top: 16px; background: #276749; padding: 10px 20px; border-radius: 8px; color: white; border: none; cursor: pointer; font-size: 13px; }"
    ".footer { margin-top: 16px; color: #718096; font-size: 12px; }"
    "</style>"
    "</head>"
    "<body>"
    "<div class='header'>"
    "<h1>Juriste AMO Invest</h1>"
    "<p>Votre expert juridique immobilier disponible 24h/24</p>"
    "</div>"
    "<div class='chat-container'>"
    "<div class='messages' id='messages'>"
    "<div class='message assistant-msg'>Bonjour, je suis votre juriste specialise en droit immobilier, transaction, location et urbanisme. Posez-moi votre question.</div>"
    "</div>"
    "<div class='input-zone'>"
    "<textarea id='question' placeholder='Posez votre question juridique...'></textarea>"
    "<button class='send-btn' id='btn'>Envoyer</button>"
    "</div>"
    "</div>"
    "<button class='veille-btn' id='veilleBtn'>Lancer la veille juridique maintenant</button>"
    "<div class='footer'>AMO Invest - Graveson (13) - Usage interne uniquement</div>"
    "<script>"
    "document.getElementById('question').addEventListener('keydown', function(e) {"
    "if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); document.getElementById('btn').click(); }"
    "});"
    "document.getElementById('btn').addEventListener('click', function() {"
    "var question = document.getElementById('question').value.trim();"
    "if (!question) return;"
    "var messagesDiv = document.getElementById('messages');"
    "var btn = document.getElementById('btn');"
    "var userDiv = document.createElement('div');"
    "userDiv.className = 'message user-msg';"
    "userDiv.textContent = question;"
    "messagesDiv.appendChild(userDiv);"
    "var loadingDiv = document.createElement('div');"
    "loadingDiv.className = 'message loading-msg';"
    "loadingDiv.id = 'loading';"
    "loadingDiv.textContent = 'Analyse en cours...';"
    "messagesDiv.appendChild(loadingDiv);"
    "document.getElementById('question').value = '';"
    "btn.disabled = true;"
    "messagesDiv.scrollTop = messagesDiv.scrollHeight;"
    "fetch('/question', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question: question}) })"
    ".then(function(r) { return r.json(); })"
    ".then(function(data) {"
    "var l = document.getElementById('loading'); if (l) l.remove();"
    "var d = document.createElement('div'); d.className = 'message assistant-msg'; d.textContent = data.reponse;"
    "messagesDiv.appendChild(d); btn.disabled = false; messagesDiv.scrollTop = messagesDiv.scrollHeight;"
    "})"
    ".catch(function() {"
    "var l = document.getElementById('loading'); if (l) l.remove();"
    "var d = document.createElement('div'); d.className = 'message assistant-msg'; d.textContent = 'Erreur de connexion. Reessayez.';"
    "messagesDiv.appendChild(d); btn.disabled = false;"
    "});"
    "});"
    "document.getElementById('veilleBtn').addEventListener('click', function() {"
    "if (!confirm('Lancer la veille juridique ? Un email vous sera envoye.')) return;"
    "var btn = document.getElementById('veilleBtn');"
    "btn.disabled = true; btn.textContent = 'Veille en cours...';"
    "fetch('/veille', { method: 'POST' })"
    ".then(function(r) { return r.json(); })"
    ".then(function(data) { alert(data.message); btn.disabled = false; btn.textContent = 'Lancer la veille juridique maintenant'; })"
    ".catch(function() { alert('Erreur.'); btn.disabled = false; btn.textContent = 'Lancer la veille juridique maintenant'; });"
    "});"
    "</script>"
    "</body>"
    "</html>"
)

SYSTEME_JURIDIQUE = (
    "Tu es un expert juridique senior specialise en droit immobilier francais, "
    "droit de la transaction, droit de la location, droit de l urbanisme et fiscalite immobiliere. "
    "Tu travailles exclusivement pour AMO Invest, agence immobiliere a Graveson (13690). "
    "Tu reponds avec la precision d un avocat specialise, en citant les textes de loi applicables. "
    "Tu es direct, concis et pratique. "
    "Tu couvres : vente, achat, mandat, transaction, location nue et meublee, gestion locative, "
    "copropriete, urbanisme, permis de construire, fiscalite, diagnostics obligatoires, droit des baux."
)

THEMES_VEILLE = [
    "nouvelles lois decrets immobilier location France 2025",
    "reforme transaction immobiliere mandat agence 2025",
    "DPE diagnostic immobilier obligation nouveaute 2025",
    "fiscalite immobiliere plus-value IFI 2025",
    "jurisprudence droit bail locataire bailleur 2025",
    "urbanisme permis construire reglementation 2025"
]

def recherche_duckduckgo(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    params = {"q": query, "format": "json", "no_html": "1"}
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
                resultats.append("- " + r.get("Text", ""))
        if not resultats:
            resultats.append("Theme: " + query)
        return "\n".join(resultats)
    except Exception as e:
        return "Theme: " + query

def faire_veille():
    tous_resultats = []
    for theme in THEMES_VEILLE:
        resultats = recherche_duckduckgo(theme)
        tous_resultats.append("THEME: " + theme + "\n" + resultats)
    contenu = "\n\n".join(tous_resultats)
    prompt = (
        "Voici les resultats de recherche sur l actualite juridique immobiliere:\n\n"
        + contenu
        + "\n\nRedige une veille juridique mensuelle structuree pour AMO Invest, "
        "agence immobiliere a Graveson (13690). "
        "Ne mentionne que les vraies nouveautes. "
        "Structure par theme avec titres clairs. "
        "Impact concret pour l agence a chaque point. "
        "Date: " + datetime.now().strftime("%B %Y")
    )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    veille_text = message.content[0].text
    envoyer_email(veille_text)
    return veille_text

def envoyer_email(contenu):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = EMAIL_DESTINATAIRE
    msg["Subject"] = "Veille Juridique Immobiliere - " + datetime.now().strftime("%B %Y")
    msg.attach(MIMEText(contenu, "plain", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Erreur email: " + str(e))

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/question", methods=["POST"])
def repondre_question():
    data = request.get_json()
    question = data.get("question", "")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEME_JURIDIQUE,
        messages=[{"role": "user", "content": question}]
    )
    return jsonify({"reponse": message.content[0].text})

@app.route("/veille", methods=["POST"])
def lancer_veille():
    try:
        faire_veille()
        return jsonify({"message": "Veille terminee ! Email envoye avec succes."})
    except Exception as e:
        return jsonify({"message": "Erreur: " + str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
