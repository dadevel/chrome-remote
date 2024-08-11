#!/usr/bin/env python3
from __future__ import annotations
from argparse import ArgumentParser, FileType
from typing import Any
import json
import re
import sys
import urllib.parse

import requests
import websocket

TITLE_REGEX = re.compile(r'<title>([^<>]+)</title>')
DEBUG = False


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

    parser = parsers.add_parser('eval')
    parser.add_argument('url', nargs=None)
    parser.add_argument('js', type=FileType('r'), nargs=None)

    parser = parsers.add_parser('curl')
    parser.add_argument('url', nargs=None)
    parser.add_argument('-X', dest='method', default='GET')
    parser.add_argument('-d', dest='body', default=None)

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
    elif opts.action == 'eval':
        print(json.dumps(eval_js(opts.target, opts.url, opts.js.read()), indent=2))
    elif opts.action == 'curl':
        print(js_curl(opts.target, opts.url, opts.method, opts.body))
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
    debugger = ChromeDebugger.connect(target)
    response = debugger.send(dict(method='Storage.getCookies'))
    return response['result']['cookies']


def open_tab(target: str, url: str|None) -> dict[str, Any]:
    response = requests.put(f'http://{target}/json/new?{url}' if url else f'http://{target}/json/new')
    response.raise_for_status()
    return response.json()


def close_tab(target: str, id: str) -> None:
    response = requests.get(f'http://{target}/json/close/{id}')
    response.raise_for_status()


def eval_js(target: str, url: str, code: str) -> Any:
    debugger = ChromeDebugger.connect(target)
    response = debugger.send(dict(method='Target.getTargets'))
    target_id = None
    for target_info in response['result']['targetInfos']:
        if target_info['type'] == 'page':
            target_id = target_info['targetId']
    assert target_id
    response = debugger.send(dict(method='Target.attachToTarget', params=dict(targetId=target_id, flatten=True)))
    session_id = response['result']['sessionId']
    response = debugger.send(dict(sessionId=session_id, id=1, method='Page.enable'))
    response = debugger.send(dict(sessionId=session_id, method='Page.navigate', params=dict(url=url)))
    response = debugger.send(dict(sessionId=session_id, method='Runtime.enable'))
    response = debugger.send(dict(sessionId=session_id, method='Runtime.evaluate', params=dict(expression=code)))
    return response['result']['result']['value']


JS_WITHOUT_BODY = """
var req = new XMLHttpRequest();
req.open("{METHOD}", "{PATH}", false);
req.send(null);
req.responseText
"""
JS_WITH_BODY = """
var req = new XMLHttpRequest();
req.open("POST", "{PATH}", false);
req.send("{BODY}");
req.responseText
"""

# based on https://github.com/zimnyaa/remotechrome/blob/a231d5f6694d56bea537288eea17337a1ebce153/remotechrome_curl.py
def js_curl(target: str, url: str, method: str, body: str|None) -> str:
    assert '"' not in url
    assert '"' not in method
    assert not body or '"' not in body
    if body:
        template = JS_WITH_BODY
    else:
        template = JS_WITHOUT_BODY
    request_url = urllib.parse.urlparse(url)
    code = template.format(METHOD=method, PATH=f'{request_url.path}?{request_url.query}' if request_url.query else request_url.path, BODY=body)
    return eval_js(target, f'{request_url.scheme}://{request_url.netloc}', code)


class ChromeDebuggerError(Exception):
    pass


class ChromeDebugger:
    def __init__(self, ws: websocket.WebSocket) -> None:
        self.ws = ws
        self.message_counter = 0

    @staticmethod
    def get_debugger_url(target: str) -> str:
        response = requests.get(f'http://{target}/json/version')
        response.raise_for_status()
        data = response.json()#
        return data['webSocketDebuggerUrl']

    @classmethod
    def connect(cls, target: str) -> ChromeDebugger:
        ws = websocket.WebSocket()
        ws.connect(cls.get_debugger_url(target), suppress_origin=True)
        return cls(ws)

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        self.message_counter += 1
        request.update(id=self.message_counter)
        if DEBUG:
            print(json.dumps(dict(tx=request)), file=sys.stderr)
        self.ws.send(json.dumps(request))
        while True:
            response = json.loads(self.ws.recv())
            if DEBUG:
                print(json.dumps(dict(rx=response)), file=sys.stderr)
            if response.get('id') == request['id']:
                if response.get('error'):
                    raise ChromeDebuggerError(response['error']['message'])
                return response


if __name__ == '__main__':
    main()
