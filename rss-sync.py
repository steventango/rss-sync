import argparse
import os
import urllib.parse
import urllib.request
from datetime import datetime

import lxml.etree as ET


def rss_sync(url):
    path = urllib.parse.urlparse(url).path
    basename = os.path.basename(path)
    if not basename.endswith('.rss'):
        basename += '.rss'

    request = urllib.request.urlopen(url)
    data = request.read()

    parser = ET.XMLParser(encoding='utf-8', strip_cdata=False)
    patch = ET.fromstring(data, parser)
    try:
        tree = ET.parse(basename, parser)
        root = tree.getroot()
    except FileNotFoundError:
        with open(basename, 'w') as f:
            f.write(data)
            return

    root.find('./channel/lastBuildDate').text = patch.find('./channel/lastBuildDate').text

    latest_item = root.find('./channel/item')
    latest_pubDate = datetime.strptime(latest_item.find('./pubDate').text, '%a, %d %b %Y %H:%M:%S %z')
    modified = False
    for item in patch.findall('./channel/item'):
        pubDate = datetime.strptime(item.find('./pubDate').text, '%a, %d %b %Y %H:%M:%S %z')
        if latest_pubDate >= pubDate:
            break
        latest_item.addprevious(item)
        modified = True
    if modified:
        tree.write(basename, xml_declaration=True, encoding='UTF-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='RSS feed URL')
    args = parser.parse_args()
    rss_sync(args.url)


if __name__ == '__main__':
    main()
