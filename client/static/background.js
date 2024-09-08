// import browser from './browser-polyfill.js';

// chrome.runtime.onClicked.addListener(async () => {
//   for (const cs of chrome.runtime.getManifest().content_scripts) {
//     for (const tab of await chrome.tabs.query({})) {
//       if (tab.url.match(/(chrome|chrome-extension):\/\//gi)) {
//         continue;
//       }
//       chrome.scripting.executeScript({
//         files: cs.js,
//         target: { tabId: tab.id, allFrames: cs.all_frames },
//         injectImmediately: cs.run_at === 'document_start'
//       });
//     }
//   }
// });

chrome.action.onClicked.addListener((tab) => {
  chrome.scripting.executeScript({
    files: ['content.js'],
    target: { tabId: tab.id },
    injectImmediately: true,
  });
})

chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
  console.log(message, sender)
  const { tab, action, videoName } = message;
  if (tab.url.match(/(chrome|chrome-extension):\/\//gi)) {
    return false;
  }

  await chrome.scripting.executeScript({
    files: ['content.js'],
    target: { tabId: tab.id },
    injectImmediately: true,
  })
    .then(console.log('content script injected'));

  if (action === 'start' || action === 'stop') {
    await chrome.tabs.sendMessage(tab.id, { action, videoName });
  }
  return true;
});
