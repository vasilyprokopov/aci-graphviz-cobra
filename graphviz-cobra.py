#!/usr/bin/env python

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# How to execute example:
# sudo python graphviz-cobra.py -u admin -p cisco123 -a https://192.168.1.1 -t graphviz1_tn graphviz2_tn

from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.mit.request import DnQuery
from cobra.mit.request import ClassQuery

import pygraphviz
import sys
import argparse


# Disable InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Parsing command line arguments
parser = argparse.ArgumentParser(description='Script to plot diagrams from running ACI fabric')
parser.add_argument('-t', '--tenant', help='Tenants to generate diagrams for. Use space to separate. Default: all Tenants', nargs='*', metavar='example_tn')
parser.add_argument('-o', '--output', help='Output file name. Default: out.png', default="out.png")
parser.add_argument('-u', '--user', help='APIC Username', nargs='?', metavar='user', required=True)
parser.add_argument('-p', '--password', help='APIC Password', nargs='?', metavar='Cisco123', required=True)
parser.add_argument('-a', '--apic', help='APIC URL', nargs='?', metavar='https://192.168.1.1', required=True)
parser.add_argument('-vv', '--verbose', help='', action='store_true')
args = parser.parse_args()


# Graphviz
graph=pygraphviz.AGraph(directed=True, rankdir="LR")


# Defining nodes for graphviz
def tn_node(tn):
    return "cluster-tn-"+tn

def ctx_node(tn, ctx):
    return tn_node(tn)+"/ctx-"+ctx

def bd_node(tn, bd):
    return tn_node(tn)+"/bd-"+bd

def ap_node(tn, ap):
    return tn_node(tn)+"/ap-"+ap

def epg_node(tn, ap, epg):
    return ap_node(tn, ap)+"/epg-"+epg

def ctrct_node(tn, ctrct):
    return tn_node(tn)+"/ctrct-"+ctrct

def l3out_node(tn, l3out):
    return tn_node(tn)+"/l3out-"+l3out

def outside_epg_node(tn, l3out, exEpg):
    return l3out_node(tn, l3out)+"/outside-epg-"+exEpg

def ctrctIf_node(ctrctIf):
    return "global-ctrctIf-"+ctrctIf # In the global graph space, because needs to be shared between Tenants


