#!/usr/bin/env python

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Execution example:
# sudo python graphviz-cobra.py -u admin -p cisco123 -a https://169.254.1.1 -t graphviz1_tn graphviz2_tn

import pygraphviz
import sys
import argparse
import getpass

from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession, CertSession

from plottenant import plot_tenant # Import plot_tenant() function from a separate module plottenant (file plottenant.py)


# Disable InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Parsing command line arguments
parser = argparse.ArgumentParser(description='Script to plot diagrams from running ACI fabric')

parser.add_argument('-u', '--user', help='APIC Username', nargs='?', metavar='user')
parser.add_argument('-p', '--password', help='APIC Password', nargs='?', metavar='Cisco123')
parser.add_argument('-a', '--apic', help='APIC URL', nargs='?', metavar='https://169.254.1.1')
parser.add_argument('-t', '--tenant', help='Tenants to generate diagrams for. Use space to separate. Default: all Tenants', nargs='*', metavar='example_tn')
parser.add_argument('-o', '--output', help='Output file name. Default: out.png', default="out.png")
parser.add_argument('-vv', '--verbose', help='', action='store_true')
parser.add_argument('-k', '--keyfile', help='APIC user private key file', nargs='?', metavar='user.key')
parser.add_argument('-c', '--certdn', help='APIC user certificate Dn', nargs='?', metavar='uni/userext/user-cisco/usercert-cisco_crt')
args = parser.parse_args()


# If Certificate Dn and Private Key file are both specified – we assume Cert-based authentication
if args.keyfile and args.certdn: # uni/userext/user-automation/usercert-automation_crt

    print ("Certificate-based authentication.")

    # If APIC URL was not provided as command line arguments
    if args.apic is None:
        args.apic = input("Enter APIC URL: ")

    # Open and read Private Key file
    privateKeyFile = open(args.keyfile, "r")
    privateKey = privateKeyFile.read()

    # Initiate session to APIC – Certificate-based authentication
    loginSession = CertSession(args.apic,"uni/userext/user-automation/usercert-automation_crt",privateKey, secure=False)
    moDir = MoDirectory(loginSession)
    moDir.login()

else: # If either Certificate Dn or Private Key are absent – we assume Password-based authentication

    print ("Password-based authentication.")

    # If APIC URL, Username, Password were not provided as command line arguments
    if args.apic is None:
        args.apic = input("Enter APIC URL: ")

    if args.user is None:
        args.user = input("Enter Username: ")

    if args.password is None:
        args.password = getpass.getpass("Enter Password: ")

    # Initiate session to APIC - Password-based authentication
    loginSession = LoginSession(args.apic, args.user, args.password, secure=False)
    moDir = MoDirectory(loginSession)
    moDir.login()


# Create global graph space, define its parameters
graph=pygraphviz.AGraph(directed=True, rankdir="LR", K=0.5, dpi=75) # Use dpi=150 for better resolutoin, for bigger Tenant use smaller resolution


# Look up all Tenant names
fvTenant = moDir.lookupByClass("fvTenant")


# Moving tenant "common" to the end of the list
# It needs to be processed last because otherwise some of the Common objects may get rewrited by other tenants and hence appear simplified
for tenant in fvTenant:
    if tenant.name == "common":
        fvTenant.append(fvTenant.pop(fvTenant.index(tenant)))


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


## NOT IMPLEMENTED:
# Contact Subjects and Filters: may appear heavy visually if there are many sbj and flt per Contract


## IMPLEMENTED:
# Think about plotting all contracts at first, rather then plotting on-demand according to the fact of consumption. This may streamline the diagram and also reveal unused contracts
# Add Contract Scopes
# Add L2 and L3 BD depending on L3 Unicast Forwarding
# Add tenant Common support for BD, EPG, Contract, L3Out, vzAny. Common objects are 'darkseagreen' color. If tenant Common itself is excluded from the diagram, its objects that other tenants refer to are plotted, but in a simplified form (e.g. no scope for Contracts)
# Tenant Common should be processed last, otherwise simplified objects do not get detalised
# Add message if contract is unused - too complex to query all child objects of a contract (if only way to query several in one go would exist)
# Mark unused Contracts as "Unused"
# Group unused contracts and put in a subgraph
# Certificate-based authentication
# Add example for tenant Common – regular Tanant references objects in Common
# Readme
