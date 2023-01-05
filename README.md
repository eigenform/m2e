# m2e

Playground for experimenting with microbenchmarks on Apple Silicon 
(specifically the T8112 - I'm using this on my 2022 13" MacBook Pro).

These experiments rely on [AsahiLinux/m1n1](https://github.com/AsahiLinux/m1n1)
proxy/hypervisor functionality for interacting with the hardware. Refer to the 
[Asahi Linux documentation](https://github.com/AsahiLinux/docs/wiki) for 
details on setting up m1n1.

## Setup

You need to recursively clone this repository because we rely on the Python
modules defined in `m1n1/proxyclient`:

```
$ git clone --recursive https://github.com/eigenform/m2e
```

