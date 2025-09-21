import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Permisos que necesitamos en YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube']

# Inicializa el servicio de YouTube
def get_service():
    creds = None
    # Si ya existe token guardado, lo usamos
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)

    # Si no existe o expiró, hacemos login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                raise FileNotFoundError("No se encontró 'client_secret.json'. Descárgalo de Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Guardamos el token
        with open('token.pickle', 'wb') as f:
            pickle.dump(creds, f)

    return build('youtube', 'v3', credentials=creds)

# Buscar el primer video que coincida con la canción
def search_video_id(youtube, query):
    res = youtube.search().list(
        q=query,
        part='id,snippet',
        type='video',
        maxResults=1
    ).execute()
    items = res.get('items', [])
    if not items:
        return None
    return items[0]['id']['videoId']

# Verificar si el video ya está en la playlist
def is_video_in_playlist(youtube, playlist_id, video_id):
    page_token = None
    while True:
        res = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()
        for item in res.get('items', []):
            rid = item['snippet']['resourceId']
            if rid.get('kind') == 'youtube#video' and rid.get('videoId') == video_id:
                return True
        page_token = res.get('nextPageToken')
        if not page_token:
            break
    return False

# Agregar el video a la playlist
def add_video_to_playlist(youtube, playlist_id, video_id):
    body = {
        'snippet': {
            'playlistId': playlist_id,
            'resourceId': {
                'kind': 'youtube#video',
                'videoId': video_id
            }
        }
    }
    youtube.playlistItems().insert(
        part='snippet',
        body=body
    ).execute()

# Función principal que usa el bot
def search_and_add(title, playlist_id):
    youtube = get_service()
    video_id = search_video_id(youtube, title)
    if not video_id:
        raise Exception(f"No se encontró video para: {title}")
    if is_video_in_playlist(youtube, playlist_id, video_id):
        return {'status': 'duplicate', 'video_id': video_id}
    add_video_to_playlist(youtube, playlist_id, video_id)
    return {'status': 'added', 'video_id': video_id}
