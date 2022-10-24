import argparse
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime

import lxml.etree as ET


def rss_sync(url, max_retries):
    path = urllib.parse.urlparse(url).path
    basename = os.path.basename(path)
    if not basename.endswith('.rss'):
        basename += '.rss'

    retries = 0
    while retries < max_retries:
        try:
            request = urllib.request.urlopen(url)
            data = request.read()
            break
        except urllib.error.URLError:
            retries += 1
            time.sleep(2 ** retries)
            return

    parser = ET.XMLParser(encoding='utf-8', strip_cdata=False)
    patch = ET.fromstring(data, parser)
    try:
        tree = ET.parse(basename, parser)
        root = tree.getroot()
    except FileNotFoundError:
        with open(basename, 'w') as f:
            f.write(data)
            return

    root.find('./channel/lastBuildDate').text = patch.find(
        './channel/lastBuildDate'
    ).text

    latest_item = root.find('./channel/item')
    latest_pubDate = datetime.strptime(
        latest_item.find('./pubDate').text, '%a, %d %b %Y %H:%M:%S %z'
    )
    modified = False
    for item in patch.findall('./channel/item'):
        pubDate = datetime.strptime(
            item.find('./pubDate').text, '%a, %d %b %Y %H:%M:%S %z'
        )
        if latest_pubDate >= pubDate:
            break
        latest_item.addprevious(item)
        modified = True
    if modified:
        tree.write(basename, xml_declaration=True, encoding='UTF-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='RSS feed URL')
    parser.add_argument(
        '--max_retries', type=int, help='Maximum number of retries', default=11
        )
    args = parser.parse_args()
    rss_sync(args.url, args.max_retries)


if __name__ == '__main__':
    main()
