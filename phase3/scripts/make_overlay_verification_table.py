#!/usr/bin/env python3

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PHASE3 = Path.home() / "phase3"

DATA_DIR = PHASE3 / "data"
IMG_DIR = PHASE3 / "img"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

IMG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


rows = [
    {
        "Verification Item":
            "VXLAN Interface",

        "Evidence":
            "vxlan100 configured with VNI 100 "
            "and UDP destination port 4789",

        "Result":
            "PASS"
    },

    {
        "Verification Item":
            "VTEP Configuration",

        "Evidence":
            "leaf1 VTEP = 1.1.1.1; "
            "leaf2 VTEP = 2.2.2.2",

        "Result":
            "PASS"
    },

    {
        "Verification Item":
            "BGP EVPN Control Plane",

        "Evidence":
            "BGP EVPN peers established; "
            "EVPN Type-2 and Type-3 routes present",

        "Result":
            "PASS"
    },

    {
        "Verification Item":
            "VXLAN Data Plane",

        "Evidence":
            "Packet capture on spine observed "
            "UDP/4789 VXLAN packets with VNI 100",

        "Result":
            "PASS"
    },

    {
        "Verification Item":
            "End-to-End Overlay Traffic",

        "Evidence":
            "Inner packets carried "
            "192.168.100.11 <-> 192.168.100.22 "
            "ICMP traffic through VXLAN",

        "Result":
            "PASS"
    }
]


df = pd.DataFrame(
    rows
)


# ============================================================
# Save CSV
# ============================================================

CSV_FILE = (
    DATA_DIR
    / "evpn_vxlan_verification_table.csv"
)

df.to_csv(
    CSV_FILE,
    index=False
)


# ============================================================
# Wrapped display version
# ============================================================

display_df = df.copy()

display_df["Evidence"] = [
    "vxlan100 configured with VNI 100\n"
    "and UDP destination port 4789",

    "leaf1 VTEP = 1.1.1.1\n"
    "leaf2 VTEP = 2.2.2.2",

    "BGP EVPN peers established;\n"
    "EVPN Type-2 and Type-3 routes present",

    "Packet capture on spine observed UDP/4789\n"
    "VXLAN packets with VNI 100",

    "Inner packets carried 192.168.100.11 ↔ 192.168.100.22\n"
    "ICMP traffic through VXLAN"
]


# ============================================================
# Draw table
# ============================================================

fig, ax = plt.subplots(
    figsize=(14, 6.5)
)

ax.axis(
    "off"
)


table = ax.table(
    cellText=display_df.values,
    colLabels=display_df.columns,
    cellLoc="left",
    colLoc="left",
    loc="center",
    colWidths=[
        0.23,
        0.62,
        0.15
    ]
)


table.auto_set_font_size(
    False
)

table.set_fontsize(
    10
)

table.scale(
    1,
    2.3
)


# Header bold
for col in range(
    len(display_df.columns)
):

    table[
        (0, col)
    ].set_text_props(
        weight="bold"
    )


# Result column bold
for row in range(
    1,
    len(display_df) + 1
):

    table[
        (row, 2)
    ].set_text_props(
        weight="bold"
    )


ax.set_title(
    "EVPN/VXLAN Overlay Verification",
    fontsize=14,
    pad=20
)


fig.tight_layout()


PNG_FILE = (
    IMG_DIR
    / "evpn_vxlan_verification_table.png"
)

PDF_FILE = (
    IMG_DIR
    / "evpn_vxlan_verification_table.pdf"
)


fig.savefig(
    PNG_FILE,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    PDF_FILE,
    bbox_inches="tight"
)

plt.close(
    fig
)


print()
print(
    "=== EVPN/VXLAN Verification Table ==="
)

print()

print(
    df.to_string(
        index=False
    )
)

print()

print(
    "Saved:"
)

print(
    CSV_FILE
)

print(
    PNG_FILE
)

print(
    PDF_FILE
)