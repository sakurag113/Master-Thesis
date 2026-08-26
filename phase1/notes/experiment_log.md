# Phase 1 Experiment Log

## Project
**Title:** eBPF-driven Fine-grained Telemetry and Machine Learning for EVPN/VXLAN Datacenter Networks

## Phase 1 Goal
The goal of Phase 1 is to build a minimal software-based experimental environment, reproduce contention-related latency increase, and collect a first proof-of-concept dataset for later analysis.

---

# Experiment 001: Minimal Testbed Setup and Connectivity Verification

## Date
2026-05-17

## Objective
To create a minimal Linux namespace-based network topology and verify that the environment can support later traffic generation and latency measurements.

## Topology
A minimal topology was built using Linux network namespaces:

- `s1`: sender 1
- `s2`: sender 2
- `sw`: intermediate forwarding node
- `r1`: receiver

Logical topology:

`s1, s2 -> sw -> r1`

## Network Configuration
IP addresses were configured as follows:

- `s1`: `10.0.1.1/24`
- `s2`: `10.0.2.1/24`
- `r1`: `10.0.3.1/24`
- `sw`:
  - `10.0.1.254/24`
  - `10.0.2.254/24`
  - `10.0.3.254/24`

IP forwarding was enabled in namespace `sw`.

## Validation
The following connectivity checks were performed:

- `s1 -> r1` ping: success
- `s2 -> r1` ping: success

## Result
The minimal testbed was successfully created. Basic connectivity between senders and receiver through the intermediate node was confirmed. This indicates that the environment is suitable for traffic experiments.

## Conclusion
Experiment 001 confirms that the software-based namespace environment works correctly and can be used as the base platform for Phase 1 traffic contention experiments.

---

# Experiment 002: Bottleneck Contention and Latency Reproduction

## Date
2026-05-17

## Objective
To reproduce noticeable latency increase under controlled contention by introducing a bottleneck link and running concurrent flows through it.

## Experimental Design

### Topology
Same as Experiment 001:

`s1, s2 -> sw -> r1`

### Bottleneck Configuration
A bottleneck was introduced on the outgoing interface from `sw` to `r1`:

- Namespace: `sw`
- Interface: `veth-swr`
- qdisc: `tbf`
- Rate: `10mbit`
- Burst: `32kbit`
- Latency: `50ms`

### Traffic Configuration
Two concurrent TCP flows were generated using `iperf3`:

- `s1 -> r1` on port `5201`
- `s2 -> r1` on port `5202`

At the same time, latency was measured using:

- `ping` from `s1` to `r1`
- interval: `0.2s`

### Data Files
The following data files were collected:

#### Run 1
- `ping_run1.txt`
- `iperf_s1_run1.txt`
- `iperf_s2_run1.txt`

#### Run 2
- `ping_run2.txt`
- `iperf_s1_run2.txt`
- `iperf_s2_run2.txt`

#### Run 3
- `ping_run3.txt`
- `iperf_s1_run3.txt`
- `iperf_s2_run3.txt`

---

# Run 1

## RTT Result
From the extracted RTT data:

- **Average RTT:** `25.9893 ms`
- **Maximum RTT:** `136 ms`

### Top RTT values
- 111 ms
- 114 ms
- 114 ms
- 121 ms
- 124 ms
- 125 ms
- 126 ms
- 126 ms
- 134 ms
- 136 ms

## Throughput Result
### s1
- Sender throughput: approximately `3.91 Mbits/sec`

### s2
- Sender throughput: approximately `2.59 Mbits/sec`

### Combined sender throughput
- Approximately `6.50 Mbits/sec`

## Observation
In Run 1, latency increased clearly under contention compared with the idle baseline. Most RTT values during the active contention period rose to tens of milliseconds, with repeated spikes above 100 ms. Both flows were able to transmit traffic, but the throughput was unevenly shared.

## Interpretation
Run 1 demonstrates that the bottleneck configuration is effective and that concurrent traffic already leads to noticeable queueing delay. The overall contention effect is clear but relatively moderate compared with the later runs.

## Run 1 Conclusion
The software-based testbed can reproduce contention-related latency increase in a stable way. Run 1 provides the first successful proof-of-concept result.

---

# Run 2

## RTT Result
From the extracted RTT data:

- **Average RTT:** `85.9833 ms`
- **Maximum RTT:** `562 ms`

### Top RTT values
- 178 ms
- 183 ms
- 200 ms
- 209 ms
- 235 ms
- 239 ms
- 276 ms
- 301 ms
- 341 ms
- 562 ms

## Throughput Result
### s1
- Sender throughput: approximately `2.45 Mbits/sec`

### s2
- Sender throughput: approximately `4.75 Mbits/sec`

### Combined sender throughput
- Approximately `7.20 Mbits/sec`

## Observation
Run 2 produced the strongest latency spike among all runs. RTT values were frequently in the range of tens to hundreds of milliseconds, and the peak reached 562 ms. At the same time, the two flows showed an asymmetric throughput split, with `s2` obtaining noticeably more bandwidth than `s1`.

