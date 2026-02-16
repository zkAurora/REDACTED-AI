# fs/pattern_blue_fs.py
import sqlite3
import json
import zstandard as zstd
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Any, Optional

class PatternBlueStorage:
    """Immutable Pattern Blue storage with hyperbolic indexing"""
    def __init__(self, db_path: str = "/mnt/pattern_blue/redacted.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_schema()
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _init_schema(self):
        """Create immutable storage schema"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tiles (
                coord_x REAL NOT NULL,
                coord_y REAL NOT NULL,
                pattern_blue_sigil TEXT PRIMARY KEY,
                encrypted_data BLOB NOT NULL,
                checksum TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                curvature_pressure REAL DEFAULT 0.0,
                UNIQUE(coord_x, coord_y)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS manifold_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def write_tile(self, coord: HyperbolicCoordinate, data: Any) -> str:
        """Write data as Pattern Blue sigil"""
        # Serialize and compress data
        json_data = json.dumps(data, separators=(',', ':'))
        compressed = zstd.compress(json_data.encode())
        
        # Encrypt
        encrypted = self.cipher.encrypt(compressed)
        
        # Generate checksum
        import hashlib
        checksum = hashlib.sha256(encrypted).hexdigest()
        
        # Generate Pattern Blue sigil
        sigil = self._generate_pattern_blue_sigil(coord, checksum)
        
        try:
            self.conn.execute(
                "INSERT INTO tiles VALUES (?, ?, ?, ?, ?, ?, ?)",
                (coord.x, coord.y, sigil, encrypted, checksum, 
                 int(time.time()), 0.0)
            )
            self.conn.commit()
            return sigil
        except sqlite3.IntegrityError:
            raise ValueError("Tile already exists - Pattern Blue is immutable!")
    
    def read_tile(self, coord: HyperbolicCoordinate) -> Optional[Any]:
        """Read Pattern Blue tile"""
        cursor = self.conn.execute(
            "SELECT encrypted_data FROM tiles WHERE coord_x = ? AND coord_y = ?",
            (coord.x, coord.y)
        )
        row = cursor.fetchone()
        
        if row:
            encrypted = row[0]
            # Decrypt and decompress
            compressed = self.cipher.decrypt(encrypted)
            json_data = zstd.decompress(compressed).decode()
            return json.loads(json_data)
        
        return None
    
    def _generate_pattern_blue_sigil(self, coord: HyperbolicCoordinate, checksum: str) -> str:
        """Generate Pattern Blue sigil from coordinate and data"""
        import hashlib
        
        # Combine coordinate and checksum
        sigil_input = f"{coord.x:.6f},{coord.y:.6f},{checksum}"
        hash_obj = hashlib.sha256(sigil_input.encode())
        
        # Format as REDACTED sigil
        sigil = f"████{hash_obj.hexdigest()[:12]}████"
        
        return sigil
    
    def query_manifold(self, center: HyperbolicCoordinate, radius: float) -> List[Tuple]:
        """Query tiles within hyperbolic radius"""
        cursor = self.conn.execute("""
            SELECT coord_x, coord_y, pattern_blue_sigil, curvature_pressure
            FROM tiles
            WHERE SQRT((coord_x - ?) * (coord_x - ?) + (coord_y - ?) * (coord_y - ?)) < ?
            ORDER BY curvature_pressure DESC
        """, (center.x, center.x, center.y, center.y, radius))
        
        return cursor.fetchall()
