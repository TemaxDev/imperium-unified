"""Concrete DiploStore implementations for Memory/File/SQL engines (A8)."""

import json
from datetime import datetime
from typing import Any

from ...adapters.file_engine import FileStorageEngine
from ...adapters.memory_engine import MemoryEngine
from ...adapters.sql_engine import SQLiteEngine
from ..dtos import DiplomacyEvent, Faction, Relation, Treaty, TreatyStatus, TreatyType
from .store import normalize_pair


class MemoryDiploStore:
    """DiploStore implementation for MemoryEngine."""

    def __init__(self, engine: MemoryEngine):
        self.engine = engine

    def list_factions(self) -> list[Faction]:
        return [
            Faction(id=f["id"], name=f["name"], is_player=f["is_player"])
            for f in self.engine.factions.values()
        ]

    def get_faction(self, faction_id: int) -> Faction | None:
        f = self.engine.factions.get(faction_id)
        if not f:
            return None
        return Faction(id=f["id"], name=f["name"], is_player=f["is_player"])

    def get_relation(self, a: int, b: int) -> Relation | None:
        a, b = normalize_pair(a, b)
        key = f"{a}_{b}"
        rel = self.engine.relations.get(key)
        if not rel:
            return None
        return Relation(
            a=rel["a"],
            b=rel["b"],
            stance=rel["stance"],
            opinion=rel["opinion"],
            last_updated=rel["last_updated"].isoformat(),
        )

    def upsert_relation(self, a: int, b: int, stance: str, opinion: float, now: datetime) -> None:
        a, b = normalize_pair(a, b)
        key = f"{a}_{b}"
        self.engine.relations[key] = {
            "a": a,
            "b": b,
            "stance": stance,
            "opinion": opinion,
            "last_updated": now,
        }

    def list_relations(self) -> list[Relation]:
        return [
            Relation(
                a=rel["a"],
                b=rel["b"],
                stance=rel["stance"],
                opinion=rel["opinion"],
                last_updated=rel["last_updated"].isoformat(),
            )
            for rel in self.engine.relations.values()
        ]

    def list_treaties(self) -> list[Treaty]:
        result = []
        for treaty in self.engine.treaties.values():
            expires_at = None
            if "expires_at" in treaty and treaty["expires_at"]:
                expires_at = (
                    treaty["expires_at"].isoformat()
                    if isinstance(treaty["expires_at"], datetime)
                    else treaty["expires_at"]
                )
            result.append(
                Treaty(
                    id=treaty["id"],
                    a=treaty["a"],
                    b=treaty["b"],
                    type=treaty["type"],
                    status=treaty["status"],
                    started_at=(
                        treaty["started_at"].isoformat()
                        if isinstance(treaty["started_at"], datetime)
                        else treaty["started_at"]
                    ),
                    expires_at=expires_at,
                )
            )
        return result

    def get_treaty(self, treaty_id: int) -> Treaty | None:
        treaty = self.engine.treaties.get(treaty_id)
        if not treaty:
            return None
        expires_at = None
        if "expires_at" in treaty and treaty["expires_at"]:
            expires_at = (
                treaty["expires_at"].isoformat()
                if isinstance(treaty["expires_at"], datetime)
                else treaty["expires_at"]
            )
        return Treaty(
            id=treaty["id"],
            a=treaty["a"],
            b=treaty["b"],
            type=treaty["type"],
            status=treaty["status"],
            started_at=(
                treaty["started_at"].isoformat()
                if isinstance(treaty["started_at"], datetime)
                else treaty["started_at"]
            ),
            expires_at=expires_at,
        )

    def open_treaty(
        self,
        a: int,
        b: int,
        treaty_type: TreatyType,
        started_at: datetime,
        expires_at: datetime | None = None,
    ) -> int:
        a, b = normalize_pair(a, b)
        treaty_id = self.engine._next_treaty_id
        self.engine._next_treaty_id += 1
        self.engine.treaties[treaty_id] = {
            "id": treaty_id,
            "a": a,
            "b": b,
            "type": treaty_type,
            "status": "ACTIVE",
            "started_at": started_at,
            "expires_at": expires_at,
        }
        return treaty_id

    def update_treaty_status(self, treaty_id: int, status: TreatyStatus) -> None:
        if treaty_id in self.engine.treaties:
            self.engine.treaties[treaty_id]["status"] = status

    def log_event(self, kind: str, payload: dict, ts: datetime) -> None:
        self.engine.diplomacy_events.append({"kind": kind, "payload": payload, "ts": ts})

    def list_events(
        self, since: datetime | None = None, limit: int | None = None
    ) -> list[DiplomacyEvent]:
        events = self.engine.diplomacy_events
        if since:
            events = [e for e in events if e["ts"] >= since]
        if limit:
            events = events[-limit:]
        return [
            DiplomacyEvent(
                id=i,
                kind=e["kind"],
                payload=e["payload"],
                ts=e["ts"].isoformat() if isinstance(e["ts"], datetime) else e["ts"],
            )
            for i, e in enumerate(events, 1)
        ]


