#!/usr/bin/env python

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.mit.request import DnQuery
from cobra.mit.request import ClassQuery

import pygraphviz as pgv
import sys

# Graphviz
graph=pgv.AGraph(directed=True, rankdir="LR")

# Defining nodes for graphviz
def tn_node(tn):
    return "cluster-tn-"+tn

def ctx_node(tn, ctx):
    return tn_node(tn)+"/ctx-"+ctx

def bd_node(tn, bd):
    return tn_node(tn)+"/bd-"+bd


# Initiating a session to APIC
apicUrl = "https://"
loginSession = LoginSession(apicUrl, "user", "pass", secure=False)
moDir = MoDirectory(loginSession)
moDir.login()

# Looking up all Tenant names
fvTenant = moDir.lookupByClass("fvTenant")

for tenant in fvTenant:
    print("Plotting Tenant "+tenant.name)


    # Plotting a Tenant
    tnCluster = graph.add_subgraph(name=tn_node(tenant.name), label="Tenant\n"+tenant.name, color="blue")


    # Quering all VRFs that belong to the Tenant
    vrfQuery = ClassQuery(str(tenant.dn)+"/fvCtx") # Creating a query for VRFs, that takes "uni/tn-graphviz/fvCtx" as a Class input

    fvCtx = moDir.query(vrfQuery) # Executing a query that was created
    for ctx in fvCtx:
        print(ctx.name)
        tnCluster.add_node(ctx_node(tenant.name, ctx.name), label="VRF\n"+ctx.name, shape='box')


    # Quering all BDs that belong to the Tenant
    bdQuery = ClassQuery(str(tenant.dn)+"/fvBD")

    fvBD = moDir.query(bdQuery)
    for bd in fvBD:
        print(bd.name)
        tnCluster.add_node(bd_node(tenant.name, bd.name), label="Bridge Domain\n"+bd.name, shape='box')

        # Quering VRF that this BD attaches to
        ctxQuery = ClassQuery(str(bd.dn)+"/fvRsCtx") # If there is a VRF attached, BD will have a child MO "fvRsCtx"
        attachedCtx = moDir.query(ctxQuery)
        print("Attached VRF: "+attachedCtx[0].tnFvCtxName)

        # Checking if indeed there is a VRF attached
        if attachedCtx[0].tnFvCtxName: # The name of attached VRF is in attribute "tnFvCtxName"
            tnCluster.add_edge(ctx_node(tenant.name, attachedCtx[0].tnFvCtxName), bd_node(tenant.name, bd.name))
        else: # If VRF is not attached, then create an invisible node to move BD node to the right
            tnCluster.add_node("_ctx-dummy-"+bd_node(tenant.name, bd.name), style="invis", label='Private Network', shape='circle')
            tnCluster.add_edge("_ctx-dummy-"+bd_node(tenant.name, bd.name), bd_node(tenant.name, bd.name), style="invis")



#    dnQuery = DnQuery(tenant.dn)
#    dnQuery.queryTarget = 'children'
#    childMos = moDir.query(dnQuery)
#    for Mo in childMos:
#        print(Mo.name)



moDir.logout()

print ("\nGenerating output file")
graph.draw("example.png", prog='dot')
