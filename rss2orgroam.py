import os
from datetime import datetime
import feedparser
from markdownify import markdownify as md
from dotenv import load_dotenv
from openai import OpenAI

# ==== Load Environment Variables ====
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Make sure .env file contains OPENAI_API_KEY=...")

client = OpenAI(api_key=OPENAI_API_KEY)

# ==== CONFIGURATION ====

ORG_ROAM_DIR = os.path.expanduser("~/Dropbox/ORG/RESOURCES/rss_summaries/")
os.makedirs(ORG_ROAM_DIR, exist_ok=True)

TAGS = ":rss:research:hydro:modelling:"

# Structure: (Section Name, [Feed URLs])
RSS_FEEDS = [
    ("Academic Journals", [
        "https://link.springer.com/search.rss?facet-journal-id=10040",
        "https://ngwa.onlinelibrary.wiley.com/feed/17456584/most-recent",
        "https://agupubs.onlinelibrary.wiley.com/rss/journal/19447973",
    ]),
    ("Preprints / Open Science", [
        "https://arxiv.org/rss/physics.geo-ph",
        "https://arxiv.org/rss/cs.CE",
    ]),
    ("Tools and Packages", [
        "https://github.com/modflowpy/flopy/releases.atom",
        "https://github.com/usgs/pestpp/releases.atom",
        "https://github.com/pypest/pyemu/releases.atom",
    ]),
]

def summarize_entry(title, summary, link):
    prompt = f"""You are summarizing scientific or technical articles for a groundwater modeller.

Title: {title}

Abstract or content:
{summary}

Generate:
- Three concise bullet points with key takeaways
- One sentence on "Why this matters" to hydrogeology, groundwater modelling, or uncertainty analysis.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-rss-summaries.org"
    filepath = os.path.join(ORG_ROAM_DIR, filename)

    org_content = [
        f"#+TITLE: RSS Summaries {date_str}",
        f"#+DATE: {date_str}",
        f"#+FILETAGS: {TAGS}",
        "",
    ]

    seen_slugs = set()

    for section, feeds in RSS_FEEDS:
        org_content.append(f"* {section}")
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            feed_title = feed.feed.get("title", feed_url)
            org_content.append(f"** Feed: {feed_title}")

            for entry in feed.entries[:3]:
                title = entry.get("title", "No Title")
                link = entry.get("link", "")
                summary_raw = entry.get("summary", "")

                slug = title.lower().replace(" ", "-").replace("/", "-")[:50]
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)

                try:
                    print(f"🧠 Summarizing: {title}")
                    summary = summarize_entry(title, md(summary_raw), link)
                    org_content.append(f"*** {title}")
                    org_content.append(f"[[{link}][Link to original article]]")
                    org_content.append("")
                    org_content.append(f"Summary from feed: *{feed_title}*")
                    org_content.append("")
                    org_content.append(summary)
                    org_content.append("")
                except Exception as e:
                    print(f"❌ Error summarizing {title}: {e}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(org_content))
    print(f"✅ Saved: {filepath}")

if __name__ == "__main__":
    main()
