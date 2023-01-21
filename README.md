# m2e

Playground for experimenting with microbenchmarks on Apple Silicon 
(specifically the T8112 - I'm using this on my 2022 13" MacBook Pro).

## Setup and Usage

These experiments rely on [AsahiLinux/m1n1](https://github.com/AsahiLinux/m1n1)
proxy/hypervisor functionality for interacting with the hardware. Refer to the 
[Asahi Linux documentation](https://github.com/AsahiLinux/docs/wiki) for 
details on setting up m1n1 and the proxy client.

You need to recursively clone this repository because we rely on the Python
modules defined in `m1n1/proxyclient`:

```
$ git clone --recursive https://github.com/eigenform/m2e
```

`m2e-rs` is a Rust crate that defines a simple runtime environment for
executables on top of m1n1 
(see [m2e-rs/src/bin/template.rs](./m2e-rs/src/bin/template.rs)).
You probably need to install Rust nightly and the `aarch64-unknown-none-gnu` 
target in order to build this. 

After booting into m1n1's proxy mode and connecting to the target device with
USB, you can use [run-elf.py](./run-elf.py) to run an ELF binary. 


