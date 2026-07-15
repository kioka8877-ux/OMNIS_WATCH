// OMNIS-WATCH — Gate 1 Viewer
// Upload video → set IN/OUT → choose format/blur-pad/speed/volume → generate JSON

const app = document.getElementById('app');

// ── State ──────────────────────────────────────────────────────────────

let state = {
  videoLoaded: false,
  videoName: '',
  videoDuration: 0,
  currentTime: 0,
  isPlaying: false,
  inPoint: 0,        // seconds
  outPoint: 0,       // seconds
  format: '9:16',
  blurPad: true,
  speed: 1.0,
  volume: 1.0,
  draggingMarker: null, // 'in' | 'out' | null
};

// ── Render ─────────────────────────────────────────────────────────────

function render() {
  if (!state.videoLoaded) {
    renderUpload();
  } else {
    renderEditor();
  }
}

// ── Upload Screen ──────────────────────────────────────────────────────

function renderUpload() {
  app.innerHTML = `
    <div class="min-h-dvh flex flex-col items-center justify-center p-6">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-white mb-2">OMNIS-WATCH</h1>
        <p class="text-gray-500">Gate 1 — Upload & Cut</p>
      </div>

      <div id="uploadZone" class="upload-zone w-full max-w-md">
        <svg class="mx-auto mb-4" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4ecca3" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <p class="text-gray-300 mb-2 font-medium">Drop your video here</p>
        <p class="text-gray-500 text-xs">or click to browse — MP4, MOV, AVI, MKV</p>
        <input type="file" id="fileInput" accept="video/*" class="hidden">
      </div>

      <div class="mt-6 text-center">
        <p class="text-gray-600 text-xs">
          The video stays in your browser. Nothing is uploaded to any server.
        </p>
      </div>
    </div>
  `;

  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('fileInput');

  uploadZone.addEventListener('click', () => fileInput.click());

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });

  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });

  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
      loadVideo(file);
    }
  });

  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      loadVideo(file);
    }
  });
}

// ── Load Video ─────────────────────────────────────────────────────────

function loadVideo(file) {
  state.videoName = file.name;
  const url = URL.createObjectURL(file);

  // Create a video element to get duration
  const video = document.createElement('video');
  video.preload = 'metadata';
  video.src = url;

  video.addEventListener('loadedmetadata', () => {
    state.videoDuration = video.duration;
    state.outPoint = video.duration; // Default OUT = end
    state.inPoint = 0;               // Default IN = start
    state.videoLoaded = true;
    state.videoUrl = url;
    render();
  });
}

// ── Editor Screen ──────────────────────────────────────────────────────