# Defining Plot Tenant function
def plot_tenant():
    print("Processing Tenant "+tenant.name)
    # Plot a Tenant
    tnCluster = graph.add_subgraph(name=tn_node(tenant.name), label="Tenant\n"+tenant.name, color="blue")


    # Plot VRFs
    # Query all VRFs that belong to the Tenant
    vrfQuery = ClassQuery(str(tenant.dn)+"/fvCtx") # Creating a query for VRFs, that takes "uni/tn-graphviz/fvCtx" as a Class input
    fvCtx = moDir.query(vrfQuery) # Executing a query that was created

    for ctx in fvCtx:
        tnCluster.add_node(ctx_node(tenant.name, ctx.name), label="VRF\n"+ctx.name, shape='box')


    # Plot L3Outs
        # Plot separate subgraph for all L3Outs that belong to the Tenant - Option 1
        # l3outCluster=tnCluster.add_subgraph(name=tn_node(tenant.name)+"/l3extOut", label="L3Outs")


    # Query all L3Outs that belong to the Tenant
    l3OutQuery = ClassQuery(str(tenant.dn)+"/l3extOut")
    l3extOut = moDir.query(l3OutQuery)

    for l3out in l3extOut:

        # Plot separate subgraph per each L3Out that belongs to the Tenant - Option 2
        l3outCluster=tnCluster.add_subgraph(name=l3out_node(tenant.name, l3out.name), label="L3Out")

        # Plot L3Out within the previously created subgraph
        l3outCluster.add_node(l3out_node(tenant.name, l3out.name), label = "L3Out\n"+l3out.name, shape='box')


        # Query what VRF this L3Out attaches to
        ctxQuery = ClassQuery(str(l3out.dn)+"/l3extRsEctx") # If there is a VRF attached, L3Out will have a child MO "l3extRsEctx"
        attachedCtx = moDir.query(ctxQuery)


        # Plot L3Out to VRF connection, if any
        for ctx in attachedCtx:
            if ctx.tnFvCtxName: # Verify if there is indeed VRF attached
                tnCluster.add_edge(ctx_node(tenant.name, ctx.tnFvCtxName), l3out_node(tenant.name,l3out.name), style='dotted') # The name of attached VRF is in attribute "tnFvCtxName"


        # Plot External EPGs (exEPG)
        # Query all exEPGs that belong to the L3Out
        exEpgQuery = ClassQuery(str(l3out.dn)+"/l3extInstP")
        l3extInstP = moDir.query(exEpgQuery)

        for exEpg in l3extInstP:
            # Construct a label that includes Subnets
            label = "Outside EPG\n"+exEpg.name
            subnetQuery = ClassQuery(str(exEpg.dn)+"/l3extSubnet")
            fvSubnet = moDir.query(subnetQuery)
            for subnet in fvSubnet:
                label = label+"\n"+subnet.ip


            # Plot exEPG
            l3outCluster.add_node(outside_epg_node(tenant.name, l3out.name, exEpg.name), label=label)


            # Plot exEPG to L3Out connection
            l3outCluster.add_edge(l3out_node(tenant.name, l3out.name), outside_epg_node(tenant.name, l3out.name, exEpg.name))


            # Plot Contracts provided by this exEPG, if any
            # Query what Contracts this exEPG provides
            pcQuery = ClassQuery(str(exEpg.dn)+"/fvRsProv") # Provided Contract will have a child MO "fvRsProv"
            fvRsProv = moDir.query(pcQuery)

            for pc in fvRsProv:
                if pc.state == "formed": # Check if contract exists

                    # Plot Provided Contract
                    l3outCluster.add_node(ctrct_node(tenant.name, pc.tnVzBrCPName), label="Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                    # Plot Provided Contract to exEPG connection
                    l3outCluster.add_edge(outside_epg_node(tenant.name, l3out.name, exEpg.name), ctrct_node(tenant.name, pc.tnVzBrCPName), label="p")

                elif pc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    l3outCluster.add_node(ctrct_node(tenant.name, pc.tnVzBrCPName), label="Missing Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to exEPG connection
                    l3outCluster.add_edge(outside_epg_node(tenant.name, l3out.name, exEpg.name), ctrct_node(tenant.name, pc.tnVzBrCPName), label="p")


            # Plot Contracts consumed by this exEPG, if any
            # Query what Contracts this exEPG consumes
            ccQuery = ClassQuery(str(exEpg.dn)+"/fvRsCons") # Consumed Contract will have a child MO "fvRsCons"
            fvRsCons = moDir.query(ccQuery)

            for cc in fvRsCons:
                if cc.state == "formed": # Check if contract exists

                    # Plot Consumed Contract
                    l3outCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                    # Plot Consumed Contract to exEPG connection
                    l3outCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), outside_epg_node(tenant.name, l3out.name, exEpg.name), label="c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    l3outCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Missing Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to exEPG connection
                    l3outCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), outside_epg_node(tenant.name, l3out.name, exEpg.name), label="c")


            # Plot Contract Interfaces consumed by this exEPG, if any
            # Query what Contract Interfaces this exEPG consumes
            ccQuery = ClassQuery(str(exEpg.dn)+"/fvRsConsIf") # Consumed Contract Interface will have a child MO "fvRsConsIf"
            fvRsConsIf = moDir.query(ccQuery)

            for cc in fvRsConsIf:
                if cc.state == "formed": # Check if Contract Interface exists

                    # Plot Consumed Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='lightgray')

                    # Plot Consumed Contract Interface to exEPG connection
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), outside_epg_node(tenant.name, l3out.name, exEpg.name), label="inter-tenant c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Missing Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract Interface to exEPG connection
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), outside_epg_node(tenant.name, l3out.name, exEpg.name), label="inter-tenant c")


    # Plot BDs
    # Query all BDs that belong to the Tenant
    bdQuery = ClassQuery(str(tenant.dn)+"/fvBD")
    fvBD = moDir.query(bdQuery)

    for bd in fvBD:
        # Construct a label that includes Subnets
        label = "Bridge Domain\n"+bd.name
        subnetQuery = ClassQuery(str(bd.dn)+"/fvSubnet")
        fvSubnet = moDir.query(subnetQuery)
        for subnet in fvSubnet:
            label = label+"\n"+subnet.ip


        # Plot a BD
        tnCluster.add_node(bd_node(tenant.name, bd.name), label=label, shape='box')


        # Query what VRF this BD attaches to
        ctxQuery = ClassQuery(str(bd.dn)+"/fvRsCtx") # If there is a VRF attached, BD will have a child MO "fvRsCtx"
        attachedCtx = moDir.query(ctxQuery)


        # Plot BD to VRF connection, if any
        for ctx in attachedCtx:
            if ctx.tnFvCtxName: # Verify if there is indeed VRF attached (or maybe several VRFs in the future)
                tnCluster.add_edge(ctx_node(tenant.name, ctx.tnFvCtxName), bd_node(tenant.name, bd.name))
            else: # If VRF is not attached, then create an invisible node to move BD to the right
                tnCluster.add_node("_ctx-dummy-"+bd_node(tenant.name, bd.name), style="invis", label='Dummy Context', shape='circle')
                tnCluster.add_edge("_ctx-dummy-"+bd_node(tenant.name, bd.name), bd_node(tenant.name, bd.name), style="invis")


        # Query what L3Outs this BD attaches to
        l3OutQuery = ClassQuery(str(bd.dn)+"/fvRsBDToOut") # If there is a L3Out attached, BD will have a child MO "fvRsBDToOut"
        attachedL3Out = moDir.query(l3OutQuery)


        # Plot BD to L3Out connection, if any
        for l3out in attachedL3Out:
            if l3out.tnL3extOutName: # Verify if there is indeed a L3Out attached
                tnCluster.add_edge(bd_node(tenant.name, bd.name), l3out_node(tenant.name,l3out.tnL3extOutName), style='dotted') # The name of attached L3Out is in attribute "tnL3extOutName"


    # Plot APs
    # Query all APs that belong to the Tenant
    apQuery = ClassQuery(str(tenant.dn)+"/fvAp")
    fvAp = moDir.query(apQuery)

    for ap in fvAp:
        apCluster=tnCluster.add_subgraph(name=ap_node(tenant.name, ap.name), label="Application Profile\n"+ap.name) # Plot an AP


        # Plot EPGs
        # Query all EPGs that belong to the AP
        epgQuery = ClassQuery(str(ap.dn)+"/fvAEPg")
        fvAEPg = moDir.query(epgQuery)

        for epg in fvAEPg:

            # Construct a label that includes Preferred Group for VRF information
            label = "EPG\n"+epg.name
            if epg.prefGrMemb == "include":
                label = label + "\n Preferred Group Member"

            apCluster.add_node(epg_node(tenant.name, ap.name, epg.name), label=label) # Plot an EPG


            # Plot EPG to BD connection
            # Query what BD this EPG attaches to
            bdQuery = ClassQuery(str(epg.dn)+"/fvRsBd") # BD will have a child MO "fvRsBd"
            attachedBd = moDir.query(bdQuery)
            for bd in attachedBd:
                tnCluster.add_edge(bd_node(tenant.name, bd.tnFvBDName), epg_node(tenant.name, ap.name, epg.name), style='dotted')


            # Plot Contracts provided by this EPG, if any
            # Query what Contracts this EPG provides
            pcQuery = ClassQuery(str(epg.dn)+"/fvRsProv") # Provided Contract will have a child MO "fvRsProv"
            fvRsProv = moDir.query(pcQuery)

            for pc in fvRsProv:
                if pc.state == "formed": # Check if contract is indeed present

                    # Plot Provided Contract
                    apCluster.add_node(ctrct_node(tenant.name, pc.tnVzBrCPName), label="Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                    # Plot Provided Contract to EPG connection
                    apCluster.add_edge(epg_node(tenant.name, ap.name, epg.name), ctrct_node(tenant.name, pc.tnVzBrCPName), label="p")

                elif pc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    apCluster.add_node(ctrct_node(tenant.name, pc.tnVzBrCPName), label="Missing Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to EPG connection
                    apCluster.add_edge(epg_node(tenant.name, ap.name, epg.name), ctrct_node(tenant.name, pc.tnVzBrCPName), label="p")


            # Plot Contracts consumed by this EPG, if any
            # Query what Contracts this EPG consumes
            ccQuery = ClassQuery(str(epg.dn)+"/fvRsCons") # Consumed Contract will have a child MO "fvRsCons"
            fvRsCons = moDir.query(ccQuery)

            for cc in fvRsCons:
                if cc.state == "formed": # Check if contract exists

                    # Plot Consumed Contract
                    apCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                    # Plot Consumed Contract to EPG connection
                    apCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), epg_node(tenant.name, ap.name, epg.name), label="c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    apCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Missing Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to EPG connection
                    apCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), epg_node(tenant.name, ap.name, epg.name), label="c")


            # Plot Contract Interfaces consumed by this EPG, if any
            # Query what Contract Interfaces this EPG consumes
            ccQuery = ClassQuery(str(epg.dn)+"/fvRsConsIf") # Consumed Contract Interface will have a child MO "fvRsConsIf"
            fvRsConsIf = moDir.query(ccQuery)

            for cc in fvRsConsIf:
                if cc.state == "formed": # Check if Contract Interface exists

                    # Plot Consumed Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='lightgray')

                    # Plot Consumed Contract Interface to EPG connection
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), epg_node(tenant.name, ap.name, epg.name), label="inter-tenant c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Missing Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract Interface to EPG connection
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), epg_node(tenant.name, ap.name, epg.name), label="inter-tenant c")


    # Plot Contract Interfaces Provided by this Tenant
    # Query all Contracts that belong to this Tenant
    ctrctQuery = ClassQuery(str(tenant.dn)+"/vzBrCP") # Creating a query for Contracts, that takes "uni/tn-graphviz/vzBrCP" as a Class input
    vzBrCP = moDir.query(ctrctQuery)

    # Check if a Contract is exported to other Tenants by quering all Conract Interfaces that belong to this Contract, if any
    for ctrct in vzBrCP:
        ctrctIfQuery = ClassQuery(str(ctrct.dn)+"/vzRtIf")
        vzRtIf = moDir.query(ctrctIfQuery)

        for ctrctIf in vzRtIf: # Check if Contract Interface is indeed present
            if ctrctIf.tDn: #
                i = ctrctIf.tDn.rfind("/cif-")+5 # In tDn we need to find the index where "cif-" ends
                ctrctIfName = ctrctIf.tDn[i : : ] # Taking everythin starting from index i to the end of the string, and stripping the beggining before i

                # Plot Contract
                tnCluster.add_node(ctrct_node(tenant.name, ctrct.name), label="Contract\n"+ctrct.name, shape='box', style='filled', color='lightgray')

                # Plot Contract Interface in the gloabal graph space
                tnCluster.add_node(ctrctIf_node(ctrctIfName), label="Contract Interface\n"+ctrctIfName, shape='box', style='filled', color='lightgray')

                # Plot Contract to Contract Interface connection
                tnCluster.add_edge(ctrct_node(tenant.name, ctrct.name), ctrctIf_node(ctrctIfName), label="inter-tenant p")
