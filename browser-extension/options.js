// The tool's address (chrome.storage.sync toolUrl); the default is the one in background.js.
const DEFAULT_TOOL_URL = 'https://gitlaloosh.github.io/dscan-tool/';
const input = document.getElementById('toolUrl'), status = document.getElementById('status');
function say(text, err){ status.textContent = text; status.className = err ? 'err' : ''; }
function valid(u){
  try{ const x = new URL(u); return ['https:', 'http:', 'file:'].includes(x.protocol) ? x.href.split('#')[0] : null; }catch(e){ return null; }
}
chrome.storage.sync.get({toolUrl: DEFAULT_TOOL_URL}).then(({toolUrl}) => { input.value = toolUrl; });
document.getElementById('save').addEventListener('click', async () => {
  const u = valid(input.value.trim());
  if(!u){ say('That isn\'t a web address (it should start with https://).', true); return; }
  await chrome.storage.sync.set({toolUrl: u});
  input.value = u; say('Saved.');
});
document.getElementById('reset').addEventListener('click', async () => {
  await chrome.storage.sync.set({toolUrl: DEFAULT_TOOL_URL});
  input.value = DEFAULT_TOOL_URL; say('Back to the default address.');
});
