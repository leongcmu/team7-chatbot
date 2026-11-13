// Minimal independent frontend. Set API_BASE to your hosted FastAPI URL.
// Never put GEMINI_API_KEY in JavaScript or HTML.
const API_BASE = 'http://127.0.0.1:8000';
const sessionId = crypto.randomUUID().replaceAll('-', '_');
const form = document.querySelector('#chat-form');
const messages = document.querySelector('#messages');
const status = document.querySelector('#status');
function showMessage(text, role) {
  const el = document.createElement('div'); el.className = `message ${role}`;
  el.textContent = text; messages.appendChild(el); return el;
}
form.addEventListener('submit', async event => {
  event.preventDefault(); const input = document.querySelector('#question');
  const message = input.value.trim(); if (!message) return;
  showMessage(message, 'user'); input.value = ''; status.textContent = 'Thinking...';
  try {
    const response = await fetch(`${API_BASE}/chat`, {method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message,session_id:sessionId})});
    if (!response.ok) throw new Error('Chat request failed');
    const data = await response.json(); const bubble = showMessage(data.answer,'assistant');
    // All links come from structured backend fields, not from generated prose.
    for (const action of data.actions || []) {
      const link=document.createElement('a'); link.href=action.url;
      link.textContent=action.label; link.className='action';
      link.target='_blank'; link.rel='noopener noreferrer'; bubble.appendChild(link);
    }
    for (const article of data.related_articles || []) {
      const link=document.createElement('a'); link.href=article.url;
      link.textContent=`Read: ${article.title}`; link.target='_blank';
      link.rel='noopener noreferrer'; bubble.appendChild(link);
    }
    status.textContent='';
  } catch (error) { status.textContent='Chat unavailable. Check the backend URL and CORS settings.'; }
});
