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
<title>YouTube Channel Info & Comparison</title>
<style>
  body { font-family: Arial, sans-serif; background: #f9f9f9; margin: 0; padding: 0; }
  .container { max-width: 900px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px #ddd; padding: 32px 36px 36px 36px; position: relative; }
  .compare-box { position: absolute; top: 32px; right: 36px; background: #f7f7f7; padding: 12px 16px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; }
  .compare-table { border-collapse: collapse; width: 100%; margin-top: 24px; }
  .compare-table th, .compare-table td { border: 1px solid #ccc; padding: 8px 12px; text-align: center; }
  .winner { background: #d4ffd4; font-weight: bold; }
  .loser { background: #ffd4d4; }
  .draw { background: #f7f7f7; }
  .channel-section { display: flex; gap: 32px; margin-top: 24px; }
  .channel-card { flex: 1; background: #f7f7f7; border-radius: 8px; padding: 18px 20px; box-shadow: 0 1px 4px #eee; }
  .channel-title { font-size: 1.3em; font-weight: bold; margin-bottom: 8px; }
  .channel-thumb { margin-bottom: 10px; }
  .stat-label { font-weight: bold; }
  .error { color: red; }
</style>
<div class="container">
  <h2>YouTube Channel Info & Comparison</h2>
  <form method="post" style="margin-bottom: 18px;">
    <input name="username" value="{{ username or '' }}" required placeholder="Enter YouTube Username or @handle">
    <input type="submit" value="Get Info">
    {% if info %}
      <button type="submit" name="refresh" value="1">Refresh</button>
    {% endif %}
  </form>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}

  {% if info and not compare_info %}
    <div class="channel-section">
      <div class="channel-card">
        <div class="channel-title">{{ info['snippet']['title'] }}</div>
        <div class="channel-thumb">
          {% for key, thumb in info['snippet']['thumbnails'].items() %}
            <img src="{{ thumb['url'] }}" alt="{{ key }} thumbnail" style="margin:2px;max-width:120px;">
          {% endfor %}
        </div>
        <div><span class="stat-label">Description:</span> {{ info['snippet']['description'] }}</div>
        <div><span class="stat-label">Channel ID:</span> {{ info['id'] }}</div>
        <div><span class="stat-label">Custom URL:</span> {{ info['snippet'].get('customUrl', 'N/A') }}</div>
        <div><span class="stat-label">Published At:</span> {{ info['snippet']['publishedAt'] }}</div>
        <div><span class="stat-label">Country:</span> {{ info['snippet'].get('country', 'N/A') }}</div>
        <div><span class="stat-label">Subscribers:</span> {{ info['statistics'].get('subscriberCount', 'N/A') }}</div>
        <div><span class="stat-label">Views:</span> {{ info['statistics'].get('viewCount', 'N/A') }}</div>
        <div><span class="stat-label">Videos:</span> {{ info['statistics'].get('videoCount', 'N/A') }}</div>
        <div><span class="stat-label">Hidden Subscriber Count:</span> {{ info['statistics'].get('hiddenSubscriberCount', 'N/A') }}</div>
        <div><a href="https://www.youtube.com/channel/{{ info['id'] }}" target="_blank">Visit Channel</a></div>
        {% if info %}
        <form method="post" style="margin-top:18px;">
          <input type="hidden" name="username" value="{{ username }}">
          <input name="compare_username" placeholder="Compare with..." value="">
          <button type="submit" name="compare" value="1">Compare</button>
        </form>
        {% endif %}
      </div>
    </div>
  {% elif compare_info and info %}
    <h3>Comparison: {{ info['snippet']['title'] }} vs {{ compare_info['snippet']['title'] }}</h3>
    <table class="compare-table">
      <tr>
        <th>Stat</th>
        <th>{{ info['snippet']['title'] }}</th>
        <th>{{ compare_info['snippet']['title'] }}</th>
        <th>Winner</th>
      </tr>
      {% set stats = [
        ('Subscribers', 'subscriberCount'),
        ('Views', 'viewCount'),
        ('Videos', 'videoCount'),
        ('Published At', 'publishedAt')
      ] %}
      {% set score1 = namespace(val=0) %}
      {% set score2 = namespace(val=0) %}
      {% for label, key in stats %}
        {% set v1 = info['statistics'].get(key, info['snippet'].get(key, 'N/A')) %}
        {% set v2 = compare_info['statistics'].get(key, compare_info['snippet'].get(key, 'N/A')) %}
        {% set winner = None %}
        {% if key in ['subscriberCount', 'viewCount', 'videoCount'] %}
          {% if v1 != 'N/A' and v2 != 'N/A' %}
            {% if v1|int > v2|int %}{% set winner = 1 %}{% set score1.val = score1.val + 1 %}
            {% elif v1|int < v2|int %}{% set winner = 2 %}{% set score2.val = score2.val + 1 %}
            {% else %}{% set winner = 0 %}{% endif %}
          {% endif %}
        {% elif key == 'publishedAt' %}
          {% if v1 != 'N/A' and v2 != 'N/A' %}
            {% if v1 < v2 %}{% set winner = 2 %}{% set score2.val = score2.val + 1 %}
            {% elif v1 > v2 %}{% set winner = 1 %}{% set score1.val = score1.val + 1 %}
            {% else %}{% set winner = 0 %}{% endif %}
          {% endif %}
        {% endif %}
        <tr>
          <td>{{ label }}</td>
          <td class="{% if winner == 1 %}winner{% elif winner == 2 %}loser{% elif winner == 0 %}draw{% endif %}">{{ v1 }}</td>
          <td class="{% if winner == 2 %}winner{% elif winner == 1 %}loser{% elif winner == 0 %}draw{% endif %}">{{ v2 }}</td>
          <td>
            {% if winner == 1 %}{{ info['snippet']['title'] }}
            {% elif winner == 2 %}{{ compare_info['snippet']['title'] }}
            {% elif winner == 0 %}Draw{% else %}-{% endif %}
          </td>
        </tr>
      {% endfor %}
      <tr>
        <th>Score</th>
        <th>{{ score1.val }}</th>
        <th>{{ score2.val }}</th>
        <th>
          {% if score1.val > score2.val %}Winner: {{ info['snippet']['title'] }}
          {% elif score2.val > score1.val %}Winner: {{ compare_info['snippet']['title'] }}
          {% else %}Draw{% endif %}
        </th>
      </tr>
    </table>
    <div class="channel-section">
      <div class="channel-card">
        <div class="channel-title">{{ info['snippet']['title'] }}</div>
        <div class="channel-thumb">
          {% for key, thumb in info['snippet']['thumbnails'].items() %}
            <img src="{{ thumb['url'] }}" alt="{{ key }} thumbnail" style="margin:2px;max-width:120px;">
          {% endfor %}
        </div>
        <div><span class="stat-label">Description:</span> {{ info['snippet']['description'] }}</div>
        <div><span class="stat-label">Channel ID:</span> {{ info['id'] }}</div>
        <div><span class="stat-label">Custom URL:</span> {{ info['snippet'].get('customUrl', 'N/A') }}</div>
        <div><span class="stat-label">Country:</span> {{ info['snippet'].get('country', 'N/A') }}</div>
        <div><span class="stat-label">Hidden Subscriber Count:</span> {{ info['statistics'].get('hiddenSubscriberCount', 'N/A') }}</div>
        <div><a href="https://www.youtube.com/channel/{{ info['id'] }}" target="_blank">Visit Channel</a></div>
      </div>
      <div class="channel-card">
        <div class="channel-title">{{ compare_info['snippet']['title'] }}</div>
        <div class="channel-thumb">
          {% for key, thumb in compare_info['snippet']['thumbnails'].items() %}
            <img src="{{ thumb['url'] }}" alt="{{ key }} thumbnail" style="margin:2px;max-width:120px;">
          {% endfor %}
        </div>
        <div><span class="stat-label">Description:</span> {{ compare_info['snippet']['description'] }}</div>
        <div><span class="stat-label">Channel ID:</span> {{ compare_info['id'] }}</div>
        <div><span class="stat-label">Custom URL:</span> {{ compare_info['snippet'].get('customUrl', 'N/A') }}</div>
        <div><span class="stat-label">Country:</span> {{ compare_info['snippet'].get('country', 'N/A') }}</div>
        <div><span class="stat-label">Hidden Subscriber Count:</span> {{ compare_info['statistics'].get('hiddenSubscriberCount', 'N/A') }}</div>
        <div><a href="https://www.youtube.com/channel/{{ compare_info['id'] }}" target="_blank">Visit Channel</a></div>
      </div>
    </div>
  {% endif %}
</div>
<!doctype html>
<title>YouTube Channel Info & Comparison</title>
<style>
  .compare-box { position: absolute; top: 20px; right: 20px; background: #f7f7f7; padding: 12px 16px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; }
  .compare-table { border-collapse: collapse; width: 100%; margin-top: 24px; }
  .compare-table th, .compare-table td { border: 1px solid #ccc; padding: 8px 12px; text-align: center; }
  .winner { background: #d4ffd4; font-weight: bold; }
  .loser { background: #ffd4d4; }
  .draw { background: #f7f7f7; }
</style>
<div class="compare-box">
  <form method="post" style="display:inline;">
    <input name="compare_username" placeholder="Compare with..." value="{{ compare_username or '' }}">
    <input type="hidden" name="username" value="{{ username or '' }}">
    <button type="submit" name="compare" value="1">Compare</button>
  </form>
</div>
<h2>Enter YouTube Username or @handle</h2>
<form method="post">
  <input name="username" value="{{ username or '' }}" required>
  <input type="submit" value="Get Info">
  {% if info %}
    <button type="submit" name="refresh" value="1">Refresh</button>
  {% endif %}
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}

{% if compare_info and info %}
  <h2>Comparison: {{ info['snippet']['title'] }} vs {{ compare_info['snippet']['title'] }}</h2>
  <table class="compare-table">
    <tr>
      <th>Stat</th>
      <th>{{ info['snippet']['title'] }}</th>
      <th>{{ compare_info['snippet']['title'] }}</th>
      <th>Winner</th>
    </tr>
    {% set stats = [
      ('Subscribers', 'subscriberCount'),
      ('Views', 'viewCount'),
      ('Videos', 'videoCount'),
      ('Published At', 'publishedAt')
    ] %}
    {% set score1 = 0 %}
    {% set score2 = 0 %}
    {% for label, key in stats %}
      {% set v1 = info['statistics'].get(key, info['snippet'].get(key, 'N/A')) %}
      {% set v2 = compare_info['statistics'].get(key, compare_info['snippet'].get(key, 'N/A')) %}
      {% set winner = None %}
      {% if key in ['subscriberCount', 'viewCount', 'videoCount'] %}
        {% if v1 != 'N/A' and v2 != 'N/A' %}
          {% if v1|int > v2|int %}{% set winner = 1 %}{% set score1 = score1 + 1 %}
          {% elif v1|int < v2|int %}{% set winner = 2 %}{% set score2 = score2 + 1 %}
          {% else %}{% set winner = 0 %}{% endif %}
        {% endif %}
      {% elif key == 'publishedAt' %}
        {% if v1 != 'N/A' and v2 != 'N/A' %}
          {% if v1 < v2 %}{% set winner = 1 %}{% set score1 = score1 + 1 %}
          {% elif v1 > v2 %}{% set winner = 2 %}{% set score2 = score2 + 1 %}
          {% else %}{% set winner = 0 %}{% endif %}
        {% endif %}
      {% endif %}
      <tr>
        <td>{{ label }}</td>
        <td class="{% if winner == 1 %}winner{% elif winner == 2 %}loser{% elif winner == 0 %}draw{% endif %}">{{ v1 }}</td>
        <td class="{% if winner == 2 %}winner{% elif winner == 1 %}loser{% elif winner == 0 %}draw{% endif %}">{{ v2 }}</td>
        <td>
          {% if winner == 1 %}{{ info['snippet']['title'] }}
          {% elif winner == 2 %}{{ compare_info['snippet']['title'] }}
          {% elif winner == 0 %}Draw{% else %}-{% endif %}
        </td>
      </tr>
    {% endfor %}
    <tr>
      <th>Score</th>
      <th>{{ score1 }}</th>
      <th>{{ score2 }}</th>
      <th>
        {% if score1 > score2 %}Winner: {{ info['snippet']['title'] }}
        {% elif score2 > score1 %}Winner: {{ compare_info['snippet']['title'] }}
        {% else %}Draw{% endif %}
      </th>
    </tr>
  </table>
{% endif %}

{% if info and not compare_info %}
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
    compare_username = ''
    compare_info = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        compare_username = request.form.get('compare_username', '').strip()
        refresh = request.form.get('refresh')
        compare = request.form.get('compare')

        # Always load main user info
        if not refresh and not compare:
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
            info, playlists, videos, data_to_save = get_channel_info_and_content(username)
            if info:
                save_data(username, data_to_save)
                version = data_to_save['version']

        # If compare requested and both usernames present, load comparison info
        if compare and username and compare_username:
            # Load or fetch compare user info
            compare_cached = load_data(compare_username)
            if compare_cached:
                compare_info = compare_cached.get('info')
            else:
                compare_info, _, _, compare_data_to_save = get_channel_info_and_content(compare_username)
                if compare_info:
                    save_data(compare_username, compare_data_to_save)
        if not info:
            error = 'User not found or API error.'
        elif compare and not compare_info:
            error = f'Compare user "{compare_username}" not found or API error.'
    return render_template_string(
        HTML,
        info=info,
        playlists=playlists,
        videos=videos,
        error=error,
        version=version,
        username=username,
        compare_username=compare_username,
        compare_info=compare_info
    )

if __name__ == '__main__':
    app.run(debug=True)
