# m2e

Playground for experimenting with microbenchmarks on Apple Silicon 
(specifically the T8112 - I'm using this on my 2022 13" MacBook Pro).

**NOTE:** I can't guarantee this is safe or particularly easy-to-use. 
You should avoid using this if you don't know what you're doing. 

## Setup and Usage

These experiments rely on [AsahiLinux/m1n1](https://github.com/AsahiLinux/m1n1)
proxy/hypervisor functionality for interacting with the hardware. Refer to the 
[Asahi Linux documentation](https://github.com/AsahiLinux/docs/wiki) for 
details on setting up m1n1 and the proxy client.

You need to recursively clone this repository because `m1n1` is included as 
a submodule, and we rely on the Python modules defined in `m1n1/proxyclient`.

```
$ git clone --recursive https://github.com/eigenform/m2e
```

**NOTE:** My machine is using the version of `m1n1` tracked in this repository.
This is probably *unsafe* for machines which may have a different version of
`m1n1` installed.

In general, my process for using these tools looks like this:

1. My MacBook is connected to my host machine with a USB3 cable
2. Start `./m1n1/proxyclient/tools/picocom-sec.sh` on the host
3. Boot with m1n1's proxy mode enabled
4. Run some experiments
5. When you're done, run `./m1n1/proxyclient/tools/reboot.py`, yank the 
   USB3 cable, let m1n1 boot into Asahi Linux, and then power-off the 
   machine

The scripts in this repository depend on [pym2e/](./pym2e/), which has some 
utilities for initializing the machine and assembling/running/loading small 
pieces of code with the proxy client.

## Experiments

...


