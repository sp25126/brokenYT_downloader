// Content script injected into whop.com pages
function getCleanTitle() {
  // 1. Look for lesson heading in h1 or h2
  const headings = document.querySelectorAll("h1, h2");
  for (const h of headings) {
    const text = h.innerText?.trim();
    if (text && text.length > 2 && !text.toLowerCase().includes("whop")) {
      return text;
    }
  }

  // 2. Look for active sidebar lesson item
  const activeItem = document.querySelector("[aria-current='page'], [data-active='true'], .active");
  if (activeItem && activeItem.innerText) {
    return activeItem.innerText.split("\n")[0].trim();
  }

  // 3. Fallback to document title
  const docTitle = document.title || "";
  return docTitle.split("|")[0].replace("THE ECOM MASTERCLASS", "").trim() || "Lesson";
}

// Respond to background worker queries
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_LESSON_INFO") {
    sendResponse({
      title: getCleanTitle(),
      url: window.location.href
    });
  }
  return true;
});
