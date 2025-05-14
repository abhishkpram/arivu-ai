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
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fa; margin: 0; padding: 0; }
  .header-bar {
    width: 100vw;
    background: #222e3c;
    color: #fff;
    padding: 0 0 0 0;
    margin: 0;
    box-shadow: 0 2px 8px #d0d6e1;
    display: flex;
    align-items: center;
    height: 56px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .header-bar .nav-btn {
    background: none;
    border: none;
    color: #fff;
    font-size: 1.1em;
    margin: 0 18px;
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .header-bar .nav-btn.active, .header-bar .nav-btn:hover {
    background: #3a4a5e;
  }
  .header-bar .back-btn {
    margin-left: 12px;
    background: #e0e6ef;
    color: #222e3c;
    font-weight: 500;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .header-bar .back-btn:hover {
    background: #cfd8e6;
  }
  .container {
    max-width: 1000px;
    margin: 40px auto;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 16px #d0d6e1;
    padding: 36px 40px 40px 40px;
    position: relative;
    overflow-x: auto;
  }
  .compare-table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 24px;
    table-layout: fixed;
    word-break: break-word;
    background: #f8fafc;
    border-radius: 8px;
    overflow: hidden;
  }
  .compare-table td, .compare-table th {
    max-width: 220px;
    overflow-wrap: break-word;
    padding: 10px 12px;
    border: 1px solid #e0e6ef;
  }
  @media (max-width: 1100px) {
    .container { padding: 12px 2vw; }
    .compare-table td, .compare-table th { font-size: 0.98em; }
  }
  .compare-table th { background: #e0e6ef; color: #222e3c; font-weight: 600; }
  .winner { background: #d4ffd4; font-weight: bold; }
  .loser { background: #ffd4d4; }
  .draw { background: #f7f7f7; }
  .channel-section { display: flex; gap: 32px; margin-top: 24px; }
  .channel-card {
    flex: 1;
    background: #f7f7f7;
    border-radius: 10px;
    padding: 20px 22px;
    box-shadow: 0 1px 6px #e0e6ef;
    min-width: 0;
  }
  .channel-title { font-size: 1.3em; font-weight: bold; margin-bottom: 8px; color: #1a2330; }
  .channel-thumb { margin-bottom: 10px; }
  .stat-label { font-weight: 500; color: #3a4a5e; }
  .error { color: #d32f2f; font-weight: 500; }
  .comments-summary-box {
    background: #f0f4fa;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 18px;
    color: #2a3a4c;
    font-size: 1.05em;
    box-shadow: 0 1px 4px #e0e6ef;
    display: flex;
    align-items: center;
    gap: 10px;
  }
</style>
<div class="header-bar">
  <button class="back-btn" onclick="window.history.back()">&#8592; Back</button>
  <button class="nav-btn {% if page == 'getinfo' %}active{% endif %}" onclick="window.location.href='/'">Get Info</button>
  <button class="nav-btn {% if page == 'compare' %}active{% endif %}" onclick="window.location.href='/compare'">Compare</button>
</div>
<div class="container">
  {% if page == 'getinfo' %}
    {% if not info and not compare_info %}
    <form method="post" style="margin-bottom: 18px;">
      <input name="username" value="{{ username or '' }}" required placeholder="Enter YouTube Username or @handle">
      <input type="submit" value="Get Info">
    </form>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
  {% endif %}

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
        {% if sub_history and sub_history|length > 1 %}
        <div style="margin: 18px 0;">
          <canvas id="subHistoryChart" width="400" height="180"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        const ctx = document.getElementById('subHistoryChart').getContext('2d');
        const chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: {{ sub_history|map(attribute='date')|list|tojson }},
            datasets: [{
              label: 'Subscriber Count',
              data: {{ sub_history|map(attribute='count')|list|tojson }},
              borderColor: 'rgba(75, 192, 192, 1)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              fill: true,
              tension: 0.2
            }]
          },
          options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { x: { title: { display: true, text: 'Date' } }, y: { title: { display: true, text: 'Subscribers' } } }
          }
        });
        </script>
        {% endif %}
        <div><span class="stat-label">Views:</span> {{ info['statistics'].get('viewCount', 'N/A') }}</div>
        <div><span class="stat-label">Videos:</span> {{ info['statistics'].get('videoCount', 'N/A') }}</div>
        <div><span class="stat-label">Hidden Subscriber Count:</span> {{ info['statistics'].get('hiddenSubscriberCount', 'N/A') }}</div>
        <div><span class="stat-label">Privacy Status:</span> {{ info['status'].get('privacyStatus', 'N/A') if info.get('status') else 'N/A' }}</div>
        <div><span class="stat-label">Is Linked:</span> {{ info['status'].get('isLinked', 'N/A') if info.get('status') else 'N/A' }}</div>
        <div><span class="stat-label">Long Uploads Status:</span> {{ info['status'].get('longUploadsStatus', 'N/A') if info.get('status') else 'N/A' }}</div>
        <div><span class="stat-label">Made For Kids:</span> {{ info['status'].get('madeForKids', 'N/A') if info.get('status') else 'N/A' }}</div>
        <div><span class="stat-label">Topic Categories:</span> {{ info['topicDetails'].get('topicCategories', [])|join(', ') if info.get('topicDetails') else 'N/A' }}</div>
        <div><span class="stat-label">Topic Ids:</span> {{ info['topicDetails'].get('topicIds', [])|join(', ') if info.get('topicDetails') else 'N/A' }}</div>
        <div><span class="stat-label">Unsubscribed Trailer:</span> {{ info['brandingSettings']['channel'].get('unsubscribedTrailer', 'N/A') if info.get('brandingSettings') and info['brandingSettings'].get('channel') else 'N/A' }}</div>
        <div><span class="stat-label">Banner Image:</span> <a href="{{ info['brandingSettings']['image'].get('bannerExternalUrl', '') if info.get('brandingSettings') and info['brandingSettings'].get('image') else '#' }}" target="_blank">View</a></div>
        <div><span class="stat-label">Uploads Playlist:</span> {{ info['contentDetails']['relatedPlaylists'].get('uploads', 'N/A') if info.get('contentDetails') and info['contentDetails'].get('relatedPlaylists') else 'N/A' }}</div>
        <div><span class="stat-label">Likes Playlist:</span> {{ info['contentDetails']['relatedPlaylists'].get('likes', 'N/A') if info.get('contentDetails') and info['contentDetails'].get('relatedPlaylists') else 'N/A' }}</div>
        <div><a href="https://www.youtube.com/channel/{{ info['id'] }}" target="_blank">Visit Channel</a></div>
        {% if comments_summary %}
        <div class="comments-summary-box">
          <span class="stat-label">Comments Summary:</span> <span>{{ comments_summary }}</span>
        </div>
        {% endif %}
        <form method="post" style="margin-top:18px;">
          <input type="hidden" name="username" value="{{ username }}">
          <input name="compare_username" placeholder="Compare with..." value="">
          <button type="submit" name="compare" value="1">Compare</button>
        </form>
        <form method="post" style="margin-top:8px;">
          <input type="hidden" name="username" value="{{ username }}">
          <button type="submit" name="refresh" value="1">Refresh</button>
        </form>
      </div>
    </div>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    {% endif %}
  {% elif page == 'compare' %}
    {% if info and compare_info %}
    <h3 style="color:#1a2330;">Comparison: {{ info['snippet']['title'] }} vs {{ compare_info['snippet']['title'] }}</h3>
    <table class="compare-table">
      <tr>
        <th>Stat</th>
        <th>{{ info['snippet']['title'] }}</th>
        <th>{{ compare_info['snippet']['title'] }}</th>
        <th>Winner</th>
      </tr>
      {% set stats = [
        ('Title', 'title', 'snippet'),
        ('Description', 'description', 'snippet'),
        ('Custom URL', 'customUrl', 'snippet'),
        ('Published At', 'publishedAt', 'snippet'),
        ('Country', 'country', 'snippet'),
        ('Subscribers', 'subscriberCount', 'statistics'),
        ('Views', 'viewCount', 'statistics'),
        ('Videos', 'videoCount', 'statistics'),
        ('Hidden Subscriber Count', 'hiddenSubscriberCount', 'statistics'),
        ('Privacy Status', 'privacyStatus', 'status'),
        ('Is Linked', 'isLinked', 'status'),
        ('Long Uploads Status', 'longUploadsStatus', 'status'),
        ('Made For Kids', 'madeForKids', 'status'),
        ('Topic Categories', 'topicCategories', 'topicDetails'),
        ('Topic Ids', 'topicIds', 'topicDetails'),
        ('Unsubscribed Trailer', 'unsubscribedTrailer', 'brandingSettings.channel'),
        ('Banner Image', 'bannerExternalUrl', 'brandingSettings.image'),
        ('Uploads Playlist', 'uploads', 'contentDetails.relatedPlaylists'),
        ('Likes Playlist', 'likes', 'contentDetails.relatedPlaylists')
      ] %}
      {% set score1 = namespace(val=0) %}
      {% set score2 = namespace(val=0) %}
      {% for label, key, section in stats %}
        {% set v1 = 'N/A' %}
        {% set v2 = 'N/A' %}
        {% if section == 'snippet' %}
          {% set v1 = info['snippet'].get(key, 'N/A') %}
          {% set v2 = compare_info['snippet'].get(key, 'N/A') %}
        {% elif section == 'statistics' %}
          {% set v1 = info['statistics'].get(key, 'N/A') %}
          {% set v2 = compare_info['statistics'].get(key, 'N/A') %}
        {% elif section == 'status' %}
          {% set v1 = info['status'].get(key, 'N/A') %}
          {% set v2 = compare_info['status'].get(key, 'N/A') %}
        {% elif section == 'topicDetails' %}
          {% set v1 = info['topicDetails'].get(key, []) %}
          {% set v2 = compare_info['topicDetails'].get(key, []) %}
          {% if v1 is iterable and v1 is not string %}{% set v1 = v1|join(', ') %}{% endif %}
          {% if v2 is iterable and v2 is not string %}{% set v2 = v2|join(', ') %}{% endif %}
        {% elif section == 'brandingSettings.channel' %}
          {% set v1 = info['brandingSettings']['channel'].get(key, 'N/A') if info.get('brandingSettings') and info['brandingSettings'].get('channel') else 'N/A' %}
          {% set v2 = compare_info['brandingSettings']['channel'].get(key, 'N/A') if compare_info.get('brandingSettings') and compare_info['brandingSettings'].get('channel') else 'N/A' %}
        {% elif section == 'brandingSettings.image' %}
          {% set v1 = info['brandingSettings']['image'].get(key, 'N/A') if info.get('brandingSettings') and info['brandingSettings'].get('image') else 'N/A' %}
          {% set v2 = compare_info['brandingSettings']['image'].get(key, 'N/A') if compare_info.get('brandingSettings') and compare_info['brandingSettings'].get('image') else 'N/A' %}
        {% elif section == 'contentDetails.relatedPlaylists' %}
          {% set v1 = info['contentDetails']['relatedPlaylists'].get(key, 'N/A') if info.get('contentDetails') and info['contentDetails'].get('relatedPlaylists') else 'N/A' %}
          {% set v2 = compare_info['contentDetails']['relatedPlaylists'].get(key, 'N/A') if compare_info.get('contentDetails') and compare_info['contentDetails'].get('relatedPlaylists') else 'N/A' %}
        {% endif %}
        {% set winner = None %}
        {# Numeric comparison for certain fields #}
        {% if key in ['subscriberCount', 'viewCount', 'videoCount'] %}
          {% if v1 != 'N/A' and v2 != 'N/A' %}
            {% if v1|int > v2|int %}{% set winner = 1 %}{% set score1.val = score1.val + 1 %}
            {% elif v1|int < v2|int %}{% set winner = 2 %}{% set score2.val = score2.val + 1 %}
            {% else %}{% set winner = 0 %}{% endif %}
          {% endif %}
        {% elif key == 'publishedAt' %}
          {% if v1 != 'N/A' and v2 != 'N/A' %}
            {% if v1 < v2 %}{% set winner = 1 %}{% set score1.val = score1.val + 1 %}
            {% elif v1 > v2 %}{% set winner = 2 %}{% set score2.val = score2.val + 1 %}
            {% else %}{% set winner = 0 %}{% endif %}
          {% endif %}
        {% elif key in ['isLinked', 'madeForKids', 'hiddenSubscriberCount'] %}
          {% if v1 != 'N/A' and v2 != 'N/A' %}
            {% if v1 == v2 %}{% set winner = 0 %}
            {% else %}{% set winner = '-' %}
            {% endif %}
          {% endif %}
        {% elif key in ['privacyStatus', 'longUploadsStatus'] %}
          {% if v1 != 'N/A' and v2 != 'N/A' %}
            {% if v1 == v2 %}{% set winner = 0 %}
            {% else %}{% set winner = '-' %}
            {% endif %}
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
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
  {% endif %}
</div>
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

def get_channel_info_and_content(username, prev_data=None):
    # Support both legacy usernames and @handles
    if username.startswith('@'):
        handle = username[1:]
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle}&key={YOUTUBE_API_KEY}"
        r = requests.get(search_url)
        data = r.json()
        if 'items' not in data or not data['items']:
            return None, [], [], None, None
        channel_id = data['items'][0]['snippet']['channelId'] if 'channelId' in data['items'][0]['snippet'] else data['items'][0]['id']['channelId']
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,brandingSettings,topicDetails,contentDetails,status&id={channel_id}&key={YOUTUBE_API_KEY}"
    else:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,brandingSettings,topicDetails,contentDetails,status&forUsername={username}&key={YOUTUBE_API_KEY}"
    r = requests.get(url)
    data = r.json()
    if 'items' not in data or not data['items']:
        return None, [], [], None, None, None
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

    # Fetch comments from all videos (limited to first 50 videos for performance)
    all_comments = []
    for video in videos:
        video_id = video['contentDetails']['videoId']
        comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=50&key={YOUTUBE_API_KEY}"
        try:
            comments_resp = requests.get(comments_url)
            comments_data = comments_resp.json()
            if 'items' in comments_data:
                for c in comments_data['items']:
                    top_comment = c['snippet']['topLevelComment']['snippet']
                    all_comments.append(top_comment['textDisplay'])
        except Exception:
            pass

    # Generate a simple comments summary (sentiment: positive/negative/neutral count)
    comments_summary = None
    if all_comments:
        pos, neg, neu = 0, 0, 0
        for comment in all_comments:
            lc = comment.lower()
            if any(w in lc for w in ['love', 'awesome', 'great', 'good', 'amazing', 'best', 'nice', 'congrats', 'congratulations', 'superb', 'fantastic', 'helpful', 'thanks', 'thank you']):
                pos += 1
            elif any(w in lc for w in ['bad', 'worst', 'hate', 'dislike', 'awful', 'terrible', 'boring', 'poor', 'useless', 'fake', 'scam']):
                neg += 1
            else:
                neu += 1
        total = pos + neg + neu
        comments_summary = f"Positive: {pos}, Negative: {neg}, Neutral: {neu} (from {total} comments)"

    # --- Subscriber history tracking ---
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    sub_count = int(item['statistics'].get('subscriberCount', 0)) if 'statistics' in item and 'subscriberCount' in item['statistics'] else None
    sub_history = []
    if prev_data and 'sub_history' in prev_data:
        sub_history = prev_data['sub_history']
        # Only add if date is new or value changed
        if sub_count is not None and (not sub_history or sub_history[-1]['date'] != today or sub_history[-1]['count'] != sub_count):
            sub_history.append({'date': today, 'count': sub_count})
    else:
        if sub_count is not None:
            sub_history = [{'date': today, 'count': sub_count}]

    version = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_to_save = {
        'version': version,
        'info': item,
        'playlists': playlists,
        'videos': videos,
        'sub_history': sub_history
    }
    return item, playlists, videos, data_to_save, comments_summary, sub_history




@app.route('/', methods=['GET', 'POST'])


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
    comments_summary = None
    sub_history = None
    page = 'getinfo'
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
                sub_history = cached.get('sub_history', [])
                comments_summary = cached.get('comments_summary', None)
            else:
                info, playlists, videos, data_to_save, comments_summary, sub_history = get_channel_info_and_content(username, None)
                if info:
                    data_to_save['comments_summary'] = comments_summary
                    save_data(username, data_to_save)
                    version = data_to_save['version']
        else:
            cached = load_data(username)
            info, playlists, videos, data_to_save, comments_summary, sub_history = get_channel_info_and_content(username, cached)
            if info:
                data_to_save['comments_summary'] = comments_summary
                save_data(username, data_to_save)
                version = data_to_save['version']

        # If compare requested and both usernames present, load comparison info
        if compare and username and compare_username:
            # Load or fetch compare user info
            compare_cached = load_data(compare_username)
            if compare_cached:
                compare_info = compare_cached.get('info')
            else:
                compare_info, _, _, compare_data_to_save, _, _ = get_channel_info_and_content(compare_username, None)
                if compare_info:
                    save_data(compare_username, compare_data_to_save)
            page = 'compare'
        if not info:
            error = 'User not found or API error.'
        elif compare and not compare_info:
            error = f'Compare user "{compare_username}" not found or API error.'
    else:
        page = request.args.get('page', 'getinfo')
        if page == 'compare':
            # Load last compared users if any
            username = request.args.get('username', '')
            compare_username = request.args.get('compare_username', '')
            if username and compare_username:
                cached = load_data(username)
                compare_cached = load_data(compare_username)
                if cached:
                    info = cached.get('info')
                if compare_cached:
                    compare_info = compare_cached.get('info')
    return render_template_string(
        HTML,
        info=info,
        playlists=playlists,
        videos=videos,
        error=error,
        version=version,
        username=username,
        compare_username=compare_username,
        compare_info=compare_info,
        comments_summary=comments_summary,
        sub_history=sub_history,
        page=page
    )

if __name__ == '__main__':
    app.run(debug=True)
