#!/usr/bin/env python3
from argparse import ArgumentParser
from typing import Any
import json
import re
import urllib.parse

import requests
import websocket

TITLE_REGEX = re.compile(r'<title>([^<>]+)</title>')


def main() -> None:
    entrypoint = ArgumentParser()
    entrypoint.add_argument('-t', '--target', metavar='HOST:PORT', default='127.0.0.1:9222')
    parsers = entrypoint.add_subparsers(dest='action', required=True)
    parsers.add_parser('list-tabs')
    parsers.add_parser('list-extensions')
    parsers.add_parser('dump-cookies')
    parser = parsers.add_parser('open-tab')
    parser.add_argument('url', nargs='?')
    parser = parsers.add_parser('close-tab')
    parser.add_argument('id', nargs=None)
    opts = entrypoint.parse_args()

    if opts.action == 'list-tabs':
        print(json.dumps(list_tabs(opts.target), indent=2))
    elif opts.action == 'list-extensions':
        print(json.dumps(list_extensions(opts.target), indent=2))
    elif opts.action == 'dump-cookies':
        print(json.dumps(dump_cookies(opts.target), indent=2))
    elif opts.action == 'open-tab':
        print(json.dumps(open_tab(opts.target, opts.url), indent=2))
    elif opts.action == 'close-tab':
        close_tab(opts.target, opts.id)
    else:
        raise RuntimeError('unreachable')


def list_tabs(target: str) -> list[dict[str, Any]]:
    response = requests.get(f'http://{target}/json')
    response.raise_for_status()
    data = response.json()
    return [page for page in data if page['type'] == 'page' and not page['url'].startswith('chrome://extensions/')]


def list_extensions(target: str) -> list[dict[str, Any]]:
    response = requests.get(f'http://{target}/json')
    response.raise_for_status()
    data = response.json()
    extensions = [page for page in data if page['url'].startswith('chrome://extensions/') and page['url'] != 'chrome://extensions/']
    results = []
    for extension in extensions:
        extension_url = urllib.parse.urlparse(extension['url'])
        query_params = urllib.parse.parse_qs(extension_url.query)
        extension['extensionId'] = query_params['id'][0]
        extension['extensionStoreUrl'] = f'https://chromewebstore.google.com/detail/{extension['extensionId']}'
        response = requests.get(extension['extensionStoreUrl'])
        response.raise_for_status()
        match = TITLE_REGEX.search(response.text)
        if match:
            extension['extensionName'] = match.group(1)
        results.append(extension)
    return results


def dump_cookies(target: str) -> list[dict[str, Any]]:
    ws = websocket.WebSocket()
    ws.connect(get_debugger_url(target), suppress_origin=True)
    request = json.dumps(dict(id=1, method='Storage.getCookies'))  # successor of deprecated 'Network.getAllCookies'
    ws.send(request)
    data = json.loads(ws.recv())
    return data['result']['cookies']


def open_tab(target: str, url: str|None) -> dict[str, Any]:
    response = requests.put(f'http://{target}/json/new?{url}' if url else f'http://{target}/json/new')
    response.raise_for_status()
    return response.json()


def close_tab(target: str, id: str) -> None:
    response = requests.get(f'http://{target}/json/close/{id}')
    response.raise_for_status()


def get_debugger_url(target: str) -> str:
    response = requests.get(f'http://{target}/json/version')
    response.raise_for_status()
    data = response.json()
    return data['webSocketDebuggerUrl']


if __name__ == '__main__':
    main()
