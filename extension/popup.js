document.addEventListener("DOMContentLoaded", async () => {
  const courseSelect = document.getElementById("courseSelect");
  const courseCount = document.getElementById("courseCount");
  const fetchBtn = document.getElementById("fetchBtn");
  const progressBox = document.getElementById("progressBox");
  const progressText = document.getElementById("progressText");
  const progressPercent = document.getElementById("progressPercent");
  const progressFill = document.getElementById("progressFill");
  const actionBox = document.getElementById("actionBox");
  const downloadQueueBtn = document.getElementById("downloadQueueBtn");
  const downloadBatBtn = document.getElementById("downloadBatBtn");
  const logBox = document.getElementById("logBox");

  let fetchedManifest = [];
  let selectedCourseTitle = "";

  function log(msg) {
    logBox.style.display = "block";
    const div = document.createElement("div");
    div.innerText = `> ${msg}`;
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
  }

  // Helper to make GraphQL requests through browser session cookies
  async function queryGraphQL(operationName, query, variables) {
    const res = await fetch("https://whop.com/api/graphql/" + operationName, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "accept": "*/*"
      },
      body: JSON.stringify({ operationName, query, variables }),
      credentials: "include"
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  // 1. Load all courses accessible to this account
  async function loadCourses() {
    try {
      const q = `query CoreFetchCourses($first: Int) {
        listCourses(first: $first) {
          edges {
            node {
              id
              title
              totalLessonsCount
            }
          }
        }
      }`;
      const data = await queryGraphQL("CoreFetchCourses", q, { first: 100 });
      const courses = data?.data?.listCourses?.edges?.map(e => e.node) || [];
      
      courseSelect.innerHTML = "";
      if (courses.length === 0) {
        courseSelect.innerHTML = "<option value=''>No courses found. Are you logged in to Whop?</option>";
        courseCount.innerText = "0 courses";
        return;
      }

      courseCount.innerText = `${courses.length} courses available`;
      for (const c of courses) {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.innerText = `${c.title} (${c.totalLessonsCount} lessons)`;
        opt.dataset.title = c.title;
        courseSelect.appendChild(opt);
      }
    } catch (e) {
      console.error(e);
      courseSelect.innerHTML = "<option value=''>Error connecting to Whop. Log in first!</option>";
      log("Error loading courses: " + e.message);
    }
  }

  // 2. Fetch full course outline and Mux signed URLs for every lesson
  fetchBtn.addEventListener("click", async () => {
    const courseId = courseSelect.value;
    if (!courseId) return;

    selectedCourseTitle = courseSelect.selectedOptions[0].dataset.title || "Course";
    fetchBtn.disabled = true;
    progressBox.style.display = "block";
    actionBox.style.display = "none";
    logBox.innerHTML = "";
    fetchedManifest = [];

    try {
      log(`Fetching syllabus for: ${selectedCourseTitle}...`);
      const courseQuery = `query CoreFetchCourse($id: ID!) {
        course(id: $id) {
          id
          title
          chapters {
            id
            title
            lessons {
              id
              title
            }
          }
        }
      }`;

      const res = await queryGraphQL("CoreFetchCourse", courseQuery, { id: courseId });
      const chapters = res?.data?.course?.chapters || [];
      
      const allLessons = [];
      for (const chap of chapters) {
        for (const les of (chap.lessons || [])) {
          allLessons.push({
            chapter: chap.title,
            id: les.id,
            title: les.title
          });
        }
      }

      log(`Found ${allLessons.length} lessons in course outline.`);
      if (allLessons.length === 0) {
        log("No lessons found in this course.");
        fetchBtn.disabled = false;
        return;
      }

      // Query Whop API for each lesson's signed Mux stream URL
      for (let i = 0; i < allLessons.length; i++) {
        const item = allLessons[i];
        const pct = Math.round(((i + 1) / allLessons.length) * 100);
        progressPercent.innerText = `${pct}%`;
        progressFill.style.width = `${pct}%`;
        progressText.innerText = `Resolving [${i + 1}/${allLessons.length}]: ${item.title.substring(0, 30)}...`;

        try {
          const lessonResp = await fetch(`https://whop.com/api/v1/course_lessons/${item.id}`, {
            headers: { "accept": "application/json" },
            credentials: "include"
          });

          if (lessonResp.ok) {
            const data = await lessonResp.json();
            const va = data?.video_asset;
            if (va && va.signed_playback_id && va.signed_video_playback_token) {
              const streamUrl = `https://stream.mux.com/${va.signed_playback_id}.m3u8?token=${va.signed_video_playback_token}`;
              fetchedManifest.push({
                index: i + 1,
                chapter: item.chapter,
                title: item.title,
                url: streamUrl,
                durationSeconds: va.duration_seconds || 0
              });
              log(`✓ [${i + 1}] Captured: ${item.title}`);
            } else {
              log(`- [${i + 1}] (No video asset) ${item.title}`);
            }
          } else {
            log(`! [${i + 1}] Failed to resolve: ${item.title}`);
          }
        } catch (err) {
          log(`! [${i + 1}] Error: ${err.message}`);
        }

        // Small delay to be polite to Whop API
        await new Promise(r => setTimeout(r, 80));
      }

      progressText.innerText = `Completed! Captured ${fetchedManifest.length} video streams.`;
      actionBox.style.display = "block";
    } catch (e) {
      log("Fatal error: " + e.message);
    } finally {
      fetchBtn.disabled = false;
    }
  });

  // 3. Export course_queue.json
  downloadQueueBtn.addEventListener("click", () => {
    if (fetchedManifest.length === 0) return;
    const blob = new Blob([JSON.stringify(fetchedManifest, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `course_queue.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });

  // 4. Export 1-click Windows download_all.bat
  downloadBatBtn.addEventListener("click", () => {
    if (fetchedManifest.length === 0) return;
    let batLines = [
      "@echo off",
      "chcp 65001 > nul",
      "echo ==================================================",
      `echo DOWNLOADING COURSE: ${selectedCourseTitle}`,
      "echo ==================================================",
      "if not exist \"downloads\" mkdir \"downloads\"",
      ""
    ];

    for (const item of fetchedManifest) {
      const cleanTitle = item.title.replace(/[\\/:*?"<>|]/g, "").trim();
      const safeIndex = String(item.index).padStart(2, "0");
      const filename = `downloads\\${safeIndex}_${cleanTitle}.mp4`;
      batLines.push(`echo [${item.index}/${fetchedManifest.length}] Downloading: ${cleanTitle}`);
      batLines.push(`yt-dlp -f "bestvideo+bestaudio/best" --concurrent-fragments 4 --retries 10 --fragment-retries 10 "${item.url}" -o "${filename}"`);
      batLines.push("");
    }

    batLines.push("echo [SUCCESS] All lessons downloaded successfully!");
    batLines.push("pause");

    const blob = new Blob([batLines.join("\r\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `download_${selectedCourseTitle.replace(/[\\/:*?"<>|]/g, "_")}.bat`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });

  // Run on start
  loadCourses();
});