class FileDiploStore:
    """DiploStore implementation for FileStorageEngine."""

    def __init__(self, engine: FileStorageEngine):
        self.engine = engine

    def _save(self) -> None:
        """Save diplomacy state to JSON file."""
        data = json.loads(self.engine.storage_path.read_text())

        # Update factions
        data["factions"] = {str(fid): f for fid, f in self.engine.factions.items()}

        # Update relations (convert datetime to ISO)
        data["relations"] = {}
        for key, rel in self.engine.relations.items():
            rel_copy = rel.copy()
            if isinstance(rel_copy["last_updated"], datetime):
                rel_copy["last_updated"] = rel_copy["last_updated"].isoformat()
            data["relations"][key] = rel_copy

        # Update treaties
        data["treaties"] = {}
        for tid, treaty in self.engine.treaties.items():
            treaty_copy = treaty.copy()
            if isinstance(treaty_copy.get("started_at"), datetime):
                treaty_copy["started_at"] = treaty_copy["started_at"].isoformat()
            if isinstance(treaty_copy.get("expires_at"), datetime):
                treaty_copy["expires_at"] = treaty_copy["expires_at"].isoformat()
            data["treaties"][str(tid)] = treaty_copy

        # Update events
        data["diplomacyEvents"] = []
        for event in self.engine.diplomacy_events:
            event_copy = event.copy()
            if isinstance(event_copy.get("ts"), datetime):
                event_copy["ts"] = event_copy["ts"].isoformat()
            data["diplomacyEvents"].append(event_copy)

        self.engine.storage_path.write_text(json.dumps(data, indent=2))

    def list_factions(self) -> list[Faction]:
        return [
            Faction(id=f["id"], name=f["name"], is_player=f["is_player"])
            for f in self.engine.factions.values()
        ]

    def get_faction(self, faction_id: int) -> Faction | None:
        f = self.engine.factions.get(faction_id)
        if not f:
            return None
        return Faction(id=f["id"], name=f["name"], is_player=f["is_player"])

    def get_relation(self, a: int, b: int) -> Relation | None:
        a, b = normalize_pair(a, b)
        key = f"{a}_{b}"
        rel = self.engine.relations.get(key)
        if not rel:
            return None
        return Relation(
            a=rel["a"],
            b=rel["b"],
            stance=rel["stance"],
            opinion=rel["opinion"],
            last_updated=(
                rel["last_updated"].isoformat()
                if isinstance(rel["last_updated"], datetime)
                else rel["last_updated"]
            ),
        )

    def upsert_relation(self, a: int, b: int, stance: str, opinion: float, now: datetime) -> None:
        a, b = normalize_pair(a, b)
        key = f"{a}_{b}"
        self.engine.relations[key] = {
            "a": a,
            "b": b,
            "stance": stance,
            "opinion": opinion,
            "last_updated": now,
        }
        self._save()

    def list_relations(self) -> list[Relation]:
        return [
            Relation(
                a=rel["a"],
                b=rel["b"],
                stance=rel["stance"],
                opinion=rel["opinion"],
                last_updated=(
                    rel["last_updated"].isoformat()
                    if isinstance(rel["last_updated"], datetime)
                    else rel["last_updated"]
                ),
            )
            for rel in self.engine.relations.values()
        ]

    def list_treaties(self) -> list[Treaty]:
        result = []
        for treaty in self.engine.treaties.values():
            expires_at = None
            if "expires_at" in treaty and treaty["expires_at"]:
                expires_at = (
                    treaty["expires_at"].isoformat()
                    if isinstance(treaty["expires_at"], datetime)
                    else treaty["expires_at"]
                )
            result.append(
                Treaty(
                    id=treaty["id"],
                    a=treaty["a"],
                    b=treaty["b"],
                    type=treaty["type"],
                    status=treaty["status"],
                    started_at=(
                        treaty["started_at"].isoformat()
                        if isinstance(treaty["started_at"], datetime)
                        else treaty["started_at"]
                    ),
                    expires_at=expires_at,
                )
            )
        return result

    def get_treaty(self, treaty_id: int) -> Treaty | None:
        treaty = self.engine.treaties.get(treaty_id)
        if not treaty:
            return None
        expires_at = None
        if "expires_at" in treaty and treaty["expires_at"]:
            expires_at = (
                treaty["expires_at"].isoformat()
                if isinstance(treaty["expires_at"], datetime)
                else treaty["expires_at"]
            )
        return Treaty(
            id=treaty["id"],
            a=treaty["a"],
            b=treaty["b"],
            type=treaty["type"],
            status=treaty["status"],
            started_at=(
                treaty["started_at"].isoformat()
                if isinstance(treaty["started_at"], datetime)
                else treaty["started_at"]
            ),
            expires_at=expires_at,
        )

    def open_treaty(
        self,
        a: int,
        b: int,
        treaty_type: TreatyType,
        started_at: datetime,
        expires_at: datetime | None = None,
    ) -> int:
        a, b = normalize_pair(a, b)
        treaty_id = self.engine._next_treaty_id
        self.engine._next_treaty_id += 1
        self.engine.treaties[treaty_id] = {
            "id": treaty_id,
            "a": a,
            "b": b,
            "type": treaty_type,
            "status": "ACTIVE",
            "started_at": started_at,
            "expires_at": expires_at,
        }
        self._save()
        return treaty_id

    def update_treaty_status(self, treaty_id: int, status: TreatyStatus) -> None:
        if treaty_id in self.engine.treaties:
            self.engine.treaties[treaty_id]["status"] = status
            self._save()

    def log_event(self, kind: str, payload: dict, ts: datetime) -> None:
        self.engine.diplomacy_events.append({"kind": kind, "payload": payload, "ts": ts})
        self._save()

    def list_events(
        self, since: datetime | None = None, limit: int | None = None
    ) -> list[DiplomacyEvent]:
        events = self.engine.diplomacy_events
        if since:
            events = [
                e
                for e in events
                if (e["ts"] if isinstance(e["ts"], datetime) else datetime.fromisoformat(e["ts"]))
                >= since
            ]
        if limit:
            events = events[-limit:]
        return [
            DiplomacyEvent(
                id=i,
                kind=e["kind"],
                payload=e["payload"],
                ts=e["ts"].isoformat() if isinstance(e["ts"], datetime) else e["ts"],
            )
            for i, e in enumerate(events, 1)
        ]


