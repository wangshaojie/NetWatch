"""
Port Connection Model
Data model for network connections
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PortConnection:
    """Represents a single port connection"""
    protocol: str          # TCP or UDP
    local_address: str     # Local IP address
    local_port: int        # Local port number
    remote_address: str    # Remote IP address (if connected)
    remote_port: int       # Remote port (if connected)
    status: str           # Connection state
    pid: int              # Process ID
    process_name: str      # Process name
    process_path: str      # Full path to process executable
    cpu_percent: float     # CPU usage %
    memory_percent: float  # Memory usage %
    memory_mb: float       # Memory usage in MB

    def matches_search(self, query: str) -> bool:
        """Check if this connection matches the search query (port only, fuzzy)"""
        query = query.strip()
        if not query:
            return True
        # Only match local_port with fuzzy search
        return query in str(self.local_port)


class PortModel:
    """Model for managing port connections data"""

    def __init__(self):
        self._connections = []
        self._filtered_connections = []

    @property
    def connections(self):
        return self._connections

    @property
    def filtered_connections(self):
        return self._filtered_connections

    def update_connections(self, connections):
        """Update the connections list"""
        self._connections = connections
        self._filtered_connections = connections

    def filter_connections(self, query: str):
        """Filter connections by search query"""
        if not query:
            self._filtered_connections = self._connections
        else:
            self._filtered_connections = [
                c for c in self._connections
                if c.matches_search(query)
            ]

    def get_connection_at(self, index: int) -> Optional[PortConnection]:
        """Get connection at filtered index"""
        if 0 <= index < len(self._filtered_connections):
            return self._filtered_connections[index]
        return None

    def get_total_count(self) -> int:
        return len(self._connections)

    def get_filtered_count(self) -> int:
        return len(self._filtered_connections)