## Interpretation
This run suggests that the same testbed can produce more severe congestion episodes depending on the exact runtime dynamics of the two flows. The strong RTT spikes indicate significant queue buildup or short-term backlog formation at the bottleneck. The fact that the two senders did not split throughput evenly also suggests unstable short-term contention behavior, which is realistic and useful for later telemetry analysis.

## Run 2 Conclusion
Run 2 confirms that the testbed can generate strong, clearly visible latency spikes under bottleneck contention. This run is especially valuable as a proof that the environment can produce severe congestion effects.

---

# Run 3

## RTT Result
From the extracted RTT data:

- **Average RTT:** `80.9653 ms`
- **Maximum RTT:** `308 ms`

### Top RTT values
- 198 ms
- 204 ms
- 207 ms
- 209 ms
- 211 ms
- 213 ms
- 217 ms
- 219 ms
- 225 ms
- 308 ms

## Throughput Result
### s1
- Sender throughput: approximately `3.24 Mbits/sec`

### s2
- Sender throughput: approximately `1.89 Mbits/sec`

### Combined sender throughput
- Approximately `5.13 Mbits/sec`

## Observation
Run 3 again reproduced clear RTT inflation, with many RTT samples in the 60–200 ms range and a maximum of 308 ms. Compared with Run 2, the maximum spike was lower, but the average RTT remained high. Throughput was lower overall than in Run 2, and `s2` experienced weaker performance than `s1`.

## Interpretation
Run 3 confirms that the congestion-induced latency increase is reproducible, although its exact intensity varies from run to run. The lower combined throughput may indicate stronger inefficiency or harsher contention during this run. This variation is useful because it shows that the environment can produce multiple congestion severities rather than only one fixed behavior.

## Run 3 Conclusion
Run 3 further confirms the reproducibility of latency increase in the current testbed and shows that the system can generate different contention intensities across repeated runs.

---

# Cross-Run Summary

## RTT Comparison
- **Run 1:** avg `25.9893 ms`, max `136 ms`
- **Run 2:** avg `85.9833 ms`, max `562 ms`
- **Run 3:** avg `80.9653 ms`, max `308 ms`

## Overall Pattern
All three runs showed a clear increase in RTT under concurrent traffic contention. Compared with the near-zero idle baseline seen outside the active traffic period, the measured RTT during contention rose to tens and hundreds of milliseconds.

## Relative Severity
- **Run 1** was the mildest among the three runs.
- **Run 2** was the strongest and produced the largest spike.
- **Run 3** was also severe, though less extreme than Run 2.

## Throughput Comparison
- **Run 1 total sender throughput:** about `6.50 Mbits/sec`
- **Run 2 total sender throughput:** about `7.20 Mbits/sec`
- **Run 3 total sender throughput:** about `5.13 Mbits/sec`

## Interpretation
The cross-run results indicate that:

1. The bottleneck contention effect is reproducible.
2. The latency increase is not an isolated event.
3. The severity of the congestion varies across runs.
4. The throughput split between competing flows is not fixed and may change from run to run.
5. The current software-based setup is sufficient for proof-of-concept latency experiments.

---

# Preliminary Phase 1 Findings

## Main Findings
1. A minimal namespace-based software testbed was successfully built.
2. Controlled bottleneck contention could be created using `tc qdisc tbf`.
3. Concurrent `iperf3` flows could consistently trigger noticeable latency increase.
4. RTT inflation under contention was clearly measurable and reproducible.
5. Initial dataset collection for latency behavior has been completed.

## What Has Been Proven in Phase 1
Phase 1 has shown that the current setup is capable of reproducing congestion-related latency increase in a controlled environment. This confirms that the environment is suitable for continued data collection and later telemetry correlation.

## Current Limitation
At this stage, the collected data mainly includes:

- end-to-end latency measurements (`ping`)
- throughput and retransmission information (`iperf3`)

Kernel-level telemetry has not yet been added. Therefore, the current results validate the testbed and the latency phenomenon, but not yet the kernel-level observability objective.

---

# Phase 1 Status Assessment

## Completed
- Minimal topology setup
- Connectivity verification
- Bottleneck configuration
- Multi-run traffic contention experiment
- Data collection for ping and iperf3
- RTT extraction and summary statistics
- Experimental logging

## Remaining Phase 1 Work
The following tasks are still appropriate within Phase 1:

1. Save a baseline run without contention
2. Organize RTT data into CSV format
3. Plot RTT curves for run1/run2/run3
4. Collect simple link-level statistics such as:
   - `tc -s qdisc`
   - `ip -s link`
5. Prepare a concise Phase 1 summary for supervisor discussion

---

# Final Preliminary Conclusion

The current Phase 1 experiments demonstrate that the software-based namespace testbed can reliably reproduce noticeable latency increase under bottleneck contention. Across three runs, the RTT rose from an idle near-zero baseline to tens and hundreds of milliseconds, with the most severe case reaching 562 ms. These results provide a strong proof-of-concept basis for continuing Phase 1 data collection and for later studying whether low-level telemetry signals can be aligned with such latency spikes.