class SQLDiploStore:
    """DiploStore implementation for SQLiteEngine."""

    def __init__(self, engine: SQLiteEngine):
        self.engine = engine

    def list_factions(self) -> list[Faction]:
        from ...db.models import Faction as FactionORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            factions = session.query(FactionORM).all()
            return [Faction(id=f.id, name=f.name, is_player=bool(f.is_player)) for f in factions]

    def get_faction(self, faction_id: int) -> Faction | None:
        from ...db.models import Faction as FactionORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            f = session.get(FactionORM, faction_id)
            if not f:
                return None
            return Faction(id=f.id, name=f.name, is_player=bool(f.is_player))

    def get_relation(self, a: int, b: int) -> Relation | None:
        from ...db.models import Relation as RelationORM

        a, b = normalize_pair(a, b)
        with self.engine.session() as session:  # type: ignore[attr-defined]
            rel = session.get(RelationORM, (a, b))
            if not rel:
                return None
            return Relation(
                a=rel.a,
                b=rel.b,
                stance=rel.stance,
                opinion=rel.opinion,
                last_updated=rel.last_updated,
            )

    def upsert_relation(self, a: int, b: int, stance: str, opinion: float, now: datetime) -> None:
        from ...db.models import Relation as RelationORM

        a, b = normalize_pair(a, b)
        with self.engine.session() as session:  # type: ignore[attr-defined]
            rel = session.get(RelationORM, (a, b))
            if rel:
                rel.stance = stance
                rel.opinion = opinion
                rel.last_updated = now.isoformat()
            else:
                rel = RelationORM(
                    a=a, b=b, stance=stance, opinion=opinion, last_updated=now.isoformat()
                )
                session.add(rel)
            session.commit()

    def list_relations(self) -> list[Relation]:
        from ...db.models import Relation as RelationORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            relations = session.query(RelationORM).all()
            return [
                Relation(
                    a=rel.a,
                    b=rel.b,
                    stance=rel.stance,
                    opinion=rel.opinion,
                    last_updated=rel.last_updated,
                )
                for rel in relations
            ]

    def list_treaties(self) -> list[Treaty]:
        from ...db.models import Treaty as TreatyORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            treaties = session.query(TreatyORM).all()
            return [
                Treaty(
                    id=t.id,
                    a=t.a,
                    b=t.b,
                    type=t.type,
                    status=t.status,
                    started_at=t.started_at,
                    expires_at=t.expires_at,
                )
                for t in treaties
            ]

    def get_treaty(self, treaty_id: int) -> Treaty | None:
        from ...db.models import Treaty as TreatyORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            t = session.get(TreatyORM, treaty_id)
            if not t:
                return None
            return Treaty(
                id=t.id,
                a=t.a,
                b=t.b,
                type=t.type,
                status=t.status,
                started_at=t.started_at,
                expires_at=t.expires_at,
            )

    def open_treaty(
        self,
        a: int,
        b: int,
        treaty_type: TreatyType,
        started_at: datetime,
        expires_at: datetime | None = None,
    ) -> int:
        from ...db.models import Treaty as TreatyORM

        a, b = normalize_pair(a, b)
        with self.engine.session() as session:  # type: ignore[attr-defined]
            treaty = TreatyORM(
                a=a,
                b=b,
                type=treaty_type,
                status="ACTIVE",
                started_at=started_at.isoformat(),
                expires_at=expires_at.isoformat() if expires_at else None,
            )
            session.add(treaty)
            session.commit()
            session.refresh(treaty)
            return treaty.id  # type: ignore[return-value]

    def update_treaty_status(self, treaty_id: int, status: TreatyStatus) -> None:
        from ...db.models import Treaty as TreatyORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            treaty = session.get(TreatyORM, treaty_id)
            if treaty:
                treaty.status = status
                session.commit()

    def log_event(self, kind: str, payload: dict, ts: datetime) -> None:
        from ...db.models import DiplomacyEvent as EventORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            event = EventORM(kind=kind, payload=json.dumps(payload), ts=ts.isoformat())
            session.add(event)
            session.commit()

    def list_events(
        self, since: datetime | None = None, limit: int | None = None
    ) -> list[DiplomacyEvent]:
        from ...db.models import DiplomacyEvent as EventORM

        with self.engine.session() as session:  # type: ignore[attr-defined]
            query = session.query(EventORM)
            if since:
                query = query.filter(EventORM.ts >= since.isoformat())
            if limit:
                query = query.order_by(EventORM.id.desc()).limit(limit)  # type: ignore[union-attr]
            events = query.all()
            return [
                DiplomacyEvent(
                    id=e.id,
                    kind=e.kind,
                    payload=json.loads(e.payload),
                    ts=e.ts,
                )
                for e in events
            ]


def get_diplo_store(engine: Any) -> Any:
    """Factory function to get appropriate DiploStore for engine type."""
    if isinstance(engine, MemoryEngine):
        return MemoryDiploStore(engine)
    elif isinstance(engine, FileStorageEngine):
        return FileDiploStore(engine)
    elif isinstance(engine, SQLiteEngine):
        return SQLDiploStore(engine)
    else:
        msg = f"Unsupported engine type: {type(engine)}"
        raise TypeError(msg)
