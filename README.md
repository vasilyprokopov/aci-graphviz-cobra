# Graphviz Cobra

Generate diagrams from running Cisco ACI Fabrics.

## Description

This tool is a Python3 script that:
- Initiates a connection to a running Cisco ACI Fabric
- Queries each Tenant
- And plots

## Use Cases

Diagrams produced by this tool will help you to:
- Reveal object relations within the Tenant and between the Tenants
    * To simplify troubleshooting
    * And to sparkle ideas how to optimise the configuration
- Facilitate documentation by generating relevant diagrams that reflect current fabric state
- Sort out Contract configuration:
    * Reveal unused Contracts
    * Reveal Contracts with wrongly configured Scope
    * Visually figure out required Scope for the Contract (e.g. doesn't leave AP)
- Spot unused Objects (e.g. VRFs, BDs)
- Reveal missing links between objects (e.g. L3Out to VRF or BD)

## Prerequisites

The tool depends on:
- [Cobra](https://github.com/datacenter/cobra)
- [pyGraphviz](https://github.com/pygraphviz/pygraphviz)

Make sure you have these installed before attempting to run the script.

## Supported Objects

Tenant, VRF, BD, BD Subnet, Application Profile, Application EPG, L3Out, External EPG,

## ToDo

## Author

[**Vasily Prokopov**](https://github.com/vasilyprokopov)

## License

See the [LICENSE](LICENSE) file for details.

## Acronyms

- BD
- VRF
