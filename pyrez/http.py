from sys import version_info as pythonVersion

import aiohttp

class HttpRequest():
    defaultHeaders = { "User-Agent": "HttpRequestWrapper [Python/{0.major}.{0.minor} aiohttp/{1}]".format(pythonVersion, aiohttp.__version__) }
    timeout = 500

    def __init__(self, loop=None, headers=defaultHeaders):
        self.headers=defaultHeaders if headers is None else headers

    async def get(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await self.request('GET', url=url.replace(' ', '%20'), params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allowRedirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
    async def request(self, method, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
            async with session.request(method, url, params=params, data=data) as resp:
                return await resp
                #request(method, url, *, params=None, data=None, json=None, headers=None, skip_auto_headers=None, auth=None, allow_redirects=True, max_redirects=10, compress=None, chunked=None, expect100=False, read_until_eof=True, proxy=None, proxy_auth=None, timeout=5*60, verify_ssl=None, fingerprint=None, ssl_context=None, proxy_headers=None
