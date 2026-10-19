#!/usr/bin/env bash
# 노드 환경을 기록하고 RDMA가 실험망에서 동작하는지 확인한다. 결과는 실험 CSV와 함께 보관한다.
echo "== host";      hostname; date -Is; uname -r
echo "== cpu";       lscpu | grep -E 'Model name|^CPU\(s\)|NUMA node'
echo "== nic";       lspci | grep -i -E 'mellanox|connectx|broadcom|e810' || true
echo "== rdma link"; rdma link show || true
echo "== devinfo";   ibv_devinfo 2>/dev/null | grep -E 'hca_id|fw_ver|vendor_part_id|state|link_layer|active_mtu' || true
echo "== versions";  dpkg -l rdma-core perftest 2>/dev/null | awk '/^ii/{print $2,$3}'

echo "== experiment interfaces (10.10.x.x)"
for dev in $(ip -o -4 addr show | awk '$4 ~ /^10\.10\./{print $2}'); do
  echo "-- $dev $(ip -o -4 addr show dev $dev | awk '{print $4}')"
  ethtool "$dev" 2>/dev/null | grep -E 'Speed|Link detected'
  ip link show "$dev" | grep -o 'mtu [0-9]*'
  # netdev -> RDMA 장치 매핑과 NUMA 노드
  rdev=$(rdma link show | awk -v d="$dev" '$0 ~ "netdev "d"$" || $0 ~ "netdev "d" " {print $2}' | cut -d/ -f1)
  echo "rdma dev: ${rdev:-?}  numa: $(cat /sys/class/net/$dev/device/numa_node 2>/dev/null)"
  # RoCEv2 IPv4 GID 인덱스 (perftest -x 에 사용)
  if [ -n "${rdev:-}" ]; then
    for g in /sys/class/infiniband/$rdev/ports/1/gids/*; do
      i=${g##*/}; t=$(cat /sys/class/infiniband/$rdev/ports/1/gid_attrs/types/$i 2>/dev/null)
      v=$(cat "$g"); [[ "$t" == "RoCE v2" && "$v" == 0000:0000:0000:0000:0000:ffff:* ]] && echo "RoCEv2 IPv4 GID index: $i"
    done
    echo "hw_counters (일부):"
    for c in out_of_sequence packet_seq_err local_ack_timeout_err rnr_nak_retry_err; do
      f=/sys/class/infiniband/$rdev/ports/1/hw_counters/$c
      [ -r "$f" ] && echo "  $c=$(cat $f)"
    done
  fi
done
echo "== hugepages"; grep -E 'HugePages_Total|Hugepagesize' /proc/meminfo
echo "== memlock";   ulimit -l
