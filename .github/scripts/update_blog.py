import feedparser
import html
import os
import re
from email.utils import parsedate_to_datetime

DEFAULT_THUMBNAIL = "https://blog.rlarbdlf222.workers.dev/images/blog/og-default.svg"

def clean_html(raw_html):
    """HTML 태그 제거하고 텍스트만 추출"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = html.unescape(cleantext)
    # 줄바꿈과 연속된 공백을 하나의 공백으로 치환
    cleantext = re.sub(r'\s+', ' ', cleantext)
    return cleantext.strip()

def normalize_url(url):
    """프로토콜 상대 URL을 HTTPS URL로 정규화"""
    if not url:
        return ''
    return f"https:{url}" if url.startswith('//') else url

def get_thumbnail(entry):
    """RSS 엔트리에서 썸네일 이미지 URL 추출"""
    # media:thumbnail 태그 확인
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        thumbnail = entry.media_thumbnail[0]
        if thumbnail.get('url'):
            return normalize_url(thumbnail['url'])

    # media:content 태그 확인
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('url'):
                return normalize_url(media['url'])

    # enclosure 태그 확인
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image/') and enclosure.get('url'):
                return normalize_url(enclosure['url'])

    # description/content에서 이미지 추출
    content = entry.get('description', '') or entry.get('summary', '')
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if img_match:
        return normalize_url(img_match.group(1))

    return DEFAULT_THUMBNAIL

def format_date(date_str):
    """날짜 포맷팅"""
    if not date_str:
        return ''
    try:
        date_obj = parsedate_to_datetime(date_str)
        return date_obj.strftime('%Y.%m.%d')
    except (TypeError, ValueError):
        return date_str

def create_blog_table(feed_url, max_posts=6):
    """RSS 피드에서 블로그 글을 가져와 3x2 테이블 생성"""
    feed = feedparser.parse(feed_url)
    entries = feed.entries[:max_posts]

    # 테이블 생성 (왼쪽 정렬)
    table = "| | | |\n"
    table += "|---|---|---|\n"

    # 2행 3열로 구성
    for i in range(0, len(entries), 3):
        row_entries = entries[i:i+3]
        row = "|"

        for entry in row_entries:
            # 썸네일
            thumbnail = get_thumbnail(entry)
            # 제목
            title = entry.title
            # 링크
            link = entry.link
            # 내용 미리보기 (50자 제한)
            description = clean_html(entry.get('description', ''))[:50] + '...'
            # 날짜
            pub_date = format_date(entry.get('published', ''))

            # 셀 내용 구성 (이미지 크기 고정: 300x200)
            cell = f'<a href="{link}"><img src="{thumbnail}" width="300" height="200" alt="{title}"></a><br/>**[{title}]({link})**<br/>{description}<br/>{pub_date}'
            row += f" {cell} |"

        # 3개 미만인 경우 빈 셀 추가
        while len(row_entries) < 3:
            row += " |"
            row_entries.append(None)

        table += row + "\n"

    return table

def update_readme(readme_path, table_content):
    """README.md 파일 업데이트"""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 마커 사이의 내용 교체
    start_marker = "<!-- BLOG-POST-LIST:START -->"
    end_marker = "<!-- BLOG-POST-LIST:END -->"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        new_content = (
            content[:start_idx + len(start_marker)] +
            "\n" + table_content + "\n" +
            content[end_idx:]
        )

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ README.md updated successfully!")
    else:
        print("❌ Could not find markers in README.md")

if __name__ == "__main__":
    RSS_FEED_URL = os.environ.get("RSS_FEED_URL", "https://blog.rlarbdlf222.workers.dev/rss.xml")
    README_PATH = "README.md"

    print("📡 Fetching blog posts from RSS feed...")
    table = create_blog_table(RSS_FEED_URL, max_posts=6)

    print("📝 Updating README.md...")
    update_readme(README_PATH, table)
