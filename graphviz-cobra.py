#!/usr/bin/env python

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# How to execute example:
# sudo python graphviz-cobra.py -u admin -p cisco123 -a https://192.168.1.1 -t graphviz1_tn graphviz2_tn

import pygraphviz
import sys
import argparse

from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession

from plottenant import plot_tenant # Import plot_tenant() function from a separate module plotTenant (file plotTenant.py)


# Disable InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Parsing command line arguments
parser = argparse.ArgumentParser(description='Script to plot diagrams from running ACI fabric')

#parser.add_argument('-m', '--mode', help='Tenant/Fabric/EPG', nargs='?', metavar='user', required=True)
parser.add_argument('-u', '--user', help='APIC Username', nargs='?', metavar='user', required=True)
parser.add_argument('-p', '--password', help='APIC Password', nargs='?', metavar='Cisco123', required=True)
parser.add_argument('-a', '--apic', help='APIC URL', nargs='?', metavar='https://192.168.1.1', required=True)
parser.add_argument('-t', '--tenant', help='Tenants to generate diagrams for. Use space to separate. Default: all Tenants', nargs='*', metavar='example_tn')
parser.add_argument('-o', '--output', help='Output file name. Default: out.png', default="out.png")
parser.add_argument('-vv', '--verbose', help='', action='store_true')
args = parser.parse_args()


# Create global graph space, define its parameters
graph=pygraphviz.AGraph(directed=True, rankdir="LR", K=0.5)


# Initiate session to APIC
apicUrl = args.apic
apicUser = args.user
apicPass = args.password
loginSession = LoginSession(apicUrl, apicUser, apicPass, secure=False)
moDir = MoDirectory(loginSession)
moDir.login()


# Look up all Tenant names
fvTenant = moDir.lookupByClass("fvTenant")


# Process each Tenant
for tenant in fvTenant:
    if not args.tenant: # If user didn't provide -tenant command line argument
        # Call a plot_tenant function from an external module plot_tenant
        plot_tenant(tenant, graph, moDir) # Pass along Tenant name, graph that this tenant should be part of, session to the APIC - moDir
    elif args.tenant and tenant.name in args.tenant: # If -tenant command line argument was provided, and this tenant exists in ACI
        plot_tenant(tenant, graph, moDir)


# Close session to APIC
moDir.logout()


# Print the graph
print ("\nGenerating diagram")
graph.draw(args.output, prog='dot')

if args.verbose:
    print (graph.string())


## USE CASES
# Reveal object relations within the Tenant and between the Tenants
    # Can provide ideas how to optimize or streamline the configuration
# Contracts:
    # Find unused
    # Find Contracts with wrong scope
    # Visually figure out required Scope for context (e.g. doesn't leave AP)
# Find unused Objects (e.g. Contracts, VRFs)
# Reveal missing links between objects (e.g. L3Out to VRF or BD)


## TODO:
# Readme
# Comprehensive prints on every step e.g. Plot BD-X
# If L3Out is not attached to a BD, create a dummy node to move L3Out to the right
# Add L2 and L3 BD depending on L3 Unicast Forwarding
# If some object is missing but relation is present, flag it (like with missing contracts)
# See if there's better way to implement: i = ctrctIf.tDn.rfind("/cif-")+4
# Check if BD is indeed connected to L3Out (L3Out exists), TN-PROD in BRU
# If number of objects is more than 200 suggest splitting into Tenants
# Taboo Contarcts


## NOT IMPLEMENTED:
# Add message if contract is unused - too complex to query all child objects of a contract (if only way to query several in one go would exist)
# Contact Subjects and Filters: may appear heavy visually if there are many sbj and flt per Contract

## IMPLEMENTED:
# Think about plotting all contracts at first, rather then plotting on-demand according to the fact of consumption
    # This may streamline the diagram and also reveal unused contracts
# Add Contract Scopes
