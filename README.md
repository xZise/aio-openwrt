# OpenWRT ubus API

A Python library for asynchronous access to the `ubus` interface on OpenWRT devices.

## Requirements

* Python 3.10+
* `aiohttp`

## Quick Start
```python
from aio_openwrt import Ubus

async with Ubus("192.168.1.1", "username", "password") as client:
    await client.login()
    dev = await client.network.device.status(name="lan1")
    print(dev)
```

## Usage

### Connection livetime
Use `async with` to automatically manage the session:

```python
async with Ubus(host, user, password) as client:
    await client.login()
    dev = await client.network.device.status(name="lan1")
```

Without a `with` block, a session is created automatically on the first request. In that case, call `close()` manually when done:


```python
client = Ubus(host, user, password)
try:
    await client.login()
    dev = await client.network.device.status(name="lan1")
finally:
    await client.close()
```

### Making Calls
There are two ways to interact with the device:

**Typed wrappers** — available for common paths and methods:
```python
await ubus.session.login(username="...", password="...")
await ubus.network.device.status(name="lan1")
await ubus.system.board()
```

**Direct `call()`** — for any path/method not covered by a typed wrapper:
```python
await ubus.call("session", "login", {"username": "...", "password": "..."})
await ubus.call("network.device", "status", {"name": "lan1"})
await ubus.call("system", "board")
```

Both are equivalent. The typed wrappers are a convenience layer over `call()`.

**Subscript Access**
For dynamically named entries such as network interfaces, use subscript notation:
```python
await ubus.network.interface["wan"].status()
```

### Listing objects
To list the objects directly use `list()`:
```python
await ubus.list("hostapd.*")
```

Typed wrappers with subscript access can be iterated over using `list_children()`:
```python
await ubus.hostapd.list_children()
```

## Permissions
Depending on the device configuration, most features require authentication first. The authenticated user must be configured in `/etc/config/rpcd` with a corresponding ACL file in `/usr/share/rpcd/acl.d/` granting the necessary `ubus` permissions. See the [OpenWRT wiki](https://openwrt.org/docs/techref/ubus) for details.

## Development

Install dependencies:
```sh
pip install -e ".[dev]"
pre-commit install
```

This will check and format using [ruff](https://docs.astral.sh/ruff/) the code before committing.