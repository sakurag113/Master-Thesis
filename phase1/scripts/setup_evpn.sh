#!/bin/bash

set -e

echo "=== Cleaning old namespaces ==="

for ns in h1 h2 leaf1 leaf2 spine; do
    ip netns del $ns 2>/dev/null || true
done


echo "=== Creating namespaces ==="

for ns in h1 h2 leaf1 leaf2 spine; do
    ip netns add $ns
    ip netns exec $ns ip link set lo up
done


echo "=== Creating veth links ==="

ip link add h1-eth0 type veth peer name l1-host
ip link set h1-eth0 netns h1
ip link set l1-host netns leaf1

ip link add l1-spine type veth peer name sp-l1
ip link set l1-spine netns leaf1
ip link set sp-l1 netns spine

ip link add sp-l2 type veth peer name l2-spine
ip link set sp-l2 netns spine
ip link set l2-spine netns leaf2

ip link add l2-host type veth peer name h2-eth0
ip link set l2-host netns leaf2
ip link set h2-eth0 netns h2


echo "=== Configuring underlay IP addresses ==="

ip netns exec leaf1 ip addr add 10.0.1.1/30 dev l1-spine
ip netns exec leaf1 ip addr add 1.1.1.1/32 dev lo
ip netns exec leaf1 ip link set l1-spine up
ip netns exec leaf1 ip link set l1-host up

ip netns exec spine ip addr add 10.0.1.2/30 dev sp-l1
ip netns exec spine ip addr add 10.0.2.1/30 dev sp-l2
ip netns exec spine ip addr add 10.255.255.254/32 dev lo
ip netns exec spine ip link set sp-l1 up
ip netns exec spine ip link set sp-l2 up

ip netns exec leaf2 ip addr add 10.0.2.2/30 dev l2-spine
ip netns exec leaf2 ip addr add 2.2.2.2/32 dev lo
ip netns exec leaf2 ip link set l2-spine up
ip netns exec leaf2 ip link set l2-host up


echo "=== Configuring host IP addresses ==="

ip netns exec h1 ip addr add 192.168.100.11/24 dev h1-eth0
ip netns exec h1 ip link set h1-eth0 up

ip netns exec h2 ip addr add 192.168.100.22/24 dev h2-eth0
ip netns exec h2 ip link set h2-eth0 up


echo "=== Creating bridges ==="

ip netns exec leaf1 ip link add br100 type bridge
ip netns exec leaf1 ip link set br100 up
ip netns exec leaf1 ip link set l1-host master br100

ip netns exec leaf2 ip link add br100 type bridge
ip netns exec leaf2 ip link set br100 up
ip netns exec leaf2 ip link set l2-host master br100


echo "=== Creating VXLAN interfaces ==="

ip netns exec leaf1 ip link add vxlan100 \
    type vxlan id 100 \
    local 1.1.1.1 \
    dstport 4789 \
    nolearning

ip netns exec leaf1 ip link set vxlan100 master br100
ip netns exec leaf1 ip link set vxlan100 up

ip netns exec leaf2 ip link add vxlan100 \
    type vxlan id 100 \
    local 2.2.2.2 \
    dstport 4789 \
    nolearning

ip netns exec leaf2 ip link set vxlan100 master br100
ip netns exec leaf2 ip link set vxlan100 up


echo "=== Enabling IPv4 forwarding on spine ==="

ip netns exec spine sysctl -w net.ipv4.ip_forward=1


echo "=== Starting FRR ==="

/usr/lib/frr/frrinit.sh stop leaf1 2>/dev/null || true
/usr/lib/frr/frrinit.sh stop spine 2>/dev/null || true
/usr/lib/frr/frrinit.sh stop leaf2 2>/dev/null || true

/usr/lib/frr/frrinit.sh start leaf1
/usr/lib/frr/frrinit.sh start spine
/usr/lib/frr/frrinit.sh start leaf2


echo "=== Waiting for BGP ==="

sleep 5


echo "=== Adding bottleneck ==="

ip netns exec spine tc qdisc del dev sp-l2 root 2>/dev/null || true

ip netns exec spine tc qdisc add dev sp-l2 root tbf \
    rate 10mbit \
    burst 65536 \
    latency 50ms


echo "=== Verification ==="

echo "--- Namespaces ---"
ip netns list

echo
echo "--- BGP summary on spine ---"
vtysh -N spine -c "show bgp summary" || true

echo
echo "--- VTEP connectivity ---"
ip netns exec leaf1 ping -I 1.1.1.1 -c 2 2.2.2.2 || true

echo
echo "--- Overlay connectivity ---"
ip netns exec h1 ping -c 3 192.168.100.22 || true

echo
echo "--- Bottleneck ---"
ip netns exec spine tc qdisc show dev sp-l2

echo
echo "=== EVPN/VXLAN setup finished ==="