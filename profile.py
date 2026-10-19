"""RDMA 처리량 실험용 CloudLab 프로필.

같은 클러스터의 베어메탈 노드 N대를 실험망 LAN 하나(선택 시 두 개)로 묶는다.
저장소 기반 프로필로 쓰면 이 저장소가 각 노드의 /local/repository 에 복제된다.
"""
import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab  # hardware_type 등 Emulab 확장

pc = portal.Context()

pc.defineParameter("n", "노드 수", portal.ParameterType.INTEGER, 2)
pc.defineParameter("hw", "노드 타입 (예: d6515, c6525-100g, r6525, xl170)",
                   portal.ParameterType.NODETYPE, "d6515")
pc.defineParameter("image", "디스크 이미지",
                   portal.ParameterType.IMAGE,
                   "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD")
pc.defineParameter("bw", "LAN 대역폭 (Kbps). 100G 포트를 잡으려면 100000000",
                   portal.ParameterType.BANDWIDTH, 100000000)
pc.defineParameter("dual", "두 번째 LAN 추가 (d6515처럼 100G 포트가 둘인 노드에서 '다른 포트' 대조군용)",
                   portal.ParameterType.BOOLEAN, False)
pc.defineParameter("disk", "/mydata 블록스토어 크기", portal.ParameterType.STRING, "100GB")

params = pc.bindParameters()
if params.n < 2:
    pc.reportError(portal.ParameterError("노드는 2대 이상이어야 한다", ["n"]))
pc.verifyParameters()

request = pc.makeRequestRSpec()

lans = []
for k in range(2 if params.dual else 1):
    lan = request.LAN("lan%d" % k)
    lan.bandwidth = params.bw
    lan.setNoBandwidthShaping()   # 지연 노드·셰이핑 없이 물리 링크 그대로
    lans.append(lan)

for i in range(params.n):
    node = request.RawPC("node%d" % i)          # 베어메탈 (VM 아님)
    node.hardware_type = params.hw
    node.disk_image = params.image
    for k, lan in enumerate(lans):
        iface = node.addInterface("if%d" % k)
        iface.addAddress(pg.IPv4Address("10.10.%d.%d" % (k + 1, i + 1), "255.255.255.0"))
        lan.addInterface(iface)
    bs = node.Blockstore("bs%d" % i, "/mydata")  # 결과 저장용 (실험 종료 시 사라진다)
    bs.size = params.disk
    node.addService(pg.Execute(
        shell="bash",
        command="sudo bash /local/repository/setup.sh > /tmp/setup.log 2>&1"))

pc.printRequestRSpec(request)