# End of Plot Tenant function


# Initiating a session to APIC
apicUrl = args.apic
apicUser = args.user
apicPass = args.password
loginSession = LoginSession(apicUrl, apicUser, apicPass, secure=False)
moDir = MoDirectory(loginSession)
moDir.login()


# Look up all Tenant names
fvTenant = moDir.lookupByClass("fvTenant")


# Processing each Tenant
for tenant in fvTenant:
    if not args.tenant: # If user didn't provide -tenant command line argument
        plot_tenant()
    elif args.tenant and tenant.name in args.tenant: # If user provided -tenant command line argument, and this tenant exists in ACI
        plot_tenant()


# Closing a session to APIC
moDir.logout()

print ("\nGenerating diagram")
graph.draw(args.output, prog='dot')

if args.verbose:
    print (graph.string())

## TODO:
# Readme
# Comprehensive prints on every step e.g. Plot BD-X
# If L3Out is not attached to a BD, create a dummy node to move L3Out to the right
# Add support for VZany
# Add contact Subjects and Filters
# Add L2 and L3 BD depending on L3 Unicast Forwarding
# If some object is missing but relation is present, flag it (like with missing contracts)
# See if there's better way to implement: i = ctrctIf.tDn.rfind("/cif-")+4
# Check if BD is indeed connected to L3Out (L3Out exists), TN-PROD in BRU
# If number of objects is more than 200 suggest splitting into Tenants.
