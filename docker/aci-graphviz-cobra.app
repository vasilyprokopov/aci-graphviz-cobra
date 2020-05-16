# aci-graphviz-cobra.app

# Copyright: (c) 2020, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

FROM python:3.7.3-slim

COPY requirements.txt /tmp/
COPY acicobra-4.2_3l-py2.py3-none-any.whl /tmp/cobra/
COPY acimodel-4.2_3l-py2.py3-none-any.whl /tmp/cobra/

RUN apt-get update && \
    apt-get install graphviz -y && \
#
#Only on a slim image
#
    apt-get install libgraphviz-dev -y && \
    apt-get install git -y && \
#
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
#
# Cloning aci-graphviz-cobra and creating a link to let the diagram appear in the mounted volume
# Need the link because:
# Not possible to mount a volume once container has been started
# Not possible to git clone into a non-empty directory
#
    mkdir /home/out && \
    git clone https://github.com/vasilyprokopov/aci-graphviz-cobra /home/aci-graphviz-cobra && \
    rm -r /home/aci-graphviz-cobra/out/ && \
    ln -s /home/out /home/aci-graphviz-cobra && \
  #
  # Cleaning up
  #
    apt-get remove libgraphviz-dev -y && \
    apt-get remove git -y && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -r /tmp/cobra && \
#
    find /usr/local/lib/python3.7/site-packages/cobra/modelimpl/ | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf && \
#
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/l2 && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/bgp && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/ospf && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/aaa && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/fc && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/copp && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/eqptcapacity && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/condition && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/cloud && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/latency && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/stats && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/fhs && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/pcons && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/opflex && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/l1 && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/isis && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/fault && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/eqpt && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/action && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/fabric && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/traceroute && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/ping && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/hcloud && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/infra && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/coop && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/callhome && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/tunnel && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/telemetry && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/analytics && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/oam && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/cloudsec && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/sla && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/dpp && \
    rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/eptrk
