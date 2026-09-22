import bisect
import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Server:
    server_id: str
    host: str
    port: int


@dataclass(frozen=True)
class VirtualNode:
    server_id: str
    vnode_id: int
    hash_value: int


class ConsistentHashRing:
    def __init__(self, servers, virtual_nodes_per_server: int = 5):
        self.servers = list(servers)
        self.virtual_nodes_per_server = virtual_nodes_per_server
        self.ring = self._build_ring()
        self.hash_to_server = {entry["hash"]: entry["server_id"] for entry in self.ring}
        self.server_by_id = {server.server_id: server for server in self.servers}

    def _hash(self, value: str) -> int:
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)

    def _build_ring(self):
        ring = []
        for server in self.servers:
            for vnode_id in range(self.virtual_nodes_per_server):
                virtual_name = f"{server.server_id}:{vnode_id}"
                hash_value = self._hash(virtual_name)
                ring.append({
                    "hash": hash_value,
                    "server_id": server.server_id,
                    "server": server,
                    "vnode_id": vnode_id,
                })
        return sorted(ring, key=lambda item: item["hash"])

    def lookup_key(self, key: str) -> str:
        if not self.ring:
            raise ValueError("No servers available in the ring.")

        target_hash = self._hash(key)
        ring_hashes = [entry["hash"] for entry in self.ring]
        idx = bisect.bisect_left(ring_hashes, target_hash)

        if idx == len(ring_hashes):
            idx = 0

        return self.ring[idx]["server_id"]

    def get_server(self, key: str) -> Server:
        server_id = self.lookup_key(key)
        return self.server_by_id[server_id]

    def visualize_ring(self, limit: int = None):
        entries = self.ring if limit is None else self.ring[:limit]
        ring_str = "["
        for index, entry in enumerate(entries):
            suffix = ", " if index < len(entries) - 1 else ""
            ring_str += f"{entry['server_id']}@{entry['hash'] % 1000:03}{suffix}"
        ring_str += "]"
        return ring_str

    def vnode_counts(self):
        counts = {server.server_id: 0 for server in self.servers}
        for entry in self.ring:
            counts[entry["server_id"]] += 1
        return counts

    def add_server(self, server: Server):
        if server in self.servers:
            return self.ring

        self.servers.append(server)
        for vnode_id in range(self.virtual_nodes_per_server):
            virtual_name = f"{server.server_id}:{vnode_id}"
            hash_value = self._hash(virtual_name)
            self.ring.append({
                "hash": hash_value,
                "server_id": server.server_id,
                "server": server,
                "vnode_id": vnode_id,
            })

        # Intentionally do not rebalance existing keys here; this is just the ring update.
        self.ring.sort(key=lambda item: item["hash"])
        self.hash_to_server = {entry["hash"]: entry["server_id"] for entry in self.ring}
        self.server_by_id = {server.server_id: server for server in self.servers}
        return self.ring

    def remove_server(self, server_id: str):
        self.servers = [server for server in self.servers if server.server_id != server_id]
        self.ring = self._build_ring()
        self.hash_to_server = {entry["hash"]: entry["server_id"] for entry in self.ring}
        self.server_by_id = {server.server_id: server for server in self.servers}

    def describe_ownership(self):
        entries = []
        for index, entry in enumerate(self.ring):
            prev_hash = self.ring[index - 1]["hash"] if index > 0 else self.ring[-1]["hash"]
            entries.append(
                {
                    "slot": index,
                    "server_id": entry["server_id"],
                    "vnode": entry["vnode_id"],
                    "hash": entry["hash"],
                    "prev_hash": prev_hash,
                }
            )
        return entries


servers = [
    Server(server_id="server-1", host="cache-a", port=8001),
    Server(server_id="server-2", host="cache-b", port=8002),
    Server(server_id="server-3", host="cache-c", port=8003),
]

ring = ConsistentHashRing(servers, virtual_nodes_per_server=5)

if __name__ == "__main__":
    sample_keys = [
        "user:42",
        "order:900",
        "session:abc",
        "cache:hello",
        "profile:alice",
    ]

    print("Initial servers:")
    for server in servers:
        print(f"- {server.server_id} -> {server.host}:{server.port}")

    print("\nBefore adding a server:")
    for server_id, count in ring.vnode_counts().items():
        print(f"- {server_id}: {count} virtual nodes")

    new_server = Server(server_id="server-4", host="cache-d", port=8004)
    ring.add_server(new_server)

    print("\nAfter adding server-4:")
    for server_id, count in ring.vnode_counts().items():
        print(f"- {server_id}: {count} virtual nodes")

    print("\nHash-to-server mapping snapshot:")
    for hash_value, server_id in list(ring.hash_to_server.items())[:10]:
        print(f"{hash_value}: {server_id}")

    print("\nRing visualization (sorted by hash):")
    for index, entry in enumerate(ring.ring):
        print(f"{index:02d}: {entry['server_id']} vnode={entry['vnode_id']} hash={entry['hash']}")

    print("\nKey assignments after ring update:")
    for key in sample_keys:
        server_id = ring.lookup_key(key)
        server = ring.server_by_id[server_id]
        print(f"{key} -> {server_id} ({server.host}:{server.port})")
