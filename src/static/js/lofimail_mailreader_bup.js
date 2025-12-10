

let currentAudio = null;
const speakBtn = document.getElementById('voice-button');
async function speakMail() {
  myAudio = new Audio('static/media/alert.mp3');
  myAudio.play();
  // prevent form submit / navigation if button inside form
  // (only needed if you use onclick attribute somewhere else)
  // event && event.preventDefault && event.preventDefault();

  const mailEl = document.querySelector('.message-body');
  if (!mailEl) {
    console.error("No .message-body element found");
    return;
  }
  const mailContent = mailEl.innerText.trim();
  if (!mailContent) {
    console.log("No mail content to speak");
    return;
  }

  // request audio from Flask
  let response;
  try {
    response = await fetch(`/speak?text=${encodeURIComponent(mailContent)}`);
  } catch (err) {
    console.error("Network error fetching TTS:", err);
    return;
  }

  if (!response.ok) {
    console.error("Server returned error for TTS:", response.status, response.statusText);
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);

  // stop previous audio if playing
  if (currentAudio) {
    try { currentAudio.pause(); } catch(e) {}
    try { URL.revokeObjectURL(currentAudio._blobUrl); } catch(e) {}
    currentAudio = null;
  }

  // keep the audio object reachable by storing in outer variable
  currentAudio = new Audio(url);
  currentAudio._blobUrl = url;
  currentAudio.src = url;
  currentAudio.preload = 'auto';

  // visual state
  speakBtn.classList.add('speaking');

  // cleanup after finished
  currentAudio.addEventListener('ended', () => {
    speakBtn.classList.remove('speaking');
    try { URL.revokeObjectURL(url); } catch(e) {}
    currentAudio = null;
  });

  currentAudio.addEventListener('error', (ev) => {
    console.error('Audio playback error event', ev);
  });

  // attempt to play and handle promise rejections
  try {
    const playPromise = currentAudio.play();
    if (playPromise !== undefined) {
      await playPromise; // wait for playback to actually start
    }
    console.log("Playback started");
  } catch (err) {
    console.warn("audio.play() was rejected:", err);
    // fallback: attach controls to the page so user can manually start it
    currentAudio.controls = true;
    document.body.appendChild(currentAudio);
    // optionally inform the user
    speakBtn.classList.remove('speaking');
  }
}


