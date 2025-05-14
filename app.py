import json
import requests
import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for

# Load config
with open('config.json') as f:
    config = json.load(f)

YOUTUBE_API_KEY = config['YOUTUBE_API_KEY']

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

HTML = '''
<!doctype html>
<title>YouTube Channel Info</title>
<h2>Enter YouTube Username or @handle</h2>
<form method="post">
  <input name="username" value="{{ username or '' }}" required>
  <input type="submit" value="Get Info">
  {% if info %}
    <button type="submit" name="refresh" value="1">Refresh</button>
  {% endif %}
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
{% if info %}
  <h3>All Channel Info</h3>
  <ul>
    <li><b>Channel Title:</b> {{ info['snippet']['title'] }}</li>
    <li><b>Description:</b> {{ info['snippet']['description'] }}</li>
    <li><b>Channel ID:</b> {{ info['id'] }}</li>
    <li><b>Custom URL:</b> {{ info['snippet'].get('customUrl', 'N/A') }}</li>
    <li><b>Published At:</b> {{ info['snippet']['publishedAt'] }}</li>
    <li><b>Country:</b> {{ info['snippet'].get('country', 'N/A') }}</li>
    <li><b>Subscribers:</b> {{ info['statistics'].get('subscriberCount', 'N/A') }}</li>
    <li><b>Views:</b> {{ info['statistics'].get('viewCount', 'N/A') }}</li>
    <li><b>Videos:</b> {{ info['statistics'].get('videoCount', 'N/A') }}</li>
    <li><b>Hidden Subscriber Count:</b> {{ info['statistics'].get('hiddenSubscriberCount', 'N/A') }}</li>
    <li><b>Channel Thumbnail:</b> <br>
      {% for key, thumb in info['snippet']['thumbnails'].items() %}
        <img src="{{ thumb['url'] }}" alt="{{ key }} thumbnail" style="margin:2px;max-width:120px;">
      {% endfor %}
    </li>
    <li><b>Branding Settings:</b>
      <pre>{{ info['brandingSettings'] | tojson(indent=2) }}</pre>
    </li>
    <li><b>Topic Details:</b>
      <pre>{{ info.get('topicDetails', {}) | tojson(indent=2) }}</pre>
    </li>
    <li><b>Content Details:</b>
      <pre>{{ info.get('contentDetails', {}) | tojson(indent=2) }}</pre>
    </li>
    <li><b>Status:</b>
      <pre>{{ info.get('status', {}) | tojson(indent=2) }}</pre>
    </li>
    <li><b>All Raw Data:</b>
      <pre>{{ info | tojson(indent=2) }}</pre>
    </li>
    <li><a href="https://www.youtube.com/channel/{{ info['id'] }}" target="_blank">Visit Channel</a></li>
  </ul>
  <h3>Playlists</h3>
  {% if playlists %}
    <ul>
    {% for pl in playlists %}
      <li>
        <b>{{ pl['snippet']['title'] }}</b> ({{ pl['id'] }})<br>
        <i>{{ pl['snippet']['description'] }}</i><br>
        <a href="https://www.youtube.com/playlist?list={{ pl['id'] }}" target="_blank">View Playlist</a>
      </li>
    {% endfor %}
    </ul>
  {% else %}
    <p>No playlists found.</p>
  {% endif %}
  <h3>Videos (from Uploads Playlist)</h3>
  {% if videos %}
    <ul>
    {% for vid in videos %}
      <li>
        <b>{{ vid['snippet']['title'] }}</b> ({{ vid['contentDetails']['videoId'] }})<br>
        <i>{{ vid['snippet']['description'] }}</i><br>
        <a href="https://www.youtube.com/watch?v={{ vid['contentDetails']['videoId'] }}" target="_blank">Watch Video</a><br>
        <pre>{{ vid | tojson(indent=2) }}</pre>
      </li>
    {% endfor %}
    </ul>
  {% else %}
    <p>No videos found or channel has no uploads.</p>
  {% endif %}
{% endif %}
'''


def get_data_file_path(username):
    # Use safe filename
    safe = username.replace('@', '_at_').replace('/', '_').replace('\\', '_')
    return os.path.join(DATA_DIR, f'{safe}.json')

def save_data(username, data):
    path = get_data_file_path(username)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data(username):
    path = get_data_file_path(username)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_channel_info_and_content(username):
    # Support both legacy usernames and @handles
    if username.startswith('@'):
        handle = username[1:]
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle}&key={YOUTUBE_API_KEY}"
        r = requests.get(search_url)
        data = r.json()
        if 'items' not in data or not data['items']:
            return None, [], [], None
        channel_id = data['items'][0]['snippet']['channelId'] if 'channelId' in data['items'][0]['snippet'] else data['items'][0]['id']['channelId']
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,brandingSettings,topicDetails,contentDetails,status&id={channel_id}&key={YOUTUBE_API_KEY}"
    else:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,brandingSettings,topicDetails,contentDetails,status&forUsername={username}&key={YOUTUBE_API_KEY}"
    r = requests.get(url)
    data = r.json()
    if 'items' not in data or not data['items']:
        return None, [], [], None
    item = data['items'][0]
    channel_id = item['id']

    # Get playlists
    playlists = []
    pl_url = f"https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&channelId={channel_id}&maxResults=50&key={YOUTUBE_API_KEY}"
    pl_resp = requests.get(pl_url)
    pl_data = pl_resp.json()
    if 'items' in pl_data:
        playlists = pl_data['items']

    # Get uploads playlist id
    uploads_playlist_id = None
    if 'contentDetails' in item and 'relatedPlaylists' in item['contentDetails']:
        uploads_playlist_id = item['contentDetails']['relatedPlaylists'].get('uploads')

    # Get videos from uploads playlist
    videos = []
    if uploads_playlist_id:
        nextPageToken = ''
        while True:
            vids_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={uploads_playlist_id}&maxResults=10&key={YOUTUBE_API_KEY}"
            if nextPageToken:
                vids_url += f"&pageToken={nextPageToken}"
            vids_resp = requests.get(vids_url)
            vids_data = vids_resp.json()
            if 'items' in vids_data:
                videos.extend(vids_data['items'])
            nextPageToken = vids_data.get('nextPageToken')
            if not nextPageToken or len(videos) >= 50:
                break

    version = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_to_save = {
        'version': version,
        'info': item,
        'playlists': playlists,
        'videos': videos
    }
    return item, playlists, videos, data_to_save



@app.route('/', methods=['GET', 'POST'])
def index():
    info = None
    playlists = []
    videos = []
    error = None
    version = None
    username = ''
    if request.method == 'POST':
        username = request.form['username']
        refresh = request.form.get('refresh')
        if not refresh:
            # Try to load from data folder
            cached = load_data(username)
            if cached:
                info = cached.get('info')
                playlists = cached.get('playlists', [])
                videos = cached.get('videos', [])
                version = cached.get('version')
            else:
                info, playlists, videos, data_to_save = get_channel_info_and_content(username)
                if info:
                    save_data(username, data_to_save)
                    version = data_to_save['version']
        else:
            # Force refresh from API
            info, playlists, videos, data_to_save = get_channel_info_and_content(username)
            if info:
                save_data(username, data_to_save)
                version = data_to_save['version']
        if not info:
            error = 'User not found or API error.'
    return render_template_string(HTML, info=info, playlists=playlists, videos=videos, error=error, version=version, username=username)

if __name__ == '__main__':
    app.run(debug=True)
