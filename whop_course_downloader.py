import os
import sys
import re
import json
import argparse
import subprocess
import requests

sys.stdout.reconfigure(encoding='utf-8')

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
COOKIE_FILE = os.path.join(os.getcwd(), "cookies.txt")

def sanitize(name):
    clean = re.sub(r'[\\/*?:"<>|]', '', name).strip()
    return clean[:120] if clean else "Lesson"

def load_cookies():
    """
    Loads cookies from an environment variable 'WHOP_COOKIE' or a local 'cookies.txt' file.
    If neither exists, prompts the user once to paste their cookie string.
    """
    if os.environ.get("WHOP_COOKIE"):
        return os.environ.get("WHOP_COOKIE").strip()

    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content

    print("=" * 70)
    print("                 WHOP SESSION SETUP REQUIRED")
    print("=" * 70)
    print("1. Log in to whop.com in your browser.")
    print("2. Open DevTools (F12) -> Network tab -> click any request to whop.com.")
    print("3. Copy the 'cookie' header value and paste it below.")
    print("=" * 70)
    user_cookie = input("\nPaste Whop Cookie here: ").strip()
    if user_cookie:
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write(user_cookie)
        print(f"[✓] Saved session to {COOKIE_FILE} (will be remembered automatically)")
        return user_cookie
    else:
        print("[!] No cookie provided. Exiting.")
        sys.exit(1)

def get_headers(cookies):
    return {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'cookie': cookies,
        'origin': 'https://whop.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',
        'x-whop-api-proxy-key': 'test',
        'x-whop-app-name': 'web',
        'x-whop-force-new-permission-system': 'true',
        'x-whop-id': 'biz_mfWiQYc1r0k51O',
        'x-whop-introspection': '1'
    }

def get_courses(headers, experience_ids=None):
    if not experience_ids:
        experience_ids = ['exp_FuPZMaWCRZnSOr', 'exp_JCxIoTDgr2TpzF']

    all_courses = []
    seen = set()

    for exp_id in experience_ids:
        payload = {
            'operationName': 'CoreFetchCourses',
            'query': """query CoreFetchCourses($experienceId: ID, $companyId: ID, $first: Int, $after: String) {
  listCourses(experienceId: $experienceId, companyId: $companyId, first: $first, after: $after) {
    edges {
      node {
        id
        title
        chaptersCount
        totalLessonsCount
      }
    }
  }
}""",
            'variables': {'experienceId': exp_id, 'first': 100}
        }

        try:
            r = requests.post('https://whop.com/api/graphql/CoreFetchCourses', headers=headers, json=payload)
            if r.ok:
                edges = r.json().get('data', {}).get('listCourses', {}).get('edges', [])
                for e in edges:
                    node = e.get('node', {})
                    if node.get('id') and node['id'] not in seen:
                        seen.add(node['id'])
                        all_courses.append(node)
        except Exception:
            pass

    return all_courses

def get_course_outline(course_id, headers):
    payload = {
        'operationName': 'CoreFetchCourse',
        'query': """query CoreFetchCourse($id: ID!) {
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
}""",
        'variables': {'id': course_id}
    }

    r = requests.post('https://whop.com/api/graphql/CoreFetchCourse', headers=headers, json=payload)
    if not r.ok:
        return []

    chapters = r.json().get('data', {}).get('course', {}).get('chapters', [])
    lessons = []
    for chap in chapters:
        for les in chap.get('lessons', []):
            lessons.append({
                'chapter': chap.get('title'),
                'id': les.get('id'),
                'title': les.get('title')
            })
    return lessons

def get_lesson_stream(lesson_id, headers):
    url = f"https://whop.com/api/v1/course_lessons/{lesson_id}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        va = data.get('video_asset')
        if va and va.get('signed_playback_id') and va.get('signed_video_playback_token'):
            pid = va['signed_playback_id']
            token = va['signed_video_playback_token']
            return f"https://stream.mux.com/{pid}.m3u8?token={token}", data.get('title')
    return None, None

def download_video(stream_url, target_path):
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--concurrent-fragments", "4",
        "--retries", "10",
        "--fragment-retries", "10",
        stream_url,
        "-o", target_path
    ]
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Whop Automated Course Downloader")
    parser.add_argument("--all", action="store_true", help="Download all available courses automatically")
    parser.add_argument("--course", type=int, help="Download a specific course number from the list")
    parser.add_argument("--skip", nargs="*", default=["yapping"], help="Course titles or keywords to skip (default: yapping)")
    args = parser.parse_args()

    print("=" * 70)
    print("             WHOP COURSE BULK DOWNLOADER (CLI)")
    print("=" * 70)

    cookies = load_cookies()
    headers = get_headers(cookies)

    print("\n[*] Fetching course library from Whop...")
    courses = get_courses(headers)
    if not courses:
        print("[!] No courses retrieved. Your session cookie may be invalid or expired.")
        if os.path.exists(COOKIE_FILE):
            os.remove(COOKIE_FILE)
            print("[!] Removed cached cookies.txt. Please run again with a fresh cookie.")
        return

    print(f"\n[✓] Found {len(courses)} available courses:\n")
    for idx, c in enumerate(courses, 1):
        print(f"  [{idx:2d}] {c['title']} ({c.get('totalLessonsCount', 0)} lessons)")

    selected = []
    if args.all:
        selected = courses
    elif args.course and 1 <= args.course <= len(courses):
        selected = [courses[args.course - 1]]
    else:
        print("\n  [A] Download ALL courses")
        print("  [Q] Quit")
        choice = input("\n>>> Select a course number (or 'A' for all): ").strip().upper()
        if choice == 'Q':
            return
        if choice == 'A':
            selected = courses
        elif choice.isdigit() and 1 <= int(choice) <= len(courses):
            selected = [courses[int(choice) - 1]]
        else:
            print("[!] Invalid selection.")
            return

    skip_keywords = [s.lower() for s in args.skip]

    for c in selected:
        title_lower = c["title"].lower()
        if any(sk in title_lower for sk in skip_keywords):
            print(f"\n[~] Skipping course: {c['title']}")
            continue

        course_name = sanitize(c["title"])
        course_folder = os.path.join(DOWNLOAD_DIR, course_name)
        os.makedirs(course_folder, exist_ok=True)

        print("\n" + "=" * 70)
        print(f"[*] Course: {c['title']}")
        print(f"[*] Target Directory: {course_folder}")
        print("=" * 70)

        lessons = get_course_outline(c["id"], headers)
        print(f"[*] Found {len(lessons)} lessons in course outline.")

        for idx, les in enumerate(lessons, 1):
            clean_title = sanitize(les['title'])
            target_path = os.path.join(course_folder, f"{idx:02d}_{clean_title}.mp4")

            if os.path.exists(target_path):
                print(f"[~] [{idx}/{len(lessons)}] Already downloaded: {os.path.basename(target_path)}")
                continue

            print(f"\n[+] [{idx}/{len(lessons)}] Resolving video stream: {les['title']}...")
            stream_url, real_title = get_lesson_stream(les['id'], headers)

            if not stream_url:
                print(f"[-] No video stream found for lesson (text or quiz).")
                continue

            print(f"[✓] Stream captured! Downloading 1080p video with yt-dlp...")
            download_video(stream_url, target_path)

    print("\n" + "=" * 70)
    print("[SUCCESS] All requested courses downloaded locally!")
    print("=" * 70)

if __name__ == "__main__":
    main()
