from sys import version_info as pythonVersion

import requests_async as requests

class HttpRequest():
    defaultHeaders = { "User-Agent": "HttpRequestWrapper [Python/{0.major}.{0.minor} requests/{1}]".format(pythonVersion, requests.__version__) }
    timeout = 500

    def __init__(self, headers=defaultHeaders):
        self.headers=defaultHeaders if headers is None else headers

    async def get(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        response = asyncio.get_event_loop().run_until_complete(requests.get(url.replace(' ', '%20'), params=params, data=data, headers=headers))#, cookies=cookies, files=files, auth=auth, timeout=timeout, allowRedirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
        return await response
    async def request(self, method, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await requests.request(method=method, url=url, params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allow_redirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
    async def post(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await requests.post(url=url.replace(' ', '%20'), params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allow_redirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
    async def put(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await requests.put(url=url.replace(' ', '%20'), params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allow_redirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
    async def delete(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await requests.delete(url=url.replace(' ', '%20'), params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allow_redirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
    async def head(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await requests.head(url=url.replace(' ', '%20'), params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allow_redirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
    async def options(self, url, params=None, data=None, headers=defaultHeaders, cookies=None, files=None, auth=None, timeout=None, allowRedirects=False, proxies=None, hooks=None, stream=False, verify=None, cert=None):
        return await requests.options(url=url.replace(' ', '%20'), params=params, data=data, headers=headers, cookies=cookies, files=files, auth=auth, timeout=timeout, allow_redirects=allowRedirects, proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert)
