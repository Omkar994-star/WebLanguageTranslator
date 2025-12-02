// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.getAttribute('data-tab');
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
  });
});

// TEXT SECTION
const inputText = document.getElementById('input_text');
const translatedText = document.getElementById('translated_text');
const textStatus = document.getElementById('text_status');
const textAudio = document.getElementById('text_audio');

document.getElementById('translate_text_btn').addEventListener('click', async ()=>{
  const text = inputText.value.trim();
  const lang = document.getElementById('text_lang').value;
  textStatus.innerText = "Status: Translating...";
  const res = await fetch('/api/translate_text', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({text, language: lang})
  });
  const j = await res.json();
  if(j.translated_text){
    translatedText.value = j.translated_text;
    textStatus.innerText = "Status: Translation Complete";
  } else {
    textStatus.innerText = "Error: " + (j.error || 'Unknown');
  }
});

document.getElementById('play_text_btn').addEventListener('click', async ()=>{
  const text = translatedText.value.trim();
  if(!text){ textStatus.innerText = "No translated text to play"; return; }
  textStatus.innerText = "Status: Generating audio...";
  const res = await fetch('/api/play_text_audio', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({text})
  });
  const j = await res.json();
  if(j.audio_url){
    textAudio.src = j.audio_url;
    textAudio.style.display = 'block';
    textAudio.play().catch(()=>{}); // autoplay may be blocked
    textStatus.innerText = "Status: Playing Audio";
  } else {
    textStatus.innerText = "Error: " + (j.error || 'Unknown');
  }
});

document.getElementById('clear_text_btn').addEventListener('click', ()=>{
  inputText.value = '';
  translatedText.value = '';
  textStatus.innerText = 'Status: Cleared';
  textAudio.style.display = 'none';
});

// AUDIO SECTION
let mediaRecorder = null;
let audioChunks = [];
let recordedBlob = null;

const audioStatus = document.getElementById('audio_status');
const audioOut = document.getElementById('audio_out');
const audioTranslated = document.getElementById('audio_translated');

document.getElementById('record_btn').addEventListener('click', async ()=>{
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = () => {
      recordedBlob = new Blob(audioChunks, { type: 'audio/webm' });
      audioStatus.innerText = "Status: Recording stopped (ready)";
    };
    mediaRecorder.start();
    audioStatus.innerText = "Status: Recording...";
  } catch (err) {
    audioStatus.innerText = "Error: Microphone access denied";
  }
});

document.getElementById('stop_btn').addEventListener('click', ()=>{
  if(mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t=>t.stop());
  }
});

document.getElementById('play_local_btn').addEventListener('click', ()=>{
  if(!recordedBlob){ audioStatus.innerText = "No recorded audio"; return; }
  const url = URL.createObjectURL(recordedBlob);
  audioOut.src = url;
  audioOut.style.display = 'block';
  audioOut.play().catch(()=>{});
});

document.getElementById('translate_audio_btn').addEventListener('click', async ()=>{
  if(!recordedBlob){ audioStatus.innerText = "Record audio first"; return; }
  const language = document.getElementById('audio_lang').value;
  if(!language){ audioStatus.innerText = "Select target language"; return; }
  audioStatus.innerText = "Status: Uploading & Translating...";
  const fd = new FormData();
  // convert blob to file
  const file = new File([recordedBlob], "audio.webm", { type: recordedBlob.type });
  fd.append('audio', file);
  fd.append('language', language);

  try {
    const res = await fetch('/api/translate_audio', { method:'POST', body: fd });
    const j = await res.json();
    if(j.error){ audioStatus.innerText = "Error: " + j.error; return; }
    audioTranslated.value = `Original: ${j.transcribed_text}\nTranslated: ${j.translated_text}`;
    if(j.audio_url){
      audioOut.src = j.audio_url;
      audioOut.style.display = 'block';
      audioOut.play().catch(()=>{});
    }
    audioStatus.innerText = "Status: Translation Complete";
  } catch (err) {
    audioStatus.innerText = "Error: Upload failed";
    console.error(err);
  }
});

document.getElementById('clear_audio_btn').addEventListener('click', ()=>{
  audioTranslated.value = '';
  audioOut.style.display = 'none';
  audioStatus.innerText = 'Status: Cleared';
});
