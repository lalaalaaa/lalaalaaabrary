import requests
from bs4 import BeautifulSoup
import csv

# Load URLs from file
with open('urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip()]

def clean_text(text):
    if not text:
        return ''
    # Replace problematic unicode with safe equivalents
    text = text.replace('\u2019', "'")   # Right single quote
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # Double quotes
    text = text.replace('\u2014', '—')   # Em dash
    text = text.replace('\u2026', '...') # Ellipsis
    text = text.replace('\u2028', ' ')   # Line separator
    return text.strip()

def get_all_metadata(url):
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'  # Force UTF-8 decoding
        soup = BeautifulSoup(response.text, 'html.parser')

        metadata = {'url': url}

        # Page title
        title = soup.title.string if soup.title else 'No title'
        metadata['title'] = clean_text(title)

        # Meta description and keywords
        description = soup.find('meta', attrs={'name': 'description'})
        keywords = soup.find('meta', attrs={'name': 'keywords'})

        metadata['meta_description'] = clean_text(description['content']) if description and description.get('content') else 'No description'
        metadata['meta_keywords'] = clean_text(keywords['content']) if keywords and keywords.get('content') else 'No keywords'

        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        metadata['canonical_url'] = clean_text(canonical['href']) if canonical and canonical.get('href') else 'No canonical URL'

        # Grab all other meta tags with name or property
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            key = tag.get('name') or tag.get('property')
            value = tag.get('content')
            if key and value:
                key_clean = clean_text(key.lower())
                value_clean = clean_text(value)
                if key_clean not in metadata:
                    metadata[key_clean] = value_clean

        return metadata

    except Exception as e:
        return {'url': url, 'error': str(e)}

# Scrape all URLs
results = [get_all_metadata(url) for url in urls]

# Build CSV headers
all_keys = set()
for result in results:
    all_keys.update(result.keys())

fieldnames = ['url', 'title', 'meta_description', 'meta_keywords', 'canonical_url'] + sorted(k for k in all_keys if k not in {'url', 'title', 'meta_description', 'meta_keywords', 'canonical_url'})

# Write to CSV
with open('full_metadata_results.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)

print("Done. Metadata saved to full_metadata_results.csv")