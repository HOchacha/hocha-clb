"""RDMA throughput experiments: N bare-metal nodes on one (or two) experiment LANs.

Repository-based profile: this repo is cloned to /local/repository on every node.
Keep this file ASCII-only (CloudLab runs geni-lib profiles with Python 2).
"""
import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab  # provides node.hardware_type

pc = portal.Context()

pc.defineParameter("n", "Number of nodes", portal.ParameterType.INTEGER, 2)
pc.defineParameter("hw", "Node type (e.g. d6515, c6525-100g, r6525, xl170)",
                   portal.ParameterType.NODETYPE, "d6515")
pc.defineParameter("image", "Disk image",
                   portal.ParameterType.IMAGE,
                   "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD")
pc.defineParameter("bw", "LAN bandwidth in Kbps (100000000 = 100G port)",
                   portal.ParameterType.BANDWIDTH, 100000000)
pc.defineParameter("dual", "Add a second LAN on the other NIC port (other-port control)",
                   portal.ParameterType.BOOLEAN, False)
pc.defineParameter("disk", "Size of /mydata blockstore", portal.ParameterType.STRING, "100GB")

params = pc.bindParameters()
if params.n < 2:
    pc.reportError(portal.ParameterError("Need at least 2 nodes", ["n"]))
pc.verifyParameters()

request = pc.makeRequestRSpec()

lans = []
for k in range(2 if params.dual else 1):
    lan = request.LAN("lan%d" % k)
    lan.bandwidth = params.bw
    lan.setNoBandwidthShaping()   # physical link as-is, no shaping
    lans.append(lan)

for i in range(params.n):
    node = request.RawPC("node%d" % i)          # bare metal, not a VM
    node.hardware_type = params.hw
    node.disk_image = params.image
    for k, lan in enumerate(lans):
        iface = node.addInterface("if%d" % k)
        iface.addAddress(pg.IPv4Address("10.10.%d.%d" % (k + 1, i + 1), "255.255.255.0"))
        lan.addInterface(iface)
    bs = node.Blockstore("bs%d" % i, "/mydata")  # results; deleted when the experiment ends
    bs.size = params.disk
    node.addService(pg.Execute(
        shell="bash",
        command="sudo bash /local/repository/setup.sh > /tmp/setup.log 2>&1"))

pc.printRequestRSpec(request)
