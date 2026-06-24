import anthropic
import requests
import smtplib
import schedule
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE")

# Client Anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

app = Flask(__name__)

# Interface HTML
HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Juriste AMO Invest</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #f0f4f8; 
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 { 
            color: #1a365d; 
            font-size: 28px;
            margin-bottom: 8px;
        }
        .header p { color: #4a5568; font-size: 15px; }
        .chat-container {
            width: 100%;
            max-width: 800px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .messages {
            height: 500px;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.6;
        }
        .message.user {
            background: #1a365d;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .message.assistant {
            background: #f7fafc;
            color: #2d3748;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid #e2e8f0;
        }
        .message.loading {
            background: #f7fafc;
            color: #718096;
            align-self: flex-start;
            border: 1px solid #e2e8f0;
            font-style: italic;
        }
        .input-zone {
            padding: 20px;
            border-top: 1px solid #e2e8f0;
            display: flex;
            gap: 12px;
        }
        textarea {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 14px;
            resize: none;
            height: 60px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }
        textarea:focus { border-color: #1a365d; }
        button {
            background: #1a365d;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0 24px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover { background: #2a4a7f; }
        button:disabled { background: #a0aec0; cursor: not-allowed; }
        .footer {
            margin-top: 16px;
            color: #718096;
            font-size: 12px;
            text-align: center;
        }
        .veille-btn {
            margin-top: 16px;
            background: #276749;
            padding: 10px 20px;
            border-radius: 8px;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 13px;
        }
        .veille-btn:hover { background: #2f855a; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚖️ Juriste AMO Invest</h1>
        <p>Votre expert juridique immobilier disponible 24h/24</p>
    </div>
    
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message assistant">
                Bonjour, je suis votre juriste spécialisé en droit immobilier, transaction, location et urbanisme. Posez-moi votre question.
            </div>
        </div>
        <div class="input-zone">
            <textarea id="question" placeholder="Ex: Un mandat exclusif peut-il être résilié avant terme ?" onkeydown="handleKey(event)"></textarea>
            <button onclick="poserQuestion()" id="btn">Envoyer</button>
        </div>
    </div>

    <button class="veille-btn" onclick="lancerVeille()">🔍 Lancer la veille juridique maintenant</button>
    
    <div class="footer">AMO Invest — Graveson (13) — Usage interne uniquement</div>

    <script>
        function handleKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                poserQuestion();
            }
        }

        async function poserQuestion() {
            const question = document.getElementById('question').value.trim();
            if (!question) return;
            
            const messages = document.getElementById('messages');
            const btn = document.getElementById('btn');
            
            // Afficher la question
            messages.innerHTML += `<div class="message user">${question}</div>`;
            messages.innerHTML += `<div class="message loading" id="loading">⏳ Analyse en cours...</div>`;
            document.getElementById('question').value = '';
            btn.disabled = true;
            messages.scrollTop = messages.scrollHeight;
            
            try {
                const response = await fetch('/question', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                const data = await response.json();
                document.getElementById('loading').remove();
                messages.innerHTML += `<div class="message assistant">${data.reponse.replace(/\\n/g, '<br>')}</div>`;
            } catch(e) {
                document.getElementById('loading').remove();
                messages.innerHTML += `<div class="message assistant">Erreur de connexion. Réessayez.</div>`;
            }
            
            btn.disabled = false;
            messages.scrollTop = messages.scrollHeight;
        }

        async function lancerVeille() {
            if (!confirm('Lancer la veille juridique maintenant ? Un email vous sera envoyé.')) return;
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ Veille en cours...';
            try {
                const response = await fetch('/veille', {method: 'POST'});
                const data = await response.json();
                alert(data.message);
            } catch(e) {
                alert('Erreur lors de la veille.');
            }
            btn.disabled = false;
            btn.textContent = '🔍 Lancer la veille juridique maintenant';
        }
    </script>
</body>
</html>
"""

SYSTEME_JURIDIQUE = """Tu es un expert juridique senior spécialisé en droit immobilier français, 
droit de la transaction, droit de la location, droit de l'urbanisme et fiscalité immobilière. 
Tu travailles exclusivement pour AMO Invest, agence immobilière à Graveson (13690).
Tu réponds avec la précision d'un avocat spécialisé, en citant les textes de loi applicables 
(articles de loi, décrets, jurisprudences) quand c'est pertinent.
Tu es direct, concis et pratique — tu donnes des réponses actionnables pour un professionnel de l'immobilier.
Tu couvres : vente, achat, mandat, transaction, location nue et meublée, gestion locative, 
copropriété, urbanisme, permis de construire, fiscalité (IFI, plus-values, défiscalisation), 
diagnostics obligatoires, droit des baux, contentieux locatif.
Si une question dépasse tes compétences ou nécessite absolument un avocat en cabinet, dis-le clairement."""

THEMES_VEILLE = [
    "nouvelles lois décrets immobilier location France 2025",
    "réforme transaction immobilière mandat agence 2025",
    "DPE diagnostic immobilier obligation nouveauté 2025",
    "fiscalité immobilière plus-value IFI défiscalisation 2025",
    "jurisprudence droit bail locataire bailleur 2025",
    "urbanisme permis construire réglementation 2025",
    "copropriété syndic réforme loi 2025"
]

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

def faire_veille():
    """Effectue la veille juridique mensuelle"""
    print(f"[{datetime.now()}] Démarrage de la veille juridique...")
    
    tous_resultats = []
    for theme in THEMES_VEILLE:
        print(f"Recherche: {theme}")
        resultats = recherche_brave(theme)
        tous_resultats.append(f"THÈME: {theme}\n{resultats}")
        time.sleep(1)
    
    contenu_recherches = "\n\n".join(tous_resultats)
    
    prompt = f"""Voici les résultats de recherche sur l'actualité juridique immobilière française du mois :

{contenu_recherches}

En tant qu'expert juridique immobilier, rédige une veille juridique mensuelle structurée pour AMO Invest, agence immobilière à Graveson (13690).

INSTRUCTIONS :
- Ne mentionne QUE les vraies nouveautés (nouvelles lois, décrets, jurisprudences récentes)
- Ignore tout ce qui n'est pas une nouveauté réelle
- Structure par thème avec des titres clairs
- Pour chaque nouveauté : ce qui change concrètement pour l'agence
- Termine par un résumé "Points d'attention ce mois-ci"
- Ton : professionnel, direct, pratique

Date : {datetime.now().strftime('%B %Y')}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    veille_text = message.content[0].text
    envoyer_email(veille_text)
    print(f"[{datetime.now()}] Veille terminée et email envoyé.")
    return veille_text

def envoyer_email(contenu):
    """Envoie le résumé par email via Gmail"""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = EMAIL_DESTINATAIRE
    msg['Subject'] = f"⚖️ Veille Juridique Immobilière — {datetime.now().strftime('%B %Y')}"
    msg.attach(MIMEText(contenu, 'plain', 'utf-8'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.send_message(msg)
        print("Email envoyé avec succès.")
    except Exception as e:
        print(f"Erreur email: {str(e)}")

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/question', methods=['POST'])
def repondre_question():
    data = request.get_json()
    question = data.get('question', '')
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEME_JURIDIQUE,
        messages=[{"role": "user", "content": question}]
    )
    
    return jsonify({"reponse": message.content[0].text})

@app.route('/veille', methods=['POST'])
def lancer_veille():
    try:
        faire_veille()
        return jsonify({"message": "✅ Veille terminée ! Email envoyé avec succès."})
    except Exception as e:
        return jsonify({"message": f"❌ Erreur: {str(e)}"})

def planificateur():
    """Lance la veille automatiquement le 1er de chaque mois"""
    schedule.every().month.do(faire_veille)
    while True:
        schedule.run_pending()
        time.sleep(3600)

if __name__ == '__main__':
    import threading
    t = threading.Thread(target=planificateur, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
