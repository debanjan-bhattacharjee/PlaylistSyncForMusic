import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
request = youtube.playlists().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": "Saved Weekly",
            "description": "For my weekly spotify recommendations"
          },
          "status": {
            "privacyStatus": "private"
          }
        }
    )

response = request.execute()