function renderEditor() {
  const inTs = formatTime(state.inPoint);
  const outTs = formatTime(state.outPoint);
  const selDuration = (state.outPoint - state.inPoint).toFixed(1);

  app.innerHTML = `
    <div class="min-h-dvh p-4 sm:p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-lg font-bold text-white">OMNIS-WATCH — Gate 1</h1>
          <p class="text-gray-500 text-xs">${state.videoName}</p>
        </div>
        <button id="btnReset" class="btn-secondary px-3 py-1.5 rounded-lg text-xs">
          ← New Video
        </button>
      </div>

      <div class="flex flex-col lg:flex-row gap-6 max-w-5xl mx-auto">

        <!-- Left: Video Player + Timeline -->
        <div class="flex-1 flex flex-col items-center">
          <!-- Video container -->
          <div class="video-container mb-4">
            <video id="videoPlayer" src="${state.videoUrl}" playsinline></video>
            <div id="playOverlay" class="play-overlay">
              <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            </div>
          </div>

          <!-- Timeline -->
          <div class="w-full max-w-md">
            <div id="timelineTrack" class="timeline-track mb-2">
              <div id="timelineSelection" class="timeline-selection"></div>
              <div id="timelineProgress" class="timeline-progress"></div>
              <div id="timelineInMarker" class="timeline-in-marker" data-label="IN"></div>
              <div id="timelineOutMarker" class="timeline-out-marker" data-label="OUT"></div>
              <div id="timelineCurrent" class="timeline-current"></div>
            </div>

            <!-- Time display -->
            <div class="flex justify-between text-xs text-gray-400 mb-3">
              <span id="currentTime">00:00.0</span>
              <span class="text-gray-600">Duration: ${state.videoDuration.toFixed(1)}s</span>
              <span id="selectionDuration" class="text-[#4ecca3] font-bold">SEL: ${selDuration}s</span>
            </div>

            <!-- Quick controls -->
            <div class="flex gap-2 mb-3">
              <button id="btnSetIn" class="btn-secondary flex-1 py-2 rounded-lg text-xs">
                ⬅ Set IN (${inTs})
              </button>
              <button id="btnSetOut" class="btn-secondary flex-1 py-2 rounded-lg text-xs">
                Set OUT (${outTs}) ➜
              </button>
            </div>

            <!-- Playback speed -->
            <div class="flex items-center gap-2 text-xs text-gray-400">
              <span>Preview speed:</span>
              <select id="previewSpeed" class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs">
                <option value="0.25">0.25x</option>
                <option value="0.5">0.5x</option>
                <option value="1" selected>1x</option>
                <option value="2">2x</option>
              </select>
              <span class="text-gray-600 ml-auto">Drag IN/OUT markers to adjust</span>
            </div>
          </div>
        </div>

        <!-- Right: Settings + Output -->
        <div class="flex-1 flex flex-col gap-4">

          <!-- Format selection -->
          <div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <h3 class="text-white font-bold mb-3 text-sm">Format</h3>
            <div class="grid grid-cols-3 gap-2">
              <button data-format="9:16" class="format-btn btn-secondary py-3 rounded-lg text-xs ${state.format === '9:16' ? 'btn-active' : ''}">
                <div class="mb-1">📱</div>9:16<br><span class="text-[10px]">1080×1920</span>
              </button>
              <button data-format="16:9" class="format-btn btn-secondary py-3 rounded-lg text-xs ${state.format === '16:9' ? 'btn-active' : ''}">
                <div class="mb-1">🖥️</div>16:9<br><span class="text-[10px]">1920×1080</span>
              </button>
              <button data-format="1:1" class="format-btn btn-secondary py-3 rounded-lg text-xs ${state.format === '1:1' ? 'btn-active' : ''}">
                <div class="mb-1">⬜</div>1:1<br><span class="text-[10px]">1080×1080</span>
              </button>
            </div>
          </div>

          <!-- Blur pad -->
          <div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-white font-bold text-sm">Blur-Pad</h3>
                <p class="text-gray-500 text-xs">Blurred background fill</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="blurPadToggle" ${state.blurPad ? 'checked' : ''} class="sr-only peer">
                <div class="w-11 h-6 bg-gray-700 peer-focus:ring-2 peer-focus:ring-[#4ecca3] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#4ecca3]"></div>
              </label>
            </div>
          </div>

          <!-- Speed -->
          <div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-white font-bold text-sm">Speed</h3>
              <span id="speedValue" class="text-[#4ecca3] font-bold text-sm">${state.speed}x</span>
            </div>
            <input type="range" id="speedSlider" min="0.25" max="3" step="0.25" value="${state.speed}" class="w-full accent-[#4ecca3]">
            <div class="flex justify-between text-[10px] text-gray-600 mt-1">
              <span>0.25x</span><span>1x</span><span>2x</span><span>3x</span>
            </div>
          </div>

          <!-- Volume -->
          <div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-white font-bold text-sm">Volume</h3>
              <span id="volumeValue" class="text-[#4ecca3] font-bold text-sm">${state.volume}x</span>
            </div>
            <input type="range" id="volumeSlider" min="0" max="3" step="0.1" value="${state.volume}" class="w-full accent-[#4ecca3]">
            <div class="flex justify-between text-[10px] text-gray-600 mt-1">
              <span>0x</span><span>1x</span><span>2x</span><span>3x</span>
            </div>
          </div>

          <!-- JSON Output -->
          <div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-white font-bold text-sm">Gate 1 JSON</h3>
              <button id="btnCopyJson" class="btn-secondary px-2 py-1 rounded text-xs">Copy</button>
            </div>
            <div id="jsonOutput" class="json-output bg-gray-950 p-3 rounded-lg text-gray-300"></div>
          </div>

          <!-- Generate button -->
          <button id="btnGenerate" class="btn-primary py-3 rounded-xl text-sm">
            ✓ Generate Gate 1 JSON & Launch F01
          </button>
        </div>
      </div>
    </div>
  `;

  setupEditorEvents();
  updateTimeline();
  updateJsonOutput();
}

