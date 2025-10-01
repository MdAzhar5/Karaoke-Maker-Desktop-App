<h1>🎶 AI Music Splitter Desktop App</h1>

<p>
  A powerful desktop GUI application for music stem separation, built using
  <strong>Python + Tkinter + Spleeter + Pygame</strong>. It allows you to extract vocals,
  drums, bass, and other stems from a song—either from a local file or by pasting a YouTube URL.
</p>

<hr />

<h2>📦 Features</h2>
<ul>
  <li>🎧 Extract stems using <strong>Spleeter</strong> (2, 4, or 5 stems)</li>
  <li>📹 Paste YouTube URL and auto-download audio</li>
  <li>🎵 Play original and all extracted stems with live progress bar</li>
  <li>🎚️ Draggable seekbar to control playback position</li>
  <li>💡 Intuitive GUI with modern styling and smooth controls</li>
</ul>

<hr />

<h2>🛠️ Requirements</h2>

<pre><code>Python 3.8+
spleeter
pygame
mutagen
requests
</code></pre>

<h3>🔧 Install dependencies:</h3>

<pre><code>pip install spleeter pygame mutagen requests</code></pre>

<hr />

<h2>🚀 How to Run</h2>

<ol>
  <li>Download or clone the repository.</li>
  <li>Ensure you have Python and dependencies installed.</li>
  <li>Run the app using:</li>
</ol>

<pre><code>python main.py</code></pre>

<hr />

<h2>🎬 Usage Guide</h2>

<ol>
  <li>Click <strong>"Browse"</strong> to select a local song <em>or</em> paste a YouTube URL and click <strong>"Download"</strong>.</li>
  <li>Select the number of stems (2, 4, or 5) from the dropdown.</li>
  <li>Click <strong>"Separate Stems"</strong>.</li>
  <li>Once done, use the <strong>play buttons</strong> to listen to:
    <ul>
      <li>Original song</li>
      <li>Vocals, drums, bass, piano, or other stems (depending on your selection)</li>
    </ul>
  </li>
  <li>Track and control playback using the progress bars.</li>
</ol>

<hr />

<h2>🧠 Powered By</h2>
<ul>
  <li><a href="https://github.com/deezer/spleeter" target="_blank">Spleeter</a> by Deezer</li>
  <li><a href="https://www.pygame.org/" target="_blank">Pygame</a></li>
  <li><a href="https://mutagen.readthedocs.io/en/latest/" target="_blank">Mutagen</a></li>
</ul>

<hr />

<h2>📁 Output Directory</h2>
<p>
  All separated stems will be saved in: <code>./output/</code><br />
  Each file will be named by stem (e.g., <code>vocals.wav</code>, <code>drums.wav</code>).
</p>

<hr />

<h2>🙌 Author</h2>
<p>
  Developed with ❤️ by M. Azhar (Aug 2025)
</p>
