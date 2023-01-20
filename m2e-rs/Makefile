.PHONY: all clean
all:
	cargo build --release
dis:
	aarch64-linux-gnu-objdump -d -C target/t8112/release/test
clean:
	cargo clean
