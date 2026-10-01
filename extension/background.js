// Background service worker: intercepts all Mux HLS m3u8 requests
chrome.webRequest.onBeforeRequest.addListener(
  async (details) => {
    const url = details.url;
    if (url.includes("stream.mux.com") && url.includes(".m3u8")) {
      console.log("[Whop Harvester] Intercepted stream URL:", url);

      // Query active Whop tab to get the current lesson title
      chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
        let title = "Unknown Lesson";
        if (tabs && tabs[0] && tabs[0].id) {
          try {
            const resp = await chrome.tabs.sendMessage(tabs[0].id, { type: "GET_LESSON_INFO" });
            if (resp && resp.title) {
              title = resp.title;
            }
          } catch (e) {
            if (tabs[0].title) {
              title = tabs[0].title.replace(/\s*\|\s*Whop/i, "").trim();
            }
          }
        }

        // Store into chrome.storage
        chrome.storage.local.get({ harvested: [] }, (data) => {
          const list = data.harvested || [];
          // Avoid duplicate stream URLs
          const existing = list.find((item) => item.url === url);
          if (!existing) {
            list.push({
              title: title,
              url: url,
              timestamp: Date.now()
            });
            chrome.storage.local.set({ harvested: list }, () => {
              console.log(`[Whop Harvester] Saved '${title}' (${list.length} total)`);
            });
          }
        });
      });
    }
  },
  { urls: ["*://stream.mux.com/*"] }
);

// Listen for messages from content or popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "CLEAR_HARVESTED") {
    chrome.storage.local.set({ harvested: [] }, () => {
      sendResponse({ status: "cleared" });
    });
    return true;
  }
});
