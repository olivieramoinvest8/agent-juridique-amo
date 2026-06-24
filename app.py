import anthropic
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, session, redirect
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE")
MOT_DE_PASSE = os.environ.get("MOT_DE_PASSE", "amoinvest2025")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
app = Flask(__name__)
app.secret_key = os.environ.get("MOT_DE_PASSE", "amoinvest2025") + "_secret"

LOGIN_PAGE = (
    "<!DOCTYPE html>"
    "<html lang='fr'>"
    "<head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
    "<title>AMO Invest - Connexion</title>"
    "<style>"
    "* { margin: 0; padding: 0; box-sizing: border-box; }"
    "body { font-family: Segoe UI, sans-serif; background: #f0f4f8; min-height: 100vh; display: flex; align-items: center; justify-content: center; }"
    ".box { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }"
    "h1 { color: #1a365d; font-size: 22px; margin-bottom: 8px; }"
    "p { color: #4a5568; font-size: 14px; margin-bottom: 24px; }"
    "input { width: 100%; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 14px; outline: none; margin-bottom: 16px; }"
    "input:focus { border-color: #1a365d; }"
    "button { width: 100%; background: #1a365d; color: white; border: none; border-radius: 10px; padding: 12px; font-size: 15px; font-weight: 600; cursor: pointer; }"
    "button:hover { background: #2a4a7f; }"
    ".erreur { color: #e53e3e; font-size: 13px; margin-bottom: 12px; }"
    "</style>"
    "</head>"
    "<body>"
    "<div class='box'>"
    "<h1>Juriste AMO Invest</h1>"
    "<p>Acces reserve a l equipe AMO Invest</p>"
    "{erreur}"
    "<input type='password' id='mdp' placeholder='Mot de passe' onkeydown='if(event.key==`Enter`)document.getElementById(`btn`).click()' />"
    "<button id='btn' onclick='login()'>Se connecter</button>"
    "</div>"
    "<script>"
    "function login() {"
    "var mdp = document.getElementById('mdp').value;"
    "fetch('/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mdp: mdp}) })"
    ".then(function(r) { return r.json(); })"
    ".then(function(d) { if (d.ok) { window.location.href = '/'; } else { window.location.reload(); } });"
    "}"
    "</script>"
    "</body>"
    "</html>"
)

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
    ".deconnexion { margin-top: 12px; background: none; border: none; color: #718096; font-size: 12px; cursor: pointer; text-decoration: underline; }"
    ".footer { margin-top: 8px; color: #718096; font-size: 12px; }"
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
    "<button class='deconnexion' onclick='deconnexion()'>Se deconnecter</button>"
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
    "function deconnexion() {"
    "fetch('/logout', { method: 'POST' }).then(function() { window.location.href = '/login'; });"
    "}"
    "</script>"
    "</body>"
    "</html>"
)

SYSTEME_JURIDIQUE = (
    "Tu es un expert juridique senior specialise en droit immobilier francais, "
    "droit de la transaction, droit de la location, droit de l urbanisme et fiscalite immobiliere. "
    "Tu travailles exclusivement pour AMO Invest, agence immobiliere a Graveson (13690). "
    "Tu reponds avec la precision d un avocat specialise. "
    "SOURCES QUE TU UTILISES EN PRIORITE : "
    "1. Legifrance (legifrance.gouv.fr) : loi Hoguet, loi ALUR, loi ELAN, loi du 6 juillet 1989, "
    "Code civil, Code de la construction et de l habitation, Code de l urbanisme. "
    "2. Service-public.fr : obligations pratiques des agences et proprietaires. "
    "3. Bofip (bofip.impots.gouv.fr) : fiscalite immobiliere, IFI, plus-values, dispositifs de defiscalisation. "
    "4. Jurisprudence : decisions de la Cour de cassation et des cours d appel. "
    "REGLES DE REPONSE : "
    "- Cite toujours le texte de loi exact avec son numero et son article. "
    "- Exemple : Loi n 89-462 du 6 juillet 1989, article 15. "
    "- Precise si une regle a ete modifiee recemment et depuis quand. "
    "- Si plusieurs interpretations existent, presente-les toutes. "
    "- Termine chaque reponse par : Point de vigilance pour AMO Invest si pertinent. "
    "- Si une question necessite absolument un avocat en cabinet, dis-le clairement. "
    "Tu couvres : vente, achat, mandat exclusif et simple, transaction, location nue et meublee, "
    "bail commercial, gestion locative, copropriete, urbanisme, permis de construire, "
    "declaration prealable, fiscalite, diagnostics obligatoires, droit des baux, contentieux locatif, "
    "expulsion, depot de garantie, charges locatives, etat des lieux, assurances."
)

def est_connecte():
    return session.get("connecte") == True

@app.route("/login", methods=["GET"])
def login_page():
    return LOGIN_PAGE.replace("{erreur}", "")

@app.route("/login", methods=["POST"])
def login_action():
    data = request.get_json()
    if data.get("mdp") == MOT_DE_PASSE:
        session["connecte"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/")
def index():
    if not est_connecte():
        return redirect("/login")
    return HTML_PAGE

@app.route("/question", methods=["POST"])
def repondre_question():
    if not est_connecte():
        return jsonify({"reponse": "Non autorise."})
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
    if not est_connecte():
        return jsonify({"message": "Non autorise."})
    return jsonify({"message": "Veille disponible prochainement."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
