#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import sys
import json
import base64
from dataclasses import dataclass
from enum import Enum

# https://github.com/espressif/esp-idf/blob/c69f0ec3292de2b9df5554405744296333d0feb2/components/nvs_flash/src/nvs_page.hpp#L36-L39
PSB_INIT = 0x1
PSB_FULL = 0x2
PSB_FREEING = 0x4
PSB_CORRUPT = 0x8


class PageState(Enum):
    # All bits set, default state after flash erase. Page has not been initialized yet.
    UNINITIALIZED = 0xFFFFFFFF

    # Page is initialized, and will accept writes.
    ACTIVE = UNINITIALIZED & ~PSB_INIT

    # Page is marked as full and will not accept new writes.
    FULL = ACTIVE & ~PSB_FULL

    # Data is being moved from this page to a new one.
    FREEING = FULL & ~PSB_FREEING

    # Page was found to be in a corrupt and unrecoverable state.
    # Instead of being erased immediately, it will be kept for diagnostics and data recovery.
    # It will be erased once we run out out free pages.
    CORRUPT = FREEING & ~PSB_CORRUPT

    @classmethod
    def from_text(cls, text):
        return {
            "UNINITIALIZED": PageState.UNINITIALIZED,
            "EMPTY": PageState.UNINITIALIZED,
            "ACTIVE": PageState.ACTIVE,
            "FULL": PageState.FULL,
            "FREEING": PageState.FREEING,
            "CORRUPT": PageState.CORRUPT,
        }[text]


ESB_WRITTEN = 0x1
ESB_ERASED = 0x2


class EntryState(Enum):
    # 0b11, default state after flash erase
    EMPTY = 0x3
    # entry was written
    WRITTEN = EMPTY & ~ESB_WRITTEN
    # entry was written and then erased
    ERASED = WRITTEN & ~ESB_ERASED
    # entry is in inconsistent state (write started but ESB_WRITTEN has not been set yet)
    INVALID = 0x4

    @classmethod
    def from_text(cls, text):
        return {
            "Empty": EntryState.EMPTY,
            "Written": EntryState.WRITTEN,
            "Erased": EntryState.ERASED,
            "Invalid": EntryState.INVALID,
        }[text]


@dataclass
class Entry:
    state: EntryState
    ns_index: int
    ns_name: str
    typ: str
    span: int
    chunk_index: int

    key: str
    data: any


@dataclass
class Page:
    state: PageState
    seq_no: int
    version: int

    entries: list[Entry]


def load_pages_from_json(json):
    result = []
    for page in json:
        result.append(
            Page(
                state=PageState.from_text(page["page_state"]),
                seq_no=page["page_seq_no"],
                version=page["page_version"],
                entries=[
                    Entry(
                        state=EntryState.from_text(entry["entry_state"]),
                        ns_index=entry["entry_ns_index"],
                        ns_name=entry.get("entry_ns", ""),
                        typ=entry["entry_type"],
                        span=entry["entry_span"],
                        chunk_index=entry["entry_chunk_index"],
                        key=entry["entry_key"],
                        data=entry.get("entry_data"),
                    )
                    for entry in page["entries"]
                ],
            )
        )

    return result


def list_namespaces(entries: list[Entry]):
    namespaces = {}
    for e in entries:
        if e.ns_name not in namespaces:
            namespaces[e.ns_name] = e.ns_index
    return [kv[0] for kv in sorted(namespaces.items(), key=lambda kv: kv[1])]


def map_to_csv(e: Entry):
    if e.state != EntryState.WRITTEN:
        return ""

    if e.typ in {"U8", "I8", "U16", "I16", "U32", "I32", "U64", "I64"}:
        data = (e.typ.lower(), str(e.data))
    elif e.typ == "BLOB_DATA":
        data = ("base64", e.data)
    elif e.typ == "STR":
        data = ("string", e.data)

    return e.key + ",data," + data[0] + "," + data[1] + "\n"


def main(args):
    with open(args[1], "r") as file:
        pages = load_pages_from_json(json.load(file))

    entries = []
    for page in pages:
        entries.extend(page.entries)

    entries = [e for e in entries if e.typ not in {"BLOB", "BLOB_IDX"}]

    namespaces = list_namespaces(entries)
    with open(args[2], "w") as out_file:
        out_file.write("key,type,encoding,value\n")
        for ns in namespaces:
            ns_entries = [e for e in entries if e.ns_name == ns]
            if ns:
                out_file.write(ns + ",namespace,,\n")
            for e in ns_entries:
                out_file.write(map_to_csv(e))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
