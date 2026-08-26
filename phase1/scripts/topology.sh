#!/bin/bash
set -e

for ns in s1 s2 r1 sw; do
    sudo ip netns del $ns 2>/dev/null || true
done

sudo ip netns add s1
sudo ip netns add s2
sudo ip netns add r1
sudo ip netns add sw

sudo ip link add veth-s1 type veth peer name veth-sw1
sudo ip link add veth-s2 type veth peer name veth-sw2
sudo ip link add veth-r1 type veth peer name veth-swr

sudo ip link set veth-s1 netns s1
sudo ip link set veth-sw1 netns sw
sudo ip link set veth-s2 netns s2
sudo ip link set veth-sw2 netns sw
sudo ip link set veth-r1 netns r1
sudo ip link set veth-swr netns sw

sudo ip netns exec s1 ip addr add 10.0.1.1/24 dev veth-s1
sudo ip netns exec s2 ip addr add 10.0.2.1/24 dev veth-s2
sudo ip netns exec r1 ip addr add 10.0.3.1/24 dev veth-r1

sudo ip netns exec sw ip addr add 10.0.1.254/24 dev veth-sw1
sudo ip netns exec sw ip addr add 10.0.2.254/24 dev veth-sw2
sudo ip netns exec sw ip addr add 10.0.3.254/24 dev veth-swr

for ns in s1 s2 r1 sw; do
    sudo ip netns exec $ns ip link set lo up
done

sudo ip netns exec s1 ip link set veth-s1 up
sudo ip netns exec s2 ip link set veth-s2 up
sudo ip netns exec r1 ip link set veth-r1 up
sudo ip netns exec sw ip link set veth-sw1 up
sudo ip netns exec sw ip link set veth-sw2 up
sudo ip netns exec sw ip link set veth-swr up

sudo ip netns exec s1 ip route add default via 10.0.1.254
sudo ip netns exec s2 ip route add default via 10.0.2.254
sudo ip netns exec r1 ip route add default via 10.0.3.254

sudo ip netns exec sw sysctl -w net.ipv4.ip_forward=1 >/dev/null

echo "Topology created successfully."