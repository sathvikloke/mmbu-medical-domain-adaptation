# UTC MOCS access audit

**Observed:** `2026-10-18T03:38:37Z`, repeated `2026-10-18T03:56:22Z`, alternate-host check
`2026-10-17 23:01 CDT`, route-state recheck `2026-10-18T04:28:05Z`, and independent route recheck
`2026-10-18T04:47:44Z`, with a latest bounded recheck at `2026-10-18T05:34:02Z`  
**Scope:** read-only local configuration and non-interactive login reachability; no job, allocation, model, or GPU action

## Result

The local SSH configuration contains a dedicated MocsHPC alias targeting the public hostname
`login.mocshpc.utc.edu` and a configured local account identifier. The alias and account identifier are intentionally
redacted from this repository. This is evidence of a configured route, not evidence that the account, allocation,
credential, hostname, or scheduler is currently valid.

A non-interactive SSH reachability probe failed before authentication with:

```text
ssh: Could not resolve hostname login.mocshpc.utc.edu: nodename nor servname provided, or not known
```

The bounded probe was repeated eighteen minutes later with `BatchMode=yes`, an eight-second connection timeout, and a
remote request limited to hostname plus scheduler-command presence. It failed at the same DNS step before any remote
command or authentication. This strengthens only the claim that the configured route was unreachable from the current
network during both observations; it does not identify the cause or prove the hostname obsolete.

No login occurred. No scheduler command ran. No remote filesystem, account, allocation, module, quota, queue, GPU, or
runtime fact was observed. The configured user name must not be promoted to a verified-account fact.

The `04:28Z` recheck resolved the redacted local alias to `login.mocshpc.utc.edu`, the redacted configured account,
port 22, and one dedicated Ed25519 identity-file declaration. The identity file itself was not opened or printed. A bounded SSH command again
failed at DNS before authentication. Direct local resolver checks returned no address for either
`login.mocshpc.utc.edu` or `login01.mocshpc.utc.edu`. macOS reported only two configured third-party consumer VPN
services, both disconnected; no UTC VPN service was observed. This does not prove the absence of every possible UTC
network client or route, but it does establish that the required UTC path was not active through the enumerated native
VPN services at that time.

The `04:47Z` recheck independently confirmed the same redacted alias/account, hostname, port, and identity-file
declaration without opening the key. Python resolver calls for both official hostname variants returned `gaierror`
before authentication. GlobalProtect and `PanGPS` processes were running, and several `utun` interfaces existed, but
process/interface presence does not identify an authenticated UTC tunnel; DNS still supplied no MocsHPC address. No
SSH connection or remote command was attempted after the resolver failure. Compute readiness therefore remains 3.5.

The `05:34Z` recheck again resolved the redacted local alias only to `login.mocshpc.utc.edu`, the redacted configured
account, port 22, and the same dedicated identity-file declaration without opening the key. Both `login.mocshpc.utc.edu` and
`login01.mocshpc.utc.edu` still failed local address resolution with `gaierror`. The GlobalProtect application and
`PanGPS` service were running, while the enumerated native VPN services remained two disconnected consumer VPNs.
Because process presence still did not produce UTC DNS reachability, no SSH authentication or remote command was
attempted. This is a new same-state observation, not evidence that the account, allocation, or hostname is invalid.

The later primary-source check resolved part of that uncertainty. UTC's official
[first-login article](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/163777/Research-Institute-First-Time-Login-Instructions)
names `login.mocshpc.utc.edu`, says users must be added before login, and explicitly requires the UTC VPN when off
campus. A newer official [Jupyter environment article](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=165153)
names `login01.mocshpc.utc.edu` and the same Open OnDemand service. A bounded DNS plus non-interactive SSH probe of
`login01` also failed before authentication on the current network. The disagreement means neither hostname should be
silently substituted; the VPN/current internal instructions must establish the active route.

UTC's official [node inventory](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/PrintArticle?ID=163829) and
[partition guide](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/PrintArticle?ID=163830) establish a public planning
envelope, not account access: the published `epyc-gpu` partition uses A100 80 GB nodes, requires one or two GPUs, limits
CPU requests to eight per node, and permits up to five days; `epyc-full` requires explicit access. These facts may shape
a prospective preflight but cannot be copied into an allocation receipt. No official MocsHPC source found in this audit
uses the name “Solara”; the runbook therefore uses **Slurm/MocsHPC** unless an authenticated internal source proves a
separate service.

UTC's current [macOS VPN article](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/131579/Connect-Your-macOS-Computer-to-the-UTC-VPN)
identifies GlobalProtect, portal `vpn.utc.edu`, UTC credentials, and Duo as the approved path; it also warns that default
VPN access may require account elevation for privileged services. A read-only local application/process check found
`/Applications/GlobalProtect.app` and its `PanGPS` service running. This proves the official client is installed, not
that it is connected, authenticated, elevated for MocsHPC, or carrying the current route. Connecting would require an
interactive account/Duo action and was not attempted by this audit.

## Current classification

| Fact | Status | Reason |
|---|---|---|
| SSH alias exists | observed local configuration | Alias/hostname/account entries were present locally; private identifiers are redacted here |
| MOCS account usable | unknown | Probe never reached authentication |
| Login hostname current | conflicting official guidance | First-login article names `login`; newer Jupyter article names `login01`; neither resolved on the current network |
| VPN/campus route required | official off-campus requirement | UTC's first-login article explicitly instructs off-campus users to connect to the UTC VPN |
| UTC VPN active in observed native services | not observed | The enumerated native VPN services were disconnected third-party services; no UTC service appeared |
| Official GlobalProtect client installed | observed locally, latest 05:34Z | Application and `PanGPS` process exist; connection/authentication/elevation remain unverified and UTC DNS still fails |
| Scheduler/tools | unknown | No remote command executed |
| Allocation/project | unknown | No scheduler/account receipt |
| Public planning envelope | documented, not allocated | Official inventory lists A100/P100/V100 nodes and official partition limits; none proves availability to this account |
| GPU availability | unknown | Public inventory is not account availability |
| Native model feasibility | unknown | No weights, runtime, load, forward, step, export, or reload |

## Smallest safe next gate

1. The user connects the installed GlobalProtect client to official portal `vpn.utc.edu` and completes UTC/Duo login;
   if MocsHPC remains unreachable, verify whether VPN account elevation is required. This interactive identity action
   is not delegated to the audit.
2. On the resulting UTC route, verify whether current authenticated guidance names `login` or `login01`; do not guess
   further DNS variants.
3. Repeat a non-interactive reachability probe that prints only account name, login host, and presence of scheduler
   tools; do not print environment variables, credentials, home contents, or tokens.
4. If reachable, capture read-only scheduler/account facts (`sacctmgr`/site-approved equivalents, partitions, limits,
   and storage/quota) under a reviewed result schema.
5. Only after an allocation and bounded run condition are separately authorized may the first preflight job follow
   Work package D in [the Claude handoff](CLAUDE_HANDOFF.md).

Until steps 1–4 succeed, compute readiness remains **3.5/10**. The DNS failure is not a reason to change the SSH config,
request resources, submit a job, or substitute public hardware specifications for account evidence.
