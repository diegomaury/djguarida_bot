from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define los scopes que necesitas
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # Ejemplo para Google Sheets

def get_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('sheets', 'v4', credentials=creds)
    return service

if __name__ == "__main__":
    service = get_service()
    print("Autenticación exitosa ✅")
