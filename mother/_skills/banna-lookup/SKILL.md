---
name: banna-lookup
description: Use when any code needs a TCP port number, IP address, or other network identifier for a BISOS service. `bisos.banna` is the authoritative registry — never hardcode port numbers that banna already tracks.
---

# Using `bisos.banna` for Port Numbers and IP Addresses

`bisos.banna` is the BISOS Assign Name/Number Authority. It is the single
authoritative source for TCP port numbers, Unix socket paths, and other
network identifiers assigned to BISOS services. Whenever a port number is
needed, look it up from banna rather than hardcoding it.

## TCP Port Numbers

Port assignments live in `bisos.banna.tcpPorts`:

```python
from bisos.banna import tcpPorts as bannaTcpPorts

portNu = bannaTcpPorts.tcpPortsAssignedList.tcpPortsList['airflow'].portNu
```

The key is the service name (a string matching `TcpPortNuInfo.portName`).
The `.portNu` attribute is an `int`.

Source file: `/bisos/git/auth/bxRepos/bisos-pip/banna/py3/bisos/banna/tcpPorts.py`

## IP Address from `/etc/hosts`

For services registered in `/etc/hosts`, resolve the IP with the standard
library — no banna API needed:

```python
import socket

ip = socket.gethostbyname('airflow.here')  # → '127.0.22.100'
```

`/etc/hosts` entries for BISOS services follow the convention:
```
127.0.22.100  airflow.here  # port=24006
```

The `# port=NNN` comment is informational; the authoritative port is in banna.

## Combined Pattern (used in `.pcs` config generators)

```python
import socket
from bisos.banna import tcpPorts as bannaTcpPorts

_serverName = "airflow.here"
_proxyPort = bannaTcpPorts.tcpPortsAssignedList.tcpPortsList['airflow'].portNu
_proxyIp = socket.gethostbyname(_serverName)
```

## What banna Covers

- `bisos.banna.tcpPorts` — TCP port number assignments
- `bisos.banna.unixSockets` — Unix socket path assignments
- `bisos.banna.bannaPortNu` — legacy module still used by older packages

When adding a new service port, add it to `tcpPorts.py` in the banna repo
before using it anywhere else.