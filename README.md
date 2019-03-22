# Pyrez: Easily way to connect to Hi-Rez API
[![License](https://img.shields.io/github/license/luissilva1044894/Pyrez.svg?style=plastic&logoWidth=10)](./LICENSE)
[![Runtime Version](https://img.shields.io/pypi/pyversions/pyrez.svg?style=plastic&logo=python&logoWidth=10)](https://pypi.org/project/pyrez)
[![Contributors](https://img.shields.io/github/contributors/luissilva1044894/Pyrez.svg?style=plastic&logo=github&logoWidth=10)](https://github.com/luissilva1044894/Pyrez/graphs/contributors)
[![Discord Server](https://img.shields.io/discord/549020573846470659.svg?style=plastic&logo=discord&logoWidth=10)](https://discord.gg/XkydRPS)


**PyRez** is an open-source Python-based wrapper for [Hi-Rez](http://www.hirezstudios.com "Hi-Rez Studios") API that supports *[Paladins](https://www.paladins.com "Paladins Game")*, *[Realm Royale](https://www.realmroyale.com "Realm Royale Game")* and *[Smite](https://www.smitegame.com "Smite Game")*.

### Documentation
Official Documentation: [**Click here!**](./docs)

### Support
For support using Pyrez, please join the official [*support server*](
https://discord.gg/XkydRPS) on [Discord](https://discordapp.com/ "Discord App")

### Requirements
* [Python](http://python.org "Python.org") 3.x(3.4 or higher).
    * The following libraries are required: [`aiohttp`](https://pypi.org/project/aiohttp/ "Async http client/server framework") and [`async_timeout`](https://pypi.org/project/async_timeout/).
- [Access](./docs#registration "Form access to Hi-Rez API") to Hi-Rez Studios API.

### Installation
Pyrez currently isn't being updated on [PyPI](https://pypi.org/project/pyrez) and thus needs to be installed using git. The easiest way to install **Pyrez** is using `pip`, Python's package manager:

```
pip install -e git+https://github.com/luissilva1044894/pyrez.git@async#egg=Pyrez
```
The required dependencies will be installed automatically.
After that, you can use the library using:
```py
import pyrez
```

### Contributors
- [@shaklev](https://github.com/shaklev)
- [@Rabrg](https://github.com/Rabrg)
- [@EthanHicks1](https://github.com/EthanHicks1)

### License
This project is licensed under [MIT](./LICENSE)