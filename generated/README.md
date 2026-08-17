# Generated code

Run the codegen (see `README.md` → "Building from source") after supplying your
legally obtained `.xex`. The files in this folder are **derived from the
copyrighted game executable** and are intentionally **excluded from version
control** — never commit them.

To regenerate:

```
cmake --build out/build/win-amd64-release --target dbz1_codegen
```

This produces `dbz1_init.*`, `dbz1_recomp.*`, `dbz1_register.cpp`,
`dbz1_register.h`, `sources.cmake`, etc. from `assets/default.xex` +
`dbz1_config.toml` + `dbz1_manifest.toml`.
