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

My process for using these tools looks like this:

1. My MacBook is connected to my host machine with a USB3 cable
2. Start `./m1n1/proxyclient/tools/picocom-sec.sh` 
3. Boot with m1n1's proxy mode enabled
4. Run experiments
5. When you're done, run `./m1n1/proxyclient/tools/reboot.py`, yank the 
   USB3 cable, and let m1n1 boot into Asahi Linux


## Bare-metal Rust programs

`m2e-rs` is a Rust crate that defines a simple runtime environment for
executables on top of m1n1 
(see [m2e-rs/src/bin/template.rs](./m2e-rs/src/bin/template.rs)).
You probably need to install Rust nightly for this. Since my host machine is
x86, I also needed to install the `aarch64-unknown-none-gnu` target in order 
to build this. I'm using [run-elf.py](./run-elf.py) to load and run the 
resulting binaries.

## Microbenchmarking in m1n1

[pym2e/](./pym2e/) has some infrastructure for assembling/running/loading
small pieces of code. See the following:

- [pht.py](./pht.py) - local branch predictor experiments


