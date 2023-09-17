from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import urllib.error


from flask import Flask, request, url_for, session, redirect
#Intialize Flask App

app = Flask(__name__)
#Session is used to store information about the user
#Session is a dictionary that stores key-value pairs
#Session is stored in a cookie on the browser
#Session is encrypted
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'kjsnfzkjnw*urh@*HIWEFR'
TOKEN_INFO = 'token_info'
# q: Should I store this secret key in a .env file?
# a: No, because the secret key is not a secret. It is used to encrypt the session cookie, not to authenticate with Spotify.
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
#function redirect
#Description: This function is called when the user logs in to Spotify
#It stores the token information in the session cookie
# code: The code is used to get the token information
# token_info: The token information is stored in the session cookie
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
     # redirect the user to the save_discover_weekly route
    return redirect(url_for('save_discover_weekly',_external=True))


@app.route('/toYoutube')
def save_in_playlist():
    credentials = None #going to pickle the credentials, so initially none 

    #token.pickle stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            credentials.refresh(Request())
        else:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                'newClientSecret.json',
                scopes=['https://www.googleapis.com/auth/youtube.force-ssl'])

            flow.run_local_server(port=8080, prompt='consent',
                                authorization_prompt_message='')
            credentials = flow.credentials

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)



    #function run_local_server() 
    # definition: 
    #     Runs the local server to handle OAuth 2.0 redirects.
    #     This function runs a local web server to handle redirects during OAuth
    #     authorization. This function is called by run_console() and is not
    #     intended to be called directly.
    #     The authorization prompt is served at ``http://localhost:port/``.
    #     Args:
    #         port: The port to run the server on.
    #         authorization_prompt_message: The message to display to the user when
    #             prompting them to authorize the app. This message should instruct
    #             the user to open a specific URL in their browser and paste the
    #             value that appears on the page into the application.
    #         success_message: The message to display to the user when the
    #             authorization flow is complete.
    #         open_browser: Whether or not to open a web browser automatically when
    #             prompting for authorization.
    #         open_authorization_prompt: Whether or not to open the authorization
    #             prompt in a web browser. If False, the authorization prompt is
    #             shown in the terminal. This argument is deprecated and will be
    #             removed in a future release.
    #         **kwargs: Additional arguments to pass to the underlying HTTP server.
    #     Returns:
    #         The authorization code returned by the server.
    #     Raises:
    #         FlowExchangeError: If the authorization flow fails to complete.
    #     """

    youtube = build('youtube', 'v3', credentials=credentials)
    song_data = session['song_data']
    playlistID="PLZN5r1XTFjELfColTzr2lLcs9rUwinHbJ"
    # currPlaylist = youtube.playlistItems().list(
    #     part="snippet",
    #     maxResults=250,
    #     playlistId=playlistID
    # ).execute()

    # playlistItems = currPlaylist['items']
    # # nextPageToken = currPlaylist.get('nextPageToken')

    # # while nextPageToken:
    # #     currPlaylist = youtube.playlistItems().list(
    # #         part="snippet",
    # #         maxResults=50,
    # #         playlistId=playlistID,
    # #         pageToken=nextPageToken
    # #     ).execute()
    # #     playlistItems += currPlaylist['items']
    # #     nextPageToken = currPlaylist.get('nextPageToken')


    # for item in playlistItems:
    #     youtube.playlistItems().delete(id=item['id']).execute()   

    #return ("Success! All deleted successfully")

    

    #return(currPlaylist)
    for song in song_data:
        query = song[0] + ' ' 
        for artist in song[1]:
            query += artist + ' '
        songSearch = youtube.search().list(
            part="snippet",
            maxResults=1,
            q=query 
        ).execute()
        
        kind= songSearch['items'][0]['id']['kind']
        videoID= songSearch['items'][0]['id']['videoId']
        backoff_time = 1  # In seconds
        try:
            addSong = youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlistID,
                            "position": 0,
                            "resourceId": {
                                "kind": kind,
                                "videoId": videoID
                                }
                        } 
                    }
                ).execute()
        except urllib.error.HttpError as e:
            if e.resp.status == 409 and 'SERVICE_UNAVAILABLE' in str(e):
                retry_count += 1
                print(f"Attempt {retry_count} failed. Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                raise
            raise Exception("Failed to add the song to the playlist after multiple retries.")
        
    return ("Success! All added successfully")

@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # get the user's playlists
    current_playlists =  sp.current_user_playlists()['items']
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None
    #print(current_playlists)
    # find the Discover Weekly and Saved Weekly playlists
    for playlist in current_playlists:
        if(playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']
        # if(playlist['name'] == 'Saved Daily Mix 1'):
        #     saved_weekly_playlist_id = playlist['id']
    
    # if the Discover Weekly playlist is not found, return an error message
    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found.'
    
    # get the tracks from the Discover Weekly playlist
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_data = []
    for song in discover_weekly_playlist['items']:
        song_name= song['track']['name']
        #song_names.append(song_name)
        this_song_artists= []
        for artist in song['track']['artists']:
            song_artist = artist['name']
            this_song_artists.append(song_artist)
        
        #song_artists.append(this_song_artists)
        song_data.append([song_name, this_song_artists])
    #return(song_data)
    # add the tracks to the Saved Weekly playlist
    #sp.user_playlist_add_tracks("YOUR_USER_ID", saved_weekly_playlist_id, song_uris, None)
    session['song_data'] = song_data
    # return a success message
    return redirect('toYoutube')

    



def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60    
    if (is_expired):
        token_info = create_spotify_oauth().refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(client_id=client_id, 
                        client_secret=client_secret, 
                        redirect_uri= url_for('redirect_page', _external = True), 
                        scope='user-library-read playlist-modify-public playlist-modify-private'
                        )
# redirect_page refers to the function redirect_page defined above
#q: What happens with url_for()?
#a: It generates the URL for the redirect_page function.
app.run(debug=True)
# q: What does debug=True do?
# a: It allows you to see the errors in the browser. It also restarts the server automatically when you make changes to the code.
# q: What is app.run()?
# a: It runs the Flask app.
# q: What does __name__ mean?
# a: It is a special variable that gets as value the string "__main__" when you’re executing the script.
# q: What does if __name__ == '__main__' mean?
# a: It means that the script is being run directly and not imported.
# q: What does app.run(debug=True) do?
# a: It starts the Flask server with the debugger.
