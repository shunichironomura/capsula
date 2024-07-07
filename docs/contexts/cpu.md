# `CpuContext`

The [`CpuContext`](../reference/capsula/index.md#capsula.CpuContext) captures the CPU information.
It can be created by `capsula.CpuContext()` with no arguments.

It internally uses the [`py-cpuinfo`](https://github.com/workhorsy/py-cpuinfo) package to get the CPU information.

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "CpuContext" },
]
```

### Via `@capsula.context` decorator

```python
import capsula

@capsula.run()
@capsula.context(capsula.CpuContext(), mode="pre")
def func(): ...
```

## Output example

The following is an example of the output of the `CpuContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"cpu": {
  "python_version": "3.8.17.final.0 (64 bit)",
  "cpuinfo_version": [
    9,
    0,
    0
  ],
  "cpuinfo_version_string": "9.0.0",
  "arch": "X86_64",
  "bits": 64,
  "count": 12,
  "arch_string_raw": "x86_64",
  "vendor_id_raw": "GenuineIntel",
  "brand_raw": "Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz",
  "hz_advertised_friendly": "2.9000 GHz",
  "hz_actual_friendly": "2.9040 GHz",
  "hz_advertised": [
    2900000000,
    0
  ],
  "hz_actual": [
    2904008000,
    0
  ],
  "stepping": 5,
  "model": 165,
  "family": 6,
  "flags": [
    "3dnowprefetch",
    "abm",
    "adx",
    "aes",
    "apic",
    "arch_capabilities",
    "arch_perfmon",
    "avx",
    "avx2",
    "bmi1",
    "bmi2",
    "clflush",
    "clflushopt",
    "cmov",
    "constant_tsc",
    "cpuid",
    "cx16",
    "cx8",
    "de",
    "ept",
    "ept_ad",
    "erms",
    "f16c",
    "flush_l1d",
    "fma",
    "fpu",
    "fsgsbase",
    "fxsr",
    "ht",
    "hypervisor",
    "ibpb",
    "ibrs",
    "ibrs_enhanced",
    "invpcid",
    "invpcid_single",
    "lahf_lm",
    "lm",
    "mca",
    "mce",
    "md_clear",
    "mmx",
    "movbe",
    "msr",
    "mtrr",
    "nopl",
    "nx",
    "osxsave",
    "pae",
    "pat",
    "pcid",
    "pclmulqdq",
    "pdcm",
    "pdpe1gb",
    "pge",
    "pni",
    "popcnt",
    "pse",
    "pse36",
    "rdrand",
    "rdrnd",
    "rdseed",
    "rdtscp",
    "rep_good",
    "sep",
    "smap",
    "smep",
    "ss",
    "ssbd",
    "sse",
    "sse2",
    "sse4_1",
    "sse4_2",
    "ssse3",
    "stibp",
    "syscall",
    "tpr_shadow",
    "tsc",
    "vme",
    "vmx",
    "vnmi",
    "vpid",
    "x2apic",
    "xgetbv1",
    "xsave",
    "xsavec",
    "xsaveopt",
    "xsaves",
    "xtopology"
  ],
  "l3_cache_size": 12582912,
  "l2_cache_size": "1.5 MiB",
  "l1_data_cache_size": 196608,
  "l1_instruction_cache_size": 196608,
  "l2_cache_line_size": 256,
  "l2_cache_associativity": 6
}
```