// ── Editor Events ──────────────────────────────────────────────────────

function setupEditorEvents() {
  const video = document.getElementById('videoPlayer');
  const playOverlay = document.getElementById('playOverlay');
  const timelineTrack = document.getElementById('timelineTrack');

  // Reset
  document.getElementById('btnReset').addEventListener('click', () => {
    state.videoLoaded = false;
    state.videoUrl = null;
    render();
  });

  // Play/pause
  function togglePlay() {
    if (video.paused) {
      video.play();
    } else {
      video.pause();
    }
  }

  playOverlay.addEventListener('click', togglePlay);
  video.addEventListener('click', togglePlay);

  video.addEventListener('play', () => {
    state.isPlaying = true;
    playOverlay.classList.add('hidden');
  });

  video.addEventListener('pause', () => {
    state.isPlaying = false;
    playOverlay.classList.remove('hidden');
  });

  video.addEventListener('timeupdate', () => {
    state.currentTime = video.currentTime;
    document.getElementById('currentTime').textContent = formatTime(video.currentTime);
    updateTimelineCursor();
  });

  // Preview speed
  document.getElementById('previewSpeed').addEventListener('change', (e) => {
    video.playbackRate = parseFloat(e.target.value);
  });

  // Set IN/OUT buttons
  document.getElementById('btnSetIn').addEventListener('click', () => {
    state.inPoint = video.currentTime;
    if (state.inPoint >= state.outPoint) {
      state.outPoint = Math.min(state.videoDuration, state.inPoint + 1);
    }
    updateTimeline();
    updateJsonOutput();
    renderTimeLabels();
  });

  document.getElementById('btnSetOut').addEventListener('click', () => {
    state.outPoint = video.currentTime;
    if (state.outPoint <= state.inPoint) {
      state.inPoint = Math.max(0, state.outPoint - 1);
    }
    updateTimeline();
    updateJsonOutput();
    renderTimeLabels();
  });

  // Timeline click — seek
  timelineTrack.addEventListener('click', (e) => {
    if (state.draggingMarker) return;
    const rect = timelineTrack.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    video.currentTime = pct * state.videoDuration;
  });

  // Timeline marker dragging
  const inMarker = document.getElementById('timelineInMarker');
  const outMarker = document.getElementById('timelineOutMarker');

  inMarker.addEventListener('mousedown', (e) => {
    e.preventDefault();
    state.draggingMarker = 'in';
  });

  outMarker.addEventListener('mousedown', (e) => {
    e.preventDefault();
    state.draggingMarker = 'out';
  });

  document.addEventListener('mousemove', (e) => {
    if (!state.draggingMarker) return;
    const rect = timelineTrack.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const time = pct * state.videoDuration;

    if (state.draggingMarker === 'in') {
      state.inPoint = Math.min(time, state.outPoint - 0.5);
    } else {
      state.outPoint = Math.max(time, state.inPoint + 0.5);
    }
    updateTimeline();
    updateJsonOutput();
    renderTimeLabels();
  });

  document.addEventListener('mouseup', () => {
    state.draggingMarker = null;
  });

  // Format buttons
  document.querySelectorAll('.format-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.format = btn.dataset.format;
      document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('btn-active'));
      btn.classList.add('btn-active');
      updateJsonOutput();
    });
  });

  // Blur pad toggle
  document.getElementById('blurPadToggle').addEventListener('change', (e) => {
    state.blurPad = e.target.checked;
    updateJsonOutput();
  });

  // Speed slider
  document.getElementById('speedSlider').addEventListener('input', (e) => {
    state.speed = parseFloat(e.target.value);
    document.getElementById('speedValue').textContent = state.speed + 'x';
    updateJsonOutput();
  });

  // Volume slider
  document.getElementById('volumeSlider').addEventListener('input', (e) => {
    state.volume = parseFloat(e.target.value);
    document.getElementById('volumeValue').textContent = state.volume + 'x';
    video.volume = Math.min(1, state.volume);
    updateJsonOutput();
  });

  // Copy JSON
  document.getElementById('btnCopyJson').addEventListener('click', () => {
    const json = generateJson();
    navigator.clipboard.writeText(JSON.stringify(json, null, 2));
    const btn = document.getElementById('btnCopyJson');
    btn.textContent = '✓ Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  });

  // Generate & Launch
  document.getElementById('btnGenerate').addEventListener('click', () => {
    const json = generateJson();
    const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gate1_config.json';
    a.click();
    URL.revokeObjectURL(url);
  });
}

// ── Timeline ───────────────────────────────────────────────────────────

function updateTimeline() {
  const inPct = (state.inPoint / state.videoDuration) * 100;
  const outPct = (state.outPoint / state.videoDuration) * 100;

  const selection = document.getElementById('timelineSelection');
  const inMarker = document.getElementById('timelineInMarker');
  const outMarker = document.getElementById('timelineOutMarker');

  if (selection) {
    selection.style.left = inPct + '%';
    selection.style.width = (outPct - inPct) + '%';
  }
  if (inMarker) {
    inMarker.style.left = inPct + '%';
  }
  if (outMarker) {
    outMarker.style.left = outPct + '%';
  }
}

function updateTimelineCursor() {
  const cursor = document.getElementById('timelineCurrent');
  if (cursor) {
    const pct = (state.currentTime / state.videoDuration) * 100;
    cursor.style.left = pct + '%';
  }
}

function renderTimeLabels() {
  const inBtn = document.getElementById('btnSetIn');
  const outBtn = document.getElementById('btnSetOut');
  const selDur = document.getElementById('selectionDuration');

  if (inBtn) inBtn.textContent = `⬅ Set IN (${formatTime(state.inPoint)})`;
  if (outBtn) outBtn.textContent = `Set OUT (${formatTime(state.outPoint)}) ➜`;
  if (selDur) selDur.textContent = `SEL: ${(state.outPoint - state.inPoint).toFixed(1)}s`;
}

// ── JSON Generation ────────────────────────────────────────────────────

function generateJson() {
  return {
    source_file: state.videoName,
    in_timestamp: formatTime(state.inPoint),
    out_timestamp: formatTime(state.outPoint),
    format: state.format,
    blur_pad: state.blurPad,
    speed: state.speed,
    volume: state.volume,
    selection_duration: parseFloat((state.outPoint - state.inPoint).toFixed(2)),
    video_duration: parseFloat(state.videoDuration.toFixed(2)),
  };
}

function updateJsonOutput() {
  const output = document.getElementById('jsonOutput');
  if (output) {
    output.textContent = JSON.stringify(generateJson(), null, 2);
  }
}

// ── Helpers ────────────────────────────────────────────────────────────

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(1);
  return `${String(mins).padStart(2, '0')}:${secs.padStart(4, '0')}`;
}

// ── Init ───────────────────────────────────────────────────────────────

render();
