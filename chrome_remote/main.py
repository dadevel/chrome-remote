#!/usr/bin/env python3
from argparse import ArgumentParser
from typing import Any
import json

import requests
import websocket


def main() -> None:
    entrypoint = ArgumentParser()
    entrypoint.add_argument('-t', '--target', metavar='HOST:PORT', default='127.0.0.1:9222')
    parsers = entrypoint.add_subparsers(dest='action', required=True)
    parsers.add_parser('list-tabs')
    parsers.add_parser('dump-cookies')
    opts = entrypoint.parse_args()

    if opts.action == 'list-tabs':
        print(json.dumps(list_tabs(opts.target), indent=2))
    elif opts.action == 'dump-cookies':
        print(json.dumps(dump_cookies(opts.target), indent=2))
    else:
        raise RuntimeError('unreachable')


def list_tabs(target: str) -> list[dict[str, Any]]:
    response = requests.get(f'http://{target}/json')
    response.raise_for_status()
    data = response.json()
    return [{k: v for k, v in page.items() if k in ('title', 'url')} for page in data if page['type'] == 'page']


def dump_cookies(target: str) -> list[dict[str, Any]]:
    ws = websocket.WebSocket()
    ws.connect(get_debugger_url(target), suppress_origin=True)
    request = json.dumps(dict(id=1, method='Storage.getCookies'))  # successor of deprecated 'Network.getAllCookies'
    ws.send(request)
    data = json.loads(ws.recv())
    return data['result']['cookies']


def get_debugger_url(target: str) -> str:
    response = requests.get(f'http://{target}/json/version')
    response.raise_for_status()
    data = response.json()
    return data['webSocketDebuggerUrl']


if __name__ == '__main__':
    main()
