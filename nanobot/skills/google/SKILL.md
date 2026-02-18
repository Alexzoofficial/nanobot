# Google Browser Skill 🌐

This skill allows nanobot to act like a web browser. It uses `web_search` and `web_fetch` to navigate the web, search for information, and read content.

## Capabilities

- **Search**: Find information using the Google-powered Alexzo Search API.
- **Browse**: Fetch and read the content of any web page.
- **Deep Research**: Combined search and fetch to answer complex questions.

## Usage

Simply ask nanobot to:
- "Search for the latest news on AI"
- "Read the content of https://example.com"
- "Who is the CEO of Tesla?"

## How it works

1. nanobot uses the `web_search` tool to get a list of relevant URLs.
2. It then uses the `web_fetch` tool to read the most promising pages.
3. Finally, it summarizes the information for you.
