#!/usr/bin/env python

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.mit.request import DnQuery
from cobra.mit.request import ClassQuery

import pygraphviz
import sys
import argparse


# Parsing command line arguments
parser = argparse.ArgumentParser(description='Script to plot diagrams from running ACI fabric')
parser.add_argument('-t', '--tenant', help='Tenant to generate a diagram for. Default: all Tenants present in the ACI fabric', nargs='?', metavar='example_tn')
parser.add_argument('-o', '--output', help='Output file name. Default: out.png', default="out.png")
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


# Initiating a session to APIC
apicUrl = "https://10.61.6.121:20109"
loginSession = LoginSession(apicUrl, "automation", "automation123", secure=False)
moDir = MoDirectory(loginSession)
moDir.login()


# Verify if user provided a Tenant name in command line
if args.tenant:

    # Look up a single Tenant specified as a command line argument "-t"
    fvTenant = moDir.lookupByClass("fvTenant", propFilter='and(eq(fvTenant.name, "%s"))'%args.tenant)
else:

    # Look up all Tenant names
    fvTenant = moDir.lookupByClass("fvTenant")


# Processing a Tenant
for tenant in fvTenant:
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
            tnCluster.add_edge(ctx_node(tenant.name, ctx.tnFvCtxName), l3out_node(tenant.name,l3out.name), style='dotted') # The name of attached VRF is in attribute "tnFvCtxName"


        # Plot External EPGs (exEPG)
        # Query all exEPGs that belong to the L3Out
        exEpgQuery = ClassQuery(str(l3out.dn)+"/l3extInstP")
        l3extInstP = moDir.query(exEpgQuery)

        for exEpg in l3extInstP:

            # Plot exEPG
            l3outCluster.add_node(outside_epg_node(tenant.name, l3out.name, exEpg.name), label="Outside EPG\n"+exEpg.name)

            # Plot exEPG to L3Out connection
            l3outCluster.add_edge(l3out_node(tenant.name, l3out.name), outside_epg_node(tenant.name, l3out.name, exEpg.name))


            # Plot Contracts provided by this exEPG, if any
            # Query what Contracts this exEPG provides
            pcQuery = ClassQuery(str(exEpg.dn)+"/fvRsProv") # Provided Contract will have a child MO "fvRsProv"
            fvRsProv = moDir.query(pcQuery)

            for pc in fvRsProv:

                # Plot Provided Contract
                l3outCluster.add_node(ctrct_node(tenant.name, pc.tnVzBrCPName), label="Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                # Plot Provided Contract to exEPG connection
                l3outCluster.add_edge(outside_epg_node(tenant.name, l3out.name, exEpg.name), ctrct_node(tenant.name, pc.tnVzBrCPName), label="p")


            # Plot Contracts consumed by this exEPG, if any
            # Query what Contracts this exEPG consumes
            ccQuery = ClassQuery(str(exEpg.dn)+"/fvRsCons") # Consumed Contract will have a child MO "fvRsCons"
            fvRsCons = moDir.query(ccQuery)

            for cc in fvRsCons:

                # Plot Consumed Contract
                #apCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='lightgray')
                l3outCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                # Plot Consumed Contract to exEPG connection
                #apCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), epg_node(tenant.name, ap.name, epg.name))
                l3outCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), outside_epg_node(tenant.name, l3out.name, exEpg.name), label="c")


    # Plot BDs
    # Query all BDs that belong to the Tenant
    bdQuery = ClassQuery(str(tenant.dn)+"/fvBD")
    fvBD = moDir.query(bdQuery)

    for bd in fvBD:
        tnCluster.add_node(bd_node(tenant.name, bd.name), label="Bridge Domain\n"+bd.name, shape='box') # Plot a BD


        # Query what VRF this BD attaches to
        ctxQuery = ClassQuery(str(bd.dn)+"/fvRsCtx") # If there is a VRF attached, BD will have a child MO "fvRsCtx"
        attachedCtx = moDir.query(ctxQuery)


        # Plot BD to VRF connection
        # Checking if indeed there is a VRF attached (or maybe several VRFs in the future)
        for ctx in attachedCtx:
            if ctx.tnFvCtxName: # The name of attached VRF is in attribute "tnFvCtxName"
                tnCluster.add_edge(ctx_node(tenant.name, ctx.tnFvCtxName), bd_node(tenant.name, bd.name))
            else: # If VRF is not attached, then create an invisible node to move BD node to the right
                tnCluster.add_node("_ctx-dummy-"+bd_node(tenant.name, bd.name), style="invis", label='Dummy Context', shape='circle')
                tnCluster.add_edge("_ctx-dummy-"+bd_node(tenant.name, bd.name), bd_node(tenant.name, bd.name), style="invis")


        # Query what L3Outs this BD attaches to, if any
        l3OutQuery = ClassQuery(str(bd.dn)+"/fvRsBDToOut") # If there is a L3Out attached, BD will have a child MO "fvRsBDToOut"
        attachedL3Out = moDir.query(l3OutQuery)


        # Plot BD to L3Out connection, if any
        for l3out in attachedL3Out:
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
            apCluster.add_node(epg_node(tenant.name, ap.name, epg.name), label="EPG\n"+epg.name) # Plot an EPG


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

                # Plot Provided Contract
                apCluster.add_node(ctrct_node(tenant.name, pc.tnVzBrCPName), label="Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                # Plot Provided Contract to EPG connection
                apCluster.add_edge(epg_node(tenant.name, ap.name, epg.name), ctrct_node(tenant.name, pc.tnVzBrCPName), label="p")


            # Plot Contracts consumed by this EPG, if any
            # Query what Contracts this EPG consumes
            ccQuery = ClassQuery(str(epg.dn)+"/fvRsCons") # Consumed Contract will have a child MO "fvRsCons"
            fvRsCons = moDir.query(ccQuery)

            for cc in fvRsCons:

                # Plot Consumed Contract
                apCluster.add_node(ctrct_node(tenant.name, cc.tnVzBrCPName), label="Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='lightgray')

                # Plot Consumed Contract to EPG connection
                apCluster.add_edge(ctrct_node(tenant.name, cc.tnVzBrCPName), epg_node(tenant.name, ap.name, epg.name), label="c")


moDir.logout()

print ("\nGenerating diagram")
graph.draw(args.output, prog='dot')


## TODO:
# 1. Comprehensive prints on every step e.g. Plot BD-X
# 2. If L3Out is not attached to a BD, create a dummy node to move L3Out to the right
# 3. Fix L3Out to VRF connection in Tenant Common
