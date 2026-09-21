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

    def _hash(self, value: str) -> int:
        return int(hashlib.sha1(value.encode("utf-8")).hexdigest(), 16)

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

    def get_server(self, key: str) -> Server:
        if not self.ring:
            raise ValueError("No servers available in the ring.")

        target_hash = self._hash(key)

        for entry in self.ring:
            if target_hash <= entry["hash"]:
                return entry["server"]

        return self.ring[0]["server"]

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
        if server not in self.servers:
            self.servers.append(server)
            self.ring = self._build_ring()

    def remove_server(self, server_id: str):
        self.servers = [server for server in self.servers if server.server_id != server_id]
        self.ring = self._build_ring()

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

    print("Servers:")
    for server in servers:
        print(f"- {server.server_id} -> {server.host}:{server.port}")

    print("\nVirtual node counts per server:")
    for server_id, count in ring.vnode_counts().items():
        print(f"- {server_id}: {count} virtual nodes")

    print("\nRing visualization (sorted by hash):")
    for index, entry in enumerate(ring.ring[:12]):
        print(f"{index:02d}: {entry['server_id']} vnode={entry['vnode_id']} hash={entry['hash']}")

    print("\nOwnership summary:")
    for index, entry in enumerate(ring.ring[:12]):
        previous_hash = ring.ring[index - 1]["hash"] if index > 0 else ring.ring[-1]["hash"]
        print(f"slot {index:02d}: {entry['server_id']} handles hashes > {previous_hash} and <= {entry['hash']}")

    print("\nKey assignments:")
    for key in sample_keys:
        server = ring.get_server(key)
        print(f"{key} -> {server.server_id} ({server.host}:{server.port})")

    print("\nCompact ring preview:")
    print(ring.visualize_ring(limit=12))
