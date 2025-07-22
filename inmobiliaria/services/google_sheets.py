"""
Funciones para acceso y manipulación de Google Sheets.
"""
import gspread
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from ..config import SCOPES, CLIENT_SECRET_FILE, TOKEN_PICKLE

def get_gspread_client():
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return gspread.authorize(creds)
