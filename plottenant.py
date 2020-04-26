#!/usr/bin/env python

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from cobra.mit.request import DnQuery
from cobra.mit.request import ClassQuery

import pygraphviz


# Defining nodes for Tenant
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

def external_epg_node(tn, l3out, exEpg):
    return l3out_node(tn, l3out)+"/external-epg-"+exEpg

def ctrctIf_node(ctrctIf):
    return "global-ctrctIf-"+ctrctIf # In the global graph space, because needs to be shared between Tenants


# Defining Plot Tenant function
# It will accept Tenant name, graph that this tenant should be part of, and inherit session to the APIC - moDir
def plot_tenant(tenant, graph, moDir):
    print("Processing Tenant "+tenant.name)

    # Plot a Tenant
    tnCluster = graph.add_subgraph(name=tn_node(tenant.name), label="Tenant\n"+tenant.name, color="steelblue")


    # Process Contracts
    # Standard and Contract Interfaces

    # Create separate subgraph for Unused Contracts that belong to the Tenant
    unusedCtrctCluster=tnCluster.add_subgraph(name=ctrct_node(tenant.name, "unused"), label="Unused Contracts")

    # Query all Standard Contracts that belong to the Tenant
    ctrctQuery = ClassQuery(str(tenant.dn)+"/vzBrCP") # Creating a query for Contracts, that takes "uni/tn-graphviz/vzBrCP" as a Class input
    vzBrCP = moDir.query(ctrctQuery) # Executing a query that was created
    for ctrct in vzBrCP:

        # Check if contract is unused i.e. doesn't have any child MOs indicating that the Contract is associated
        ctrctChildrenQuery = DnQuery(ctrct.dn)
        ctrctChildrenQuery.queryTarget = "subtree" # Quering only children of Contract MO
        ctrctChildrenQuery.classFilter = "vzRtProv,vzRtCons,vzRtAnyToProv,vzRtAnyToCons,vzRtIf" # Quering only certain classes among children MOs
        ctrctChildren = moDir.query(ctrctChildrenQuery)

        # If none of the listed classes present, then Contract is not assosiated and hence unused
        if not ctrctChildren:
            unusedCtrctCluster.add_node(ctrct_node(tenant.name, ctrct.name), label="Unused Contract\n"+ctrct.name+"\n Scope: "+ctrct.scope, shape='box', style='filled', color='coral2')
            continue # Continue to the next iteration of the For loop (next Contract, please)


        # Plot a contract
        # Check if currrently proccessed tenant is "common"
        if tenant.name == "common":
            # If tenant "common", then mark the plotted object
            tnCluster.add_node(ctrct_node(tenant.name, ctrct.name), label="Common Contract\n"+ctrct.name+"\n Scope: "+ctrct.scope, shape='box', style='filled', color='darkseagreen')
        else:
            # If tenant is not "common", then don't mark the plotted object
            tnCluster.add_node(ctrct_node(tenant.name, ctrct.name), label="Contract\n"+ctrct.name+"\n Scope: "+ctrct.scope, shape='box', style='filled', color='lightgrey')


        # Check if a Contract is exported to other Tenants by quering all Conract Interfaces that belong to this Contract, if any
        ctrctIfQuery = ClassQuery(str(ctrct.dn)+"/vzRtIf")
        vzRtIf = moDir.query(ctrctIfQuery)

        for ctrctIf in vzRtIf: # Check if Contract Interface is indeed present
            if ctrctIf.tDn: #
                i = ctrctIf.tDn.rfind("/cif-")+5 # In tDn we need to find the index where "cif-" ends
                ctrctIfName = ctrctIf.tDn[i : : ] # Taking everythin starting from index i to the end of the string, and stripping the beggining before i

                # Plot Contract Interface in the gloabal graph space
                tnCluster.add_node(ctrctIf_node(ctrctIfName), label="Contract Interface\n"+ctrctIfName, shape='box', style='filled', color='lightgray')

                # Plot Contract to Contract Interface association
                if ctrct.scope == "global": # Check if Contract scope is Global
                    tnCluster.add_edge(ctrct_node(tenant.name, ctrct.name), ctrctIf_node(ctrctIfName), label="inter-tenant p")
                else:
                    tnCluster.add_edge(ctrct_node(tenant.name, ctrct.name), ctrctIf_node(ctrctIfName), label="inter-tenant p\nChange scope to global!", style="dotted", color="indianred3")


    # Process VRFs
    # Query all VRFs that belong to the Tenant
    vrfQuery = ClassQuery(str(tenant.dn)+"/fvCtx") # Creating a query for VRFs, that takes "uni/tn-graphviz/fvCtx" as a Class input
    fvCtx = moDir.query(vrfQuery)

    for ctx in fvCtx:

        # Plot a VRF
        # Check if currrently proccessed tenant is "common"
        if tenant.name == "common":
            # If tenant "common", then mark the plotted object
            tnCluster.add_node(ctx_node(tenant.name, ctx.name), label="Common VRF\n"+ctx.name, shape='circle', style='filled', color='darkseagreen')
        else:
            # If tenant is not "common", then don't mark the plotted object
            tnCluster.add_node(ctx_node(tenant.name, ctx.name), label="VRF\n"+ctx.name, shape='circle')


        # Plot Contracts (vzAny) provided by this VRF, if any
        # Query what Contracts this VRF provides
        pcQuery = ClassQuery(str(ctx.dn)+"/any/vzRsAnyToProv") # Provided Contract will have a child MO "vzRsAnyToProv"
        vzRsAnyToProv = moDir.query(pcQuery)

        for pc in vzRsAnyToProv:

            # Check if Provided Contract (vzAny) comes from tenant Common
            if "/tn-common/" in pc.tDn and tenant.name != "common":
                ctrctTenant = "common" # If Provided Contract comes from tenant Common, replace tenant.name to "common"

                # Plot Contract from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                graph.add_node(ctrct_node(ctrctTenant,pc.tnVzBrCPName), label="Common Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='darkseagreen')

            else:
                ctrctTenant = tenant.name # If Provided Contract does not come from tenant Common, leave tenant.name unchanged


            if pc.state == "formed": # Check if contract exists

                # Plot Provided Contract to VRF association
                tnCluster.add_edge(ctx_node(tenant.name, ctx.name), ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="vzAny p")

            elif pc.state == "missing-target": # Check if contract is missing

                # Plot Missing Contract
                tnCluster.add_node(ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="Missing Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                # Plot Missing Contract to VRF association
                tnCluster.add_edge(ctx_node(tenant.name, ctx.name), ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="vzAny p")


        # Plot Contracts (vzAny) consumed by this VRF, if any
        # Query what Contracts this VRF consumes
        ccQuery = ClassQuery(str(ctx.dn)+"/any/vzRsAnyToCons") # Consumed Contract will have a child MO "/any/vzRsAnyToCons"
        vzRsAnyToCons = moDir.query(ccQuery)

        for cc in vzRsAnyToCons:

            # Check if Consumed Contract (vzAny) comes from tenant Common
            if "/tn-common/" in cc.tDn and tenant.name != "common":
                ctrctTenant = "common" # If Consumed Contract comes from tenant Common, replace tenant.name to "common"

                # Plot Contract from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                graph.add_node(ctrct_node(ctrctTenant,cc.tnVzBrCPName), label="Common Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='darkseagreen')

            else:
                ctrctTenant = tenant.name # If Consumed Contract does not come from tenant Common, leave tenant.name unchanged


            if cc.state == "formed": # Check if contract exists

                # Plot Consumed Contract to VRF association
                tnCluster.add_edge(ctrct_node(ctrctTenant, cc.tnVzBrCPName), ctx_node(tenant.name, ctx.name), label="vzAny c")

            elif cc.state == "missing-target": # Check if contract is missing

                # Plot Missing Contract
                tnCluster.add_node(ctrct_node(ctrctTenant, cc.tnVzBrCPName), label="Missing Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                # Plot Missing Contract to VRF association
                tnCluster.add_edge(ctrct_node(ctrctTenant, cc.tnVzBrCPName), ctx_node(tenant.name, ctx.name), label="vzAny c")


        # Plot Contract Interfaces (vzAny) consumed by this VRF, if any
        # Query what Contract Interfaces this VRF consumes
        ccQuery = ClassQuery(str(ctx.dn)+"/any/vzRsAnyToConsIf") # Consumed Contract Interface will have a child MO "/any/vzRsAnyToConsIf"
        vzRsAnyToConsIf = moDir.query(ccQuery)

        for cc in vzRsAnyToConsIf:
            if cc.state == "formed": # Check if Contract Interface exists

                # Plot Consumed Contract Interface in the gloabal graph space
                tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='lightgray')

                # Plot Consumed Contract Interface to exEPG association
                tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), ctx_node(tenant.name, ctx.name), label="inter-tenant vzAny c")

            elif cc.state == "missing-target": # Check if contract is missing

                # Plot Missing Contract Interface in the gloabal graph space
                tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Missing Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='coral2')

                # Plot Missing Contract Interface to exEPG association
                tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), ctx_node(tenant.name, ctx.name), label="inter-tenant vzAny c")


    # Process L3Outs
    # Query all L3Outs that belong to the Tenant
    l3OutQuery = ClassQuery(str(tenant.dn)+"/l3extOut")
    l3extOut = moDir.query(l3OutQuery)

    for l3out in l3extOut:

        # Create separate subgraph per each L3Out that belongs to the Tenant
        l3outCluster=tnCluster.add_subgraph(name=l3out_node(tenant.name, l3out.name), label="L3Out")

        # Plot L3Out within its subgraph

        # Check if currrently proccessed tenant is "common"
        if tenant.name == "common":
            # If tenant "common", then mark the plotted object
            l3outCluster.add_node(l3out_node(tenant.name, l3out.name), label = "Common L3Out\n"+l3out.name, shape='box', style='filled', color='darkseagreen')
        else:
            # If tenant is not "common", then don't mark the plotted object
            l3outCluster.add_node(l3out_node(tenant.name, l3out.name), label = "L3Out\n"+l3out.name, shape='box')


        # Query what VRF this L3Out attaches to
        ctxQuery = ClassQuery(str(l3out.dn)+"/l3extRsEctx") # If there is a VRF attached, L3Out will have a child MO "l3extRsEctx"
        attachedCtx = moDir.query(ctxQuery)


        # Plot L3Out to VRF association, if any
        for ctx in attachedCtx:
            if ctx.tnFvCtxName: # Verify if there is indeed VRF attached
                tnCluster.add_edge(ctx_node(tenant.name, ctx.tnFvCtxName), l3out_node(tenant.name,l3out.name), style='dotted') # The name of attached VRF is in attribute "tnFvCtxName"


        # Plot External EPGs (exEPG)
        # Query all exEPGs that belong to the L3Out
        exEpgQuery = ClassQuery(str(l3out.dn)+"/l3extInstP")
        l3extInstP = moDir.query(exEpgQuery)

        for exEpg in l3extInstP:
            # Construct a label that includes Subnets
            label = "External EPG\n"+exEpg.name
            subnetQuery = ClassQuery(str(exEpg.dn)+"/l3extSubnet")
            fvSubnet = moDir.query(subnetQuery)
            for subnet in fvSubnet:
                label = label+"\n"+subnet.ip


            # Plot exEPG
            l3outCluster.add_node(external_epg_node(tenant.name, l3out.name, exEpg.name), label=label)


            # Plot exEPG to L3Out association
            l3outCluster.add_edge(l3out_node(tenant.name, l3out.name), external_epg_node(tenant.name, l3out.name, exEpg.name))


            # Plot Contracts provided by this exEPG, if any
            # Query what Contracts this exEPG provides
            pcQuery = ClassQuery(str(exEpg.dn)+"/fvRsProv") # Provided Contract will have a child MO "fvRsProv"
            fvRsProv = moDir.query(pcQuery)

            for pc in fvRsProv:

                # Check if Provided Contract comes from tenant Common
                if "/tn-common/" in pc.tDn and tenant.name != "common":
                    ctrctTenant = "common" # If Provided Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot Contract from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(ctrct_node(ctrctTenant,pc.tnVzBrCPName), label="Common Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='darkseagreen')

                else:
                    ctrctTenant = tenant.name # If Provided Contract does not come from tenant Common, leave tenant.name unchanged


                if pc.state == "formed": # Check if contract exists

                    # Plot Provided Contract to exEPG association
                    l3outCluster.add_edge(external_epg_node(tenant.name, l3out.name, exEpg.name), ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="p")

                elif pc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    l3outCluster.add_node(ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="Missing Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to exEPG association
                    l3outCluster.add_edge(external_epg_node(tenant.name, l3out.name, exEpg.name), ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="p")


            # Plot Contracts consumed by this exEPG, if any
            # Query what Contracts this exEPG consumes
            ccQuery = ClassQuery(str(exEpg.dn)+"/fvRsCons") # Consumed Contract will have a child MO "fvRsCons"
            fvRsCons = moDir.query(ccQuery)

            for cc in fvRsCons:

                # Check if Consumed Contract comes from tenant Common
                if "/tn-common/" in cc.tDn and tenant.name != "common":
                    ctrctTenant = "common" # If Consumed Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot Contract from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(ctrct_node(ctrctTenant,cc.tnVzBrCPName), label="Common Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='darkseagreen')

                else:
                    ctrctTenant = tenant.name # If Consumed Contract does not come from tenant Common, leave tenant.name unchanged


                if cc.state == "formed": # Check if contract exists

                    # Plot Consumed Contract to exEPG association
                    l3outCluster.add_edge(ctrct_node(ctrctTenant, cc.tnVzBrCPName), external_epg_node(tenant.name, l3out.name, exEpg.name), label="c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    l3outCluster.add_node(ctrct_node(ctrctTenant, cc.tnVzBrCPName), label="Missing Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to exEPG association
                    l3outCluster.add_edge(ctrct_node(ctrctTenant, cc.tnVzBrCPName), external_epg_node(tenant.name, l3out.name, exEpg.name), label="c")


            # Plot Contract Interfaces consumed by this exEPG, if any
            # Query what Contract Interfaces this exEPG consumes
            ccQuery = ClassQuery(str(exEpg.dn)+"/fvRsConsIf") # Consumed Contract Interface will have a child MO "fvRsConsIf"
            fvRsConsIf = moDir.query(ccQuery)

            for cc in fvRsConsIf:
                if cc.state == "formed": # Check if Contract Interface exists

                    # Plot Consumed Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='lightgray')

                    # Plot Consumed Contract Interface to exEPG association
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), external_epg_node(tenant.name, l3out.name, exEpg.name), label="inter-tenant c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Missing Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract Interface to exEPG association
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), external_epg_node(tenant.name, l3out.name, exEpg.name), label="inter-tenant c")


    # Process BDs
    # Query all BDs that belong to the Tenant
    bdQuery = ClassQuery(str(tenant.dn)+"/fvBD")
    fvBD = moDir.query(bdQuery)

    for bd in fvBD:
        # Construct a label that includes Subnets
        if bd.unicastRoute == "yes": # Check if BD is L3 BD
            label = "Bridge Domain L3\n"+bd.name
        elif bd.unicastRoute == "no": # Check if BD is L2 BD
            label = "Bridge Domain L2\n"+bd.name
        subnetQuery = ClassQuery(str(bd.dn)+"/fvSubnet")
        fvSubnet = moDir.query(subnetQuery)
        for subnet in fvSubnet:
            label = label+"\n"+subnet.ip


        # Plot a BD
        # Check if currrently proccessed tenant is "common"
        if tenant.name == "common":
            # If tenant "common", then mark the plotted object
            tnCluster.add_node(bd_node(tenant.name, bd.name), label="Common "+label, shape='box', style='filled', color='darkseagreen')
        else:
            # If tenant is not "common", then don't mark the plotted object
            tnCluster.add_node(bd_node(tenant.name, bd.name), label=label, shape='box')


        # Query what VRF this BD attaches to
        ctxQuery = ClassQuery(str(bd.dn)+"/fvRsCtx") # If there is a VRF attached, BD will have a child MO "fvRsCtx"
        attachedCtx = moDir.query(ctxQuery)


        # Plot BD to VRF association, if any
        for ctx in attachedCtx:
            if ctx.tnFvCtxName: # Verify if there is indeed VRF attached (or maybe several VRFs in the future)

                # Check if VRF comes from tenant Common
                if "/tn-common/" in ctx.tDn and tenant.name != "common":
                    vrfTenant = "common" # If Consumed Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot VRF from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(ctx_node(vrfTenant, ctx.tnFvCtxName), label="Common VRF\n"+ctx.tnFvCtxName, shape='circle', style='filled', color='darkseagreen')
                else:
                    vrfTenant = tenant.name # If Consumed Contract does not come from tenant Common, leave tenant.name unchanged

                # Plot BD to VRF association
                tnCluster.add_edge(ctx_node(vrfTenant, ctx.tnFvCtxName), bd_node(tenant.name, bd.name))

            else: # If VRF is not attached, then create an invisible node to move BD to the right
                tnCluster.add_node("_ctx-dummy-"+bd_node(tenant.name, bd.name), style="invis", label='Dummy Context', shape='circle')
                tnCluster.add_edge("_ctx-dummy-"+bd_node(tenant.name, bd.name), bd_node(tenant.name, bd.name), style="invis")


        # Query what L3Outs this BD attaches to
        l3OutQuery = ClassQuery(str(bd.dn)+"/fvRsBDToOut") # If there is a L3Out attached, BD will have a child MO "fvRsBDToOut"
        attachedL3Out = moDir.query(l3OutQuery)


        # Plot BD to L3Out association, if any
        for l3out in attachedL3Out:
            if l3out.tnL3extOutName: # Verify if there is indeed a L3Out attached

                # Check if L3Out comes from tenant Common
                if "/tn-common/" in l3out.tDn and tenant.name != "common":
                    l3outTenant = "common" # If Consumed Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot L3Out from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(l3out_node(l3outTenant, l3out.tnL3extOutName), label = "Common L3Out\n"+l3out.tnL3extOutName, shape='box', style='filled', color='darkseagreen')
                else:
                    l3outTenant = tenant.name # If Consumed Contract does not come from tenant Common, leave tenant.name unchanged

                # Plot BD to L3Out association
                tnCluster.add_edge(bd_node(tenant.name, bd.name), l3out_node(l3outTenant,l3out.tnL3extOutName), style='dotted') # The name of attached L3Out is in attribute "tnL3extOutName"


    # Process Application Profiles (APs)
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


            # Plot EPG to BD association
            # Query what BD this EPG attaches to
            bdQuery = ClassQuery(str(epg.dn)+"/fvRsBd") # BD will have a child MO "fvRsBd"
            attachedBd = moDir.query(bdQuery)
            for bd in attachedBd:

                # Check if BD comes from tenant Common
                if "/tn-common/" in bd.tDn and tenant.name != "common":
                    bdTenant = "common" # If Consumed Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot VRF from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(bd_node(bdTenant, bd.tnFvBDName), label="Common Bridge Domain\n"+bd.tnFvBDName, shape='box', style='filled', color='darkseagreen')
                else:
                    bdTenant = tenant.name # If Consumed Contract does not come from tenant Common, leave tenant.name unchanged

                tnCluster.add_edge(bd_node(bdTenant, bd.tnFvBDName), epg_node(tenant.name, ap.name, epg.name), style='dotted')


            # Plot Contracts provided by this EPG, if any
            # Query what Contracts this EPG provides
            pcQuery = ClassQuery(str(epg.dn)+"/fvRsProv") # Provided Contract will have a child MO "fvRsProv"
            fvRsProv = moDir.query(pcQuery)

            for pc in fvRsProv:

                # Check if Provided Contract comes from tenant Common
                if "/tn-common/" in pc.tDn and tenant.name != "common":
                    ctrctTenant = "common" # If Provided Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot Contract from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(ctrct_node(ctrctTenant,pc.tnVzBrCPName), label="Common Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='darkseagreen')

                else:
                    ctrctTenant = tenant.name # If Provided Contract does not come from tenant Common, leave tenant.name unchanged


                if pc.state == "formed": # Check if contract is indeed present

                    # Plot Provided Contract to EPG association
                    apCluster.add_edge(epg_node(tenant.name, ap.name, epg.name), ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="p")

                elif pc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    apCluster.add_node(ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="Missing Contract\n"+pc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to EPG association
                    apCluster.add_edge(epg_node(tenant.name, ap.name, epg.name), ctrct_node(ctrctTenant, pc.tnVzBrCPName), label="p")


            # Plot Contracts consumed by this EPG, if any
            # Query what Contracts this EPG consumes
            ccQuery = ClassQuery(str(epg.dn)+"/fvRsCons") # Consumed Contract will have a child MO "fvRsCons"
            fvRsCons = moDir.query(ccQuery)

            for cc in fvRsCons:

                # Check if Consumed Contract comes from tenant Common
                if "/tn-common/" in cc.tDn and tenant.name != "common":
                    ctrctTenant = "common" # If Consumed Contract comes from tenant Common, replace tenant.name to "common"

                    # Plot Contract from tenant Common in the gloabal graph space, in case tenant Common itself is excluded from plotting
                    graph.add_node(ctrct_node(ctrctTenant,cc.tnVzBrCPName), label="Common Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='darkseagreen')


                if cc.state == "formed": # Check if contract exists

                    # Plot Consumed Contract to EPG association
                    apCluster.add_edge(ctrct_node(ctrctTenant, cc.tnVzBrCPName), epg_node(tenant.name, ap.name, epg.name), label="c")


                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract
                    apCluster.add_node(ctrct_node(ctrctTenant, cc.tnVzBrCPName), label="Missing Contract\n"+cc.tnVzBrCPName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract to EPG association
                    apCluster.add_edge(ctrct_node(ctrctTenant, cc.tnVzBrCPName), epg_node(tenant.name, ap.name, epg.name), label="c")


            # Plot Contract Interfaces consumed by this EPG, if any
            # Query what Contract Interfaces this EPG consumes
            ccQuery = ClassQuery(str(epg.dn)+"/fvRsConsIf") # Consumed Contract Interface will have a child MO "fvRsConsIf"
            fvRsConsIf = moDir.query(ccQuery)

            for cc in fvRsConsIf:
                if cc.state == "formed": # Check if Contract Interface exists

                    # Plot Consumed Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='lightgray')

                    # Plot Consumed Contract Interface to EPG association
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), epg_node(tenant.name, ap.name, epg.name), label="inter-tenant c")

                elif cc.state == "missing-target": # Check if contract is missing

                    # Plot Missing Contract Interface in the gloabal graph space
                    tnCluster.add_node(ctrctIf_node(cc.tnVzCPIfName), label="Missing Contract Interface\n"+cc.tnVzCPIfName, shape='box', style='filled', color='coral2')

                    # Plot Missing Contract Interface to EPG association
                    tnCluster.add_edge(ctrctIf_node(cc.tnVzCPIfName), epg_node(tenant.name, ap.name, epg.name), label="inter-tenant c")

# End of Plot Tenant function
