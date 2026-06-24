import anthropic
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
app = Flask(__name__)

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
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #1a365d; font-size: 28px; margin-bottom: 8px; }
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
        .user-msg {
            background: #1a365d;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .assistant-msg {
            background: #f7fafc;
            color: #2d3748;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid #e2e8f0;
        }
        .loading-msg {
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
        }
        textarea:focus { border-color: #1a365d; }
        .send-btn {
            background: #1a365d;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0 24px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
        }
        .send-btn:hover { background: #2a4a7f; }
        .send-btn:disabled { background: #a0aec0; cursor: not-allowed; }
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
        .footer {
            margin-top: 16px;
            color: #718096;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Juriste AMO Invest</h1>
        <p>Votre expert juridique immobilier disponible 24h/24</p>
    </div>
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message
