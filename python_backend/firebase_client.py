# ─── firebase_client.py ───────────────────────────────────────────────────────
# Firebase Admin SDK wrapper — initialises once, exposes typed helpers
# Set USE_FIREBASE=False in config.py to run without a real Firebase project.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
import os, logging
from typing import Any, Dict, List, Optional

import streamlit as st
from config import USE_FIREBASE, FIRESTORE_COLLECTIONS

logger = logging.getLogger(__name__)

REQUIRED_FIREBASE_SECRET_FIELDS = (
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
)


def _firebase_secret_dict() -> Optional[Dict[str, str]]:
    try:
        if "firebase" in st.secrets:
            return dict(st.secrets["firebase"])
    except Exception:
        return None
    return None


def has_firebase_credentials() -> bool:
    """Return True when the backend has usable Firebase credentials."""
    if not USE_FIREBASE:
        return False

    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return True

    cred_dict = _firebase_secret_dict()
    if not cred_dict:
        return False

    for field in REQUIRED_FIREBASE_SECRET_FIELDS:
        value = str(cred_dict.get(field, "")).strip()
        if not value or "YOUR_" in value:
            return False

    return "BEGIN PRIVATE KEY" in str(cred_dict.get("private_key", "")) or "BEGIN RSA PRIVATE KEY" in str(cred_dict.get("private_key", ""))

# ── Lazy initialisation via st.cache_resource ─────────────────────────────
@st.cache_resource
def _get_firebase_app():
    """Initialise the Firebase Admin app exactly once per Streamlit session."""
    if not USE_FIREBASE:
        return None, None

    if not has_firebase_credentials():
        logger.warning(
            "Firebase credentials not configured. Add a real service account to "
            ".streamlit/secrets.toml or set GOOGLE_APPLICATION_CREDENTIALS."
        )
        return None, None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            # Load credentials from Streamlit secrets (preferred) or env var
            cred_dict = _firebase_secret_dict()
            if cred_dict:
                cred = credentials.Certificate(cred_dict)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                cred = credentials.ApplicationDefault()
            else:
                logger.warning(
                    "No Firebase credentials found. Add them to .streamlit/secrets.toml"
                )
                return None, None

            firebase_admin.initialize_app(cred)

        app = firebase_admin.get_app()
        db  = firestore.client()
        logger.info("Firebase initialised successfully.")
        return app, db

    except Exception as exc:
        logger.error("Firebase init failed: %s", exc)
        return None, None


def get_db():
    """Return the Firestore client (or None in local-only mode)."""
    _, db = _get_firebase_app()
    return db


# ── CRUD helpers ─────────────────────────────────────────────────────────────

def collection_ref(name: str):
    db = get_db()
    if db is None:
        return None
    return db.collection(FIRESTORE_COLLECTIONS.get(name, name))


def batch_write(collection: str, documents: List[Dict[str, Any]]) -> int:
    """
    Write a list of dicts to Firestore in batches of 499 (Firestore limit).
    Returns the number of documents written.
    """
    db = get_db()
    if db is None:
        logger.info("[local] batch_write skipped — no Firebase connection.")
        return 0

    from firebase_admin import firestore as fs
    col   = db.collection(FIRESTORE_COLLECTIONS.get(collection, collection))
    total = 0

    try:
        for i in range(0, len(documents), 499):
            batch = db.batch()
            for doc in documents[i : i + 499]:
                doc_id = doc.pop("_id", None) or col.document().id
                ref    = col.document(str(doc_id))
                batch.set(ref, doc)
            batch.commit()
            total += min(499, len(documents) - i)
    except Exception as exc:
        logger.error(f"Permission denied executing batch write: {exc}")

    logger.info("Wrote %d documents to '%s'.", total, collection)
    return total


def read_collection(
    collection: str,
    order_by: Optional[str] = None,
    limit: Optional[int]    = None,
    filters: Optional[List]  = None,
) -> List[Dict[str, Any]]:
    """
    Read documents from a Firestore collection.
    filters: list of (field, op, value) tuples, e.g. [("severity", ">=", "warning")]
    """
    db = get_db()
    if db is None:
        return []

    ref = db.collection(FIRESTORE_COLLECTIONS.get(collection, collection))

    if filters:
        for field, op, value in filters:
            ref = ref.where(field, op, value)
    if order_by:
        ref = ref.order_by(order_by)
    if limit:
        ref = ref.limit(limit)

    try:
        return [doc.to_dict() for doc in ref.stream()]
    except Exception as exc:
        logger.error(f"Permission denied or read error on collection {collection}: {exc}")
        return []


def delete_collection(collection: str) -> None:
    """Delete all documents in a collection (used before re-seeding)."""
    db = get_db()
    if db is None:
        return
    col  = db.collection(FIRESTORE_COLLECTIONS.get(collection, collection))
    try:
        docs = col.limit(500).stream()
        for doc in docs:
            doc.reference.delete()
    except Exception as exc:
        logger.error(f"Permission denied deleting collection: {exc}")
