// EVE Threat Assessment for zKillboard (v1.0.0, with the tool's v2026.10.14.80). the owner: "create a google chrome extension
// that would let me right click on a pilot name or killmail in zkillboard.com and send it to the tool"; the menu items:
// "all three" (kill links and pages, pilot links and pages, a selected pilot name).
//
// What it does: adds right-click items and opens the tool in a new tab with a link the tool reads (see index.html,
// sharedKillLinkInit): #zkill=<killmail ID>, #pilot=<character ID>, #pilotname=<name>. Nothing else: no access to any
// page's content, no network requests of its own, nothing stored but the tool's address (chrome.storage.sync).
// Permissions: contextMenus (the items) and storage (the address set in the options page).

const DEFAULT_TOOL_URL = 'https://gitlaloosh.github.io/dscan-tool/';
const ZKB = ['*://zkillboard.com/', '*://*.zkillboard.com/'];
const MENUS = [
  {id: 'eta-kill-link', title: 'Open kill in EVE Threat Assessment', contexts: ['link'], targetUrlPatterns: ZKB.map(p => p + 'kill/*')},
  {id: 'eta-kill-page', title: 'Open this kill in EVE Threat Assessment', contexts: ['page'], documentUrlPatterns: ZKB.map(p => p + 'kill/*')},
  {id: 'eta-pilot-link', title: 'Analyze pilot in EVE Threat Assessment', contexts: ['link'], targetUrlPatterns: ZKB.map(p => p + 'character/*')},
  {id: 'eta-pilot-page', title: 'Analyze this pilot in EVE Threat Assessment', contexts: ['page'], documentUrlPatterns: ZKB.map(p => p + 'character/*')},
  {id: 'eta-pilot-name', title: 'Analyze "%s" in EVE Threat Assessment', contexts: ['selection']}
];
const KILL_RE = /zkillboard\.com\/kill\/(\d+)/i;
const PILOT_RE = /zkillboard\.com\/character\/(\d+)/i;
const MAX_NAME = 37;   // EVE pilot names are at most 37 characters

// The tool link for a click, or null when there's nothing to open (exported for the extension's check).
function etaLinkFor(info){
  let m;
  switch(info.menuItemId){
    case 'eta-kill-link': case 'eta-kill-page':
      m = String(info.menuItemId === 'eta-kill-link' ? info.linkUrl : info.pageUrl).match(KILL_RE);
      return m ? `#zkill=${m[1]}` : null;
    case 'eta-pilot-link': case 'eta-pilot-page':
      m = String(info.menuItemId === 'eta-pilot-link' ? info.linkUrl : info.pageUrl).match(PILOT_RE);
      return m ? `#pilot=${m[1]}` : null;
    case 'eta-pilot-name': {
      const text = String(info.selectionText || '').replace(/\s+/g, ' ').trim();
      if((m = text.match(KILL_RE))) return `#zkill=${m[1]}`;      // a selected kill link
      if((m = text.match(PILOT_RE))) return `#pilot=${m[1]}`;
      if(!text || text.length > MAX_NAME) return null;
      return `#pilotname=${encodeURIComponent(text)}`;
    }
  }
  return null;
}

async function etaToolUrl(){
  const {toolUrl} = await chrome.storage.sync.get({toolUrl: DEFAULT_TOOL_URL});
  return String(toolUrl || DEFAULT_TOOL_URL).split('#')[0];
}

async function etaHandleClick(info){
  const link = etaLinkFor(info);
  if(!link) return null;
  const url = (await etaToolUrl()) + link;
  await chrome.tabs.create({url});
  return url;
}

function etaCreateMenus(){
  chrome.contextMenus.removeAll(() => { for(const m of MENUS) chrome.contextMenus.create(m); });
}

chrome.runtime.onInstalled.addListener(etaCreateMenus);
chrome.contextMenus.onClicked.addListener((info) => { etaHandleClick(info); });
// for tools/page_checks/extension_check.py
self.ETA = {MENUS, DEFAULT_TOOL_URL, etaLinkFor, etaHandleClick, etaToolUrl};
