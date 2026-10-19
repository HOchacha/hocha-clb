#!/usr/bin/env bash
# 부팅 시마다 실행된다(Execute 서비스). 여러 번 실행돼도 안전하게 작성한다.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y rdma-core ibverbs-utils rdmacm-utils perftest infiniband-diags \
  libibverbs-dev librdmacm-dev ethtool numactl pciutils jq python3-pip \
  linux-tools-common "linux-tools-$(uname -r)" || true

# MR 등록에 필요: 잠금 메모리 한도 해제
cat > /etc/security/limits.d/99-rdma.conf <<'EOF'
* soft memlock unlimited
* hard memlock unlimited
EOF

# 측정 잡음 줄이기: CPU 성능 모드, irqbalance 중지
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  [ -w "$g" ] && echo performance > "$g" || true
done
systemctl stop irqbalance 2>/dev/null || true

# 2MB hugepage (주소 변환 캐시 대조군용). 크기는 실험에 맞게 조정
echo 8192 > /proc/sys/vm/nr_hugepages || true

mkdir -p /mydata/results
chmod 777 /mydata /mydata/results
bash /local/repository/verify.sh > /mydata/results/env-$(hostname -s).txt 2>&1 || true
