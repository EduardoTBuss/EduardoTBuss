#!/usr/bin/env python3
"""Generate the animated SVG modules used by the GitHub profile README.

Only the Python standard library is required. Content lives in data/*.json;
this file owns presentation and animation.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import textwrap
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "generated"

BG = "#050a16"
PANEL = "#091326"
PANEL_2 = "#0c1930"
TEXT = "#e6f4ff"
MUTED = "#91a7bd"
CYAN = "#29e6f2"
BLUE = "#38bdf8"
PURPLE = "#a78bfa"
MAGENTA = "#d56dff"
GREEN = "#52e0a4"
LINE = "#17375a"

# Controles globais da poeira animada do dashboard.
tamanho_particula = 1.35          # escala visual dos grãos (recomendado: 0.6 a 2.4)
cor_particula = "#38bdf8"         # qualquer cor CSS/hexadecimal
aleatoriedade_particula = 0.85    # 0.0 = uniforme; 1.0 = máxima variação


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save_json(name: str, value) -> None:
    (DATA / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def e(value) -> str:
    return html.escape(str(value), quote=True)


def lines(value: str, width: int, maximum: int = 3) -> list[str]:
    wrapped = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) > maximum:
        wrapped = wrapped[:maximum]
        wrapped[-1] = wrapped[-1].rstrip(" .") + "…"
    return wrapped or [""]


def text_lines(value: str, x: int, y: int, *, width: int, step: int = 23,
               css: str = "body", maximum: int = 3) -> str:
    spans = []
    for index, line in enumerate(lines(value, width, maximum)):
        spans.append(f'<tspan x="{x}" dy="{0 if index == 0 else step}">{e(line)}</tspan>')
    return f'<text x="{x}" y="{y}" class="{css}">' + "".join(spans) + "</text>"


def refreshed_label(value: object) -> str:
    """Format snapshot timestamps precisely so the profile does not look stale."""
    raw = str(value or "")
    if not raw:
        return "NOT REFRESHED"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return raw[:16].replace("T", " ").upper()


def shell(width: int, height: int, title: str, description: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{e(title)}</title>
  <desc id="desc">{e(description)}</desc>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
    .eyebrow {{ fill: {CYAN}; font-size: 13px; font-weight: 700; letter-spacing: 2px; }}
    .title {{ fill: {TEXT}; font-size: 36px; font-weight: 720; letter-spacing: -1px; }}
    .heading {{ fill: {TEXT}; font-size: 22px; font-weight: 700; }}
    .subheading {{ fill: {PURPLE}; font-size: 16px; font-weight: 700; letter-spacing: .7px; }}
    .body {{ fill: {MUTED}; font-size: 15px; }}
    .small {{ fill: {MUTED}; font-size: 12px; }}
    .code {{ fill: {CYAN}; font-size: 13px; }}
    .panel {{ fill: {PANEL}; stroke: {LINE}; stroke-width: 1.2; fill-opacity: 0; stroke-dasharray: 1700; stroke-dashoffset: 1700; animation: panelBuild 1.05s ease forwards; animation-delay: calc(var(--section-delay, 0s) + var(--panel-delay, .25s)); }}
    .panel2 {{ fill: {PANEL_2}; stroke: {LINE}; stroke-width: 1.2; fill-opacity: 0; stroke-dasharray: 1700; stroke-dashoffset: 1700; animation: panelBuild 1.05s ease forwards; animation-delay: calc(var(--section-delay, 0s) + var(--panel-delay, .25s)); }}
    .reveal {{ opacity: 0; transform: translateY(8px); animation: reveal .72s ease forwards; animation-delay: calc(var(--section-delay, 0s) + var(--delay, 0s)); }}
    .draw {{ stroke-dasharray: var(--length, 500); stroke-dashoffset: var(--length, 500); animation: draw 1.4s ease forwards; animation-delay: calc(var(--section-delay, 0s) + var(--delay, .2s)); }}
    .pulse {{ animation: pulse 2.5s ease-in-out infinite; animation-delay: calc(var(--section-delay, 0s) + var(--delay, 0s)); transform-box: fill-box; transform-origin: center; }}
    .signal {{ stroke-dasharray: 4 14; animation: signal 2.8s linear infinite; animation-delay: var(--section-delay, 0s); }}
    .float {{ animation: float 4s ease-in-out infinite; animation-delay: var(--section-delay, 0s); }}
    .gridBoot {{ opacity: 0; animation: gridBoot 1.4s ease forwards; animation-delay: var(--section-delay, 0s); }}
    .borderBoot {{ stroke-dasharray: 3200; stroke-dashoffset: 3200; animation: draw 1.35s ease forwards; animation-delay: var(--section-delay, 0s); }}
    .cornerBoot {{ stroke-dasharray: 420; stroke-dashoffset: 420; animation: draw .85s ease forwards; animation-delay: calc(var(--section-delay, 0s) + .12s); }}
    .scan {{ animation: scan 2.5s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: var(--section-delay, 0s); }}
    .layerNode {{ transform-box: fill-box; transform-origin: center; animation: layerNode 4s ease-in-out infinite; animation-delay: calc(var(--section-delay, 0s) + var(--node-delay, 0s)); }}
    .connectionStage {{ animation: connectionGlow 4s ease-in-out infinite; animation-delay: calc(var(--section-delay, 0s) + var(--edge-delay, 0s)); }}
    .traveler {{ filter: url(#glow); }}
    @keyframes reveal {{ to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes panelBuild {{ 0% {{ fill-opacity: 0; stroke-dashoffset: 1700; }} 62% {{ fill-opacity: 0; stroke-dashoffset: 0; }} 100% {{ fill-opacity: 1; stroke-dashoffset: 0; }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .45; transform: scale(.85); }} 50% {{ opacity: 1; transform: scale(1.18); }} }}
    @keyframes signal {{ to {{ stroke-dashoffset: -72; }} }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
    @keyframes gridBoot {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes scan {{ 0% {{ transform: translateY(-4px); opacity: 0; }} 10% {{ opacity: .9; }} 88% {{ opacity: .55; }} 100% {{ transform: translateY({height}px); opacity: 0; }} }}
    @keyframes layerNode {{ 0%, 18%, 100% {{ opacity: .42; transform: scale(.82); }} 27%, 42% {{ opacity: 1; transform: scale(1.45); }} 55% {{ opacity: .72; transform: scale(1); }} }}
    @keyframes connectionGlow {{ 0%, 18%, 100% {{ opacity: .18; }} 25%, 48% {{ opacity: .95; }} 62% {{ opacity: .35; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .reveal, .draw, .pulse, .signal, .float, .gridBoot, .borderBoot, .cornerBoot, .scan, .layerNode, .connectionStage, .panel, .panel2 {{ animation-duration: .001ms !important; animation-delay: 0s !important; animation-iteration-count: 1 !important; animation-fill-mode: both !important; }}
      .traveler {{ display: none; }}
    }}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{BG}"/><stop offset=".52" stop-color="#061326"/><stop offset="1" stop-color="#09091b"/></linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{CYAN}"/><stop offset=".52" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>
    <radialGradient id="orb"><stop stop-color="{CYAN}" stop-opacity=".17"/><stop offset=".7" stop-color="{PURPLE}" stop-opacity=".06"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="#123050" stroke-opacity=".27" stroke-width="1"/></pattern>
    <filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="14"/></filter>
  </defs>
  <rect width="{width}" height="{height}" rx="22" fill="url(#bg)"/>
  <rect width="{width}" height="{height}" rx="22" fill="url(#grid)" class="gridBoot"/>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="21" fill="none" stroke="#18395d" class="borderBoot"/>
  <path d="M24 12H150 M12 24V90 M{width-24} {height-12}H{width-150} M{width-12} {height-24}V{height-90}" stroke="url(#accent)" stroke-width="2" opacity=".7" class="cornerBoot"/>
  <rect x="18" y="0" width="{width-36}" height="2" rx="1" fill="url(#accent)" opacity="0" class="scan" filter="url(#glow)"/>
'''


def end_svg() -> str:
    return "</svg>\n"


def hero(profile: dict) -> str:
    interests = " · ".join(profile["interests"])
    body = [shell(1200, 520, f'{profile["name"]} — research profile',
                  "Animated scientific profile with a Bloch sphere and variational quantum circuit.")]
    body.append(f'''
  <circle cx="660" cy="270" r="250" fill="url(#orb)"/>
  <g class="reveal" style="--delay:.08s">
    <text x="58" y="64" class="eyebrow">{e(profile['eyebrow'])}</text>
    <circle cx="37" cy="58" r="5" fill="{CYAN}" class="pulse" filter="url(#glow)"/>
  </g>
  <g class="reveal" style="--delay:.22s">
    <text x="56" y="132" class="title">{e(profile['name'])}</text>
    <text x="58" y="164" fill="{PURPLE}" font-size="22" font-weight="700">@{e(profile['username'])}</text>
    <text x="58" y="202" class="subheading">{e(profile['role'])}</text>
    <text x="58" y="227" class="body">{e(profile['subtitle'])}</text>
  </g>
  <g class="reveal" style="--delay:.38s">
    {text_lines(profile['bio'], 58, 275, width=48, step=24, maximum=4)}
    <rect x="58" y="374" width="176" height="30" rx="15" fill="#0b2133" stroke="#1d5268"/>
    <circle cx="76" cy="389" r="4" fill="{GREEN}" class="pulse"/>
    <text x="89" y="394" class="small">{e(profile['location'])}</text>
    <text x="58" y="444" class="small">FIELDS /</text>
    <text x="58" y="470" fill="{CYAN}" font-size="13">{e(interests)}</text>
  </g>

  <!-- Bloch sphere -->
  <g class="reveal" style="--delay:.34s"><g class="float">
    <circle cx="665" cy="277" r="170" fill="#061426" fill-opacity=".5" stroke="{BLUE}" stroke-opacity=".8" stroke-width="1.6" class="draw" style="--length:1100;--delay:.55s"/>
    <ellipse cx="665" cy="277" rx="170" ry="52" fill="none" stroke="{PURPLE}" stroke-opacity=".65" class="draw" style="--length:760;--delay:.75s"/>
    <ellipse cx="665" cy="277" rx="170" ry="116" fill="none" stroke="{BLUE}" stroke-opacity=".28" class="draw" style="--length:930;--delay:.86s"/>
    <ellipse cx="665" cy="277" rx="64" ry="170" fill="none" stroke="{CYAN}" stroke-opacity=".35" class="draw" style="--length:930;--delay:.95s"/>
    <ellipse cx="665" cy="277" rx="128" ry="170" fill="none" stroke="{PURPLE}" stroke-opacity=".22" class="draw" style="--length:1100;--delay:1.02s"/>
    <path d="M487 277H843 M665 91V464 M530 390L800 164" fill="none" stroke="#8ecff5" stroke-opacity=".72" stroke-width="1.3" class="draw" style="--length:760;--delay:1.1s"/>
    <path d="M665 277L752 160" stroke="{CYAN}" stroke-width="3" marker-end="url(#arrow)" class="draw" filter="url(#glow)" style="--length:160;--delay:1.3s"/>
    <path d="M722 201A74 74 0 0 0 665 179" fill="none" stroke="{MAGENTA}" stroke-width="2" class="draw" style="--length:150;--delay:1.52s"/>
    <circle cx="752" cy="160" r="6" fill="{CYAN}" class="pulse" style="--delay:1.5s" filter="url(#glow)"/>
    <circle cx="526" cy="329" r="4" fill="{MAGENTA}" class="pulse" style="--delay:.8s"/>
    <text x="760" y="154" fill="{CYAN}" font-size="16">|ψ⟩</text>
    <text x="711" y="195" fill="{MAGENTA}" font-size="15">θ</text>
    <text x="795" y="299" fill="{MUTED}" font-size="14">+x</text>
    <text x="650" y="78" fill="{MUTED}" font-size="14">|0⟩</text>
    <text x="650" y="486" fill="{MUTED}" font-size="14">|1⟩</text>
    <text x="552" y="129" class="eyebrow">BLOCH STATE / 01</text>
  </g></g>

  <!-- VQC -->
  <g class="reveal" style="--delay:1.25s">
    <rect x="858" y="76" width="298" height="356" rx="17" class="panel" style="--panel-delay:1.18s"/>
    <text x="882" y="110" class="eyebrow">VQC / SIGNAL PREVIEW</text>
    <text x="882" y="134" class="small">ENCODE x → U(θ) → ENTANGLE → ⟨Z⟩</text>
    <g stroke="#426688" stroke-width="1.5">
      <path d="M880 184H1134 M880 239H1134 M880 294H1134 M880 349H1134"/>
    </g>
    <g fill="#101d36" stroke="{BLUE}">
      <rect x="901" y="166" width="42" height="36" rx="7"/><rect x="901" y="221" width="42" height="36" rx="7"/><rect x="901" y="276" width="42" height="36" rx="7"/><rect x="901" y="331" width="42" height="36" rx="7"/>
    </g>
    <g fill="#151433" stroke="{PURPLE}">
      <rect x="966" y="166" width="47" height="36" rx="7"/><rect x="966" y="221" width="47" height="36" rx="7"/><rect x="966" y="276" width="47" height="36" rx="7"/><rect x="966" y="331" width="47" height="36" rx="7"/>
    </g>
    <g fill="{TEXT}" font-size="10" text-anchor="middle">
      <text x="922" y="188">Rᵧ(xᵢ)</text><text x="922" y="243">Rᵧ(xᵢ)</text><text x="922" y="298">Rᵧ(xᵢ)</text><text x="922" y="353">Rᵧ(xᵢ)</text>
      <text x="989" y="188">Rᵧ(θᵢ)</text><text x="989" y="243">Rᵧ(θᵢ)</text><text x="989" y="298">Rᵧ(θᵢ)</text><text x="989" y="353">Rᵧ(θᵢ)</text>
    </g>
    <g stroke="{CYAN}" stroke-width="1.5" class="draw signal" style="--length:500;--delay:1.5s">
      <path d="M1043 184V239"/><path d="M1073 294V349"/><path d="M1102 239V294"/>
    </g>
    <g fill="{CYAN}"><circle cx="1043" cy="184" r="5"/><circle cx="1073" cy="294" r="5"/><circle cx="1102" cy="239" r="5"/></g>
    <g fill="none" stroke="{CYAN}"><circle cx="1043" cy="239" r="9"/><path d="M1034 239H1052M1043 230V248"/><circle cx="1073" cy="349" r="9"/><path d="M1064 349H1082M1073 340V358"/><circle cx="1102" cy="294" r="9"/><path d="M1093 294H1111M1102 285V303"/></g>
    <g fill="{MAGENTA}" font-size="13" text-anchor="middle"><text x="1131" y="189">Z</text><text x="1131" y="244">Z</text><text x="1131" y="299">Z</text><text x="1131" y="354">Z</text></g>
    <text x="882" y="402" class="code">θ ← classical optimizer / C(θ)</text>
  </g>
  <defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7Z" fill="{CYAN}"/></marker></defs>
''')
    body.append(end_svg())
    return "".join(body)


def quantum_panel() -> str:
    """Large, theoretically coherent hardware-efficient VQC diagram."""
    ys = [168, 228, 288, 348]
    wires = "".join(
        f'<path d="M112 {y}H1018" class="draw" style="--length:920;--delay:{.42 + i*.08:.2f}s"/>'
        for i, y in enumerate(ys)
    )

    def gates(x: int, label: str, color: str, delay: float, width: int = 52) -> str:
        return "".join(
            f'''<g class="reveal" style="--delay:{delay + i*.04:.2f}s">
              <rect x="{x}" y="{y-18}" width="{width}" height="36" rx="7" fill="#101a31" stroke="{color}"/>
              <text x="{x + width/2:.1f}" y="{y+4}" fill="{TEXT}" font-size="11" text-anchor="middle">{label}</text>
            </g>'''
            for i, y in enumerate(ys)
        )

    labels = "".join(
        f'<text x="54" y="{y+5}" class="small">q{i} |0⟩</text>' for i, y in enumerate(ys)
    )
    measurements = "".join(
        f'''<g class="reveal" style="--delay:{2.38 + i*.05:.2f}s">
          <rect x="932" y="{y-18}" width="60" height="36" rx="8" fill="#181333" stroke="{MAGENTA}"/>
          <text x="962" y="{y+4}" fill="{TEXT}" font-size="12" text-anchor="middle">⟨Z{i}⟩</text>
        </g>'''
        for i, y in enumerate(ys)
    )
    travelers = "".join(
        f'''<circle r="4.5" fill="{CYAN if i % 2 == 0 else PURPLE}" class="traveler">
          <animateMotion path="M112 {y}H1018" dur="3.8s" begin="{1.0 + i*.3}s" repeatCount="indefinite"/>
        </circle>'''
        for i, y in enumerate(ys)
    )

    body = [shell(1200, 480, "Variational quantum circuit",
                  "A four-qubit hardware-efficient variational circuit with data encoding, parameterized rotations, staggered linear entanglement and expectation-value measurement.")]
    body.append(f'''
  <defs>
    <marker id="qArrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{CYAN}"/></marker>
  </defs>
  <text x="42" y="49" class="eyebrow reveal" style="--delay:.18s">VARIATIONAL QUANTUM CIRCUIT / HARDWARE-EFFICIENT ANSATZ</text>
  <text x="1158" y="49" fill="{MUTED}" font-size="12" text-anchor="end" class="reveal" style="--delay:.28s">4 QUBITS · RY/RZ ROTATIONS · STAGGERED LINEAR CX</text>
  <rect x="32" y="76" width="1136" height="354" rx="19" class="panel" style="--panel-delay:.18s"/>

  <g class="reveal" style="--delay:.34s">{labels}</g>
  <g fill="none" stroke="#426688" stroke-width="1.5">{wires}</g>

  <g class="reveal" style="--delay:.5s"><text x="181" y="111" class="small" text-anchor="middle">DATA ENCODING</text></g>
  {gates(150, 'Rᵧ(xᵢ)', BLUE, .62, 62)}

  <g class="reveal" style="--delay:.85s"><text x="329" y="111" class="small" text-anchor="middle">ROTATION LAYER 1</text></g>
  {gates(274, 'Rᵧ(θ₁ᵢ)', PURPLE, .92, 52)}
  {gates(338, 'R𝓏(φ₁ᵢ)', PURPLE, 1.02, 52)}

  <g class="reveal" style="--delay:1.12s">
    <text x="447" y="111" class="small" text-anchor="middle">CX / PAIRS</text>
    <g stroke="{CYAN}" stroke-width="1.7" filter="url(#glow)">
      <path d="M430 {ys[0]}V{ys[1]}"/><path d="M470 {ys[2]}V{ys[3]}"/>
    </g>
    <g fill="{CYAN}"><circle cx="430" cy="{ys[0]}" r="5"/><circle cx="470" cy="{ys[2]}" r="5"/></g>
    <g fill="none" stroke="{CYAN}"><circle cx="430" cy="{ys[1]}" r="10"/><path d="M420 {ys[1]}H440M430 {ys[1]-10}V{ys[1]+10}"/><circle cx="470" cy="{ys[3]}" r="10"/><path d="M460 {ys[3]}H480M470 {ys[3]-10}V{ys[3]+10}"/></g>
  </g>

  <g class="reveal" style="--delay:1.34s"><text x="577" y="111" class="small" text-anchor="middle">ROTATION LAYER 2</text></g>
  {gates(522, 'Rᵧ(θ₂ᵢ)', PURPLE, 1.4, 52)}
  {gates(586, 'R𝓏(φ₂ᵢ)', PURPLE, 1.5, 52)}

  <g class="reveal" style="--delay:1.66s">
    <text x="687" y="111" class="small" text-anchor="middle">CX / BRIDGE</text>
    <path d="M687 {ys[1]}V{ys[2]}" stroke="{CYAN}" stroke-width="1.7" filter="url(#glow)"/>
    <circle cx="687" cy="{ys[1]}" r="5" fill="{CYAN}"/>
    <circle cx="687" cy="{ys[2]}" r="10" fill="none" stroke="{CYAN}"/><path d="M677 {ys[2]}H697M687 {ys[2]-10}V{ys[2]+10}" stroke="{CYAN}"/>
  </g>

  <g class="reveal" style="--delay:1.82s"><text x="817" y="111" class="small" text-anchor="middle">FINAL ROTATION</text></g>
  {gates(758, 'Rᵧ(θ₃ᵢ)', PURPLE, 1.88, 52)}
  {gates(822, 'R𝓏(φ₃ᵢ)', PURPLE, 1.98, 52)}

  <g class="reveal" style="--delay:2.16s"><text x="962" y="111" class="small" text-anchor="middle">OBSERVABLES</text></g>
  {measurements}
  <g fill="none" stroke="{CYAN}" stroke-width="2" opacity=".85">{travelers}</g>

  <g class="reveal" style="--delay:2.55s"><path d="M1018 383C1018 420 840 416 720 416H330C258 416 248 394 274 374" fill="none" stroke="{CYAN}" stroke-width="1.5" marker-end="url(#qArrow)" class="signal"/></g>
  <text x="1040" y="383" class="code reveal" style="--delay:2.5s">C(θ)</text>
  <text x="535" y="410" class="small reveal" style="--delay:2.65s">CLASSICAL OPTIMIZER UPDATES θ, φ</text>
  <text x="48" y="457" class="code reveal" style="--delay:2.75s">|ψ(x,θ)⟩ = Uvar(θ) Uenc(x) |0⟩^⊗4</text>
  <text x="1152" y="457" class="small reveal" text-anchor="end" style="--delay:2.82s">illustrative ansatz · topology should follow the target problem / hardware</text>
''')
    body.append(end_svg())
    return "".join(body)


def research_panel(research: dict) -> str:
    items = research["items"][:4]
    item_svg = []
    for i, item in enumerate(items):
        y = 124 + i * 70
        color = GREEN if item.get("status") == "active" else PURPLE
        item_svg.append(f'''
      <circle cx="59" cy="{y-5}" r="4" fill="{color}" class="pulse" style="--delay:{i*.35}s"/>
      <text x="75" y="{y}" fill="{TEXT}" font-size="15" font-weight="650">{e(item['title'])}</text>
      <text x="75" y="{y+23}" class="small">{e(item['detail'])}</text>''')

    nodes = [(908, 150), (908, 220), (908, 290), (986, 125), (986, 185), (986, 245), (986, 305), (1064, 150), (1064, 220), (1064, 290), (1140, 220)]
    layers = [nodes[:3], nodes[3:7], nodes[7:10], nodes[10:]]
    connection_groups = []
    for stage, (left, right) in enumerate(zip(layers, layers[1:])):
        paths = []
        for a in left:
            for b in right:
                paths.append(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}"/>')
        connection_groups.append(
            f'<g class="connectionStage" style="--edge-delay:{.65 + stage:.2f}s">{"".join(paths)}</g>'
        )
    node_svg = []
    for stage, layer in enumerate(layers):
        color = PURPLE if stage < 2 else CYAN
        for x, y in layer:
            node_svg.append(
                f'<g class="layerNode" style="--node-delay:{.55 + stage:.2f}s">'
                f'<circle cx="{x}" cy="{y}" r="12" fill="{color}" opacity=".13"/>'
                f'<circle cx="{x}" cy="{y}" r="6" fill="{color}" filter="url(#glow)"/></g>'
            )

    body = [shell(1200, 430, "Research systems", "Current research, fuzzy inference curves and neural signal flow.")]
    body.append(f'''
  <defs>
    <linearGradient id="lowFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{PURPLE}" stop-opacity=".52"/><stop offset="1" stop-color="{PURPLE}" stop-opacity=".03"/></linearGradient>
    <linearGradient id="midFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{CYAN}" stop-opacity=".5"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".03"/></linearGradient>
    <linearGradient id="highFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{MAGENTA}" stop-opacity=".5"/><stop offset="1" stop-color="{MAGENTA}" stop-opacity=".03"/></linearGradient>
  </defs>
  <text x="42" y="52" class="eyebrow reveal" style="--delay:.16s">CURRENT RESEARCH / SIGNAL MAP</text>
  <g class="reveal" style="--delay:.12s">
    <rect x="34" y="74" width="390" height="320" rx="18" class="panel" style="--panel-delay:.2s"/>
    {''.join(item_svg)}
  </g>
  <g class="reveal" style="--delay:.34s">
    <rect x="442" y="74" width="400" height="320" rx="18" class="panel2" style="--panel-delay:.36s"/>
    <text x="468" y="108" class="subheading">FUZZY INFERENCE</text>
    <text x="468" y="134" class="small">RULE OUTPUTS → MAX AGGREGATION → CENTROID</text>
    <path d="M480 335H811M492 350V158" stroke="#31506c"/>
    <g class="reveal" style="--delay:.78s">
      <path d="M492 328C525 328 535 178 582 178S640 328 672 328Z" fill="url(#lowFill)"/>
      <path d="M550 328C590 328 615 205 651 205S712 328 748 328Z" fill="url(#midFill)" style="mix-blend-mode:screen"/>
      <path d="M650 328C687 328 720 174 768 174S807 322 811 328Z" fill="url(#highFill)" style="mix-blend-mode:screen"/>
    </g>
    <path d="M492 328C525 328 535 178 582 178S640 328 672 328" fill="none" stroke="{PURPLE}" stroke-width="3" class="draw" style="--length:420;--delay:.55s"/>
    <path d="M550 328C590 328 615 205 651 205S712 328 748 328" fill="none" stroke="{CYAN}" stroke-width="3" class="draw" style="--length:420;--delay:.75s"/>
    <path d="M650 328C687 328 720 174 768 174S807 322 811 328" fill="none" stroke="{MAGENTA}" stroke-width="3" class="draw" style="--length:420;--delay:.95s"/>
    <path d="M674 169V329" stroke="#f8fbff" stroke-width="1.5" stroke-dasharray="5 7" class="draw" style="--length:180;--delay:1.2s"/>
    <circle cx="674" cy="328" r="5" fill="#f8fbff" class="pulse" filter="url(#glow)"/>
    <text x="684" y="183" fill="#f8fbff" font-size="12">y*</text>
    <text x="514" y="367" class="small">low</text><text x="641" y="367" class="small">medium</text><text x="760" y="367" class="small">high</text>
    <text x="492" y="157" class="code">y* = ∫ y μagg(y)dy / ∫ μagg(y)dy</text>
  </g>
  <g class="reveal" style="--delay:.58s">
    <rect x="860" y="74" width="306" height="320" rx="18" class="panel" style="--panel-delay:.58s"/>
    <text x="886" y="108" class="subheading">NEURAL SIGNAL FLOW</text>
    <text x="886" y="134" class="small">INPUT → HIDDEN → OUTPUT</text>
    <g stroke="#356187" stroke-width="1.15">{''.join(connection_groups)}</g>
    {''.join(node_svg)}
    <g>
      <circle r="4.5" fill="{MAGENTA}" class="traveler"><animateMotion path="M908 150L986 125L1064 150L1140 220" dur="4s" begin="1.1s" repeatCount="indefinite"/></circle>
      <circle r="4.5" fill="{CYAN}" class="traveler"><animateMotion path="M908 220L986 245L1064 220L1140 220" dur="4s" begin="2.0s" repeatCount="indefinite"/></circle>
      <circle r="4.5" fill="{PURPLE}" class="traveler"><animateMotion path="M908 290L986 305L1064 290L1140 220" dur="4s" begin="2.9s" repeatCount="indefinite"/></circle>
    </g>
    <text x="886" y="352" class="code">aˡ⁺¹ = σ(Wˡaˡ + bˡ)</text>
    <text x="886" y="374" class="small">ACTIVATION PROPAGATES LAYER BY LAYER</text>
  </g>
''')
    body.append(end_svg())
    return "".join(body)


def projects_panel(projects: list[dict]) -> str:
    cards = []
    for i, project in enumerate(projects[:6]):
        col, row = i % 2, i // 2
        x, y = 34 + col * 583, 84 + row * 194
        delay = .12 + i * .09
        description = text_lines(project["description"], x + 24, y + 92, width=60, step=21, maximum=2)
        cards.append(f'''
  <g class="reveal" style="--delay:{delay:.2f}s">
    <rect x="{x}" y="{y}" width="550" height="166" rx="17" class="{'panel2' if i % 3 == 1 else 'panel'}"/>
    <rect x="{x}" y="{y}" width="5" height="166" rx="2.5" fill="{'url(#accent)' if i % 2 == 0 else PURPLE}"/>
    <text x="{x+24}" y="{y+31}" class="eyebrow">{e(project['category'])}</text>
    <text x="{x+24}" y="{y+63}" class="heading">{e(project['name'])}</text>
    {description}
    <text x="{x+24}" y="{y+145}" class="small">{e(project['language'])}</text>
    <text x="{x+526}" y="{y+145}" fill="{CYAN}" font-size="12" text-anchor="end">{e(project['connection'])}</text>
  </g>''')

    body = [shell(1200, 690, "Selected projects", "Six selected projects connecting research ideas to working code.")]
    body.append('  <text x="42" y="52" class="eyebrow reveal" style="--delay:.16s">SELECTED BUILDS / RESEARCH → CODE</text>\n')
    body.extend(cards)
    body.append(end_svg())
    return "".join(body)


def publications_panel(publications: dict) -> str:
    items = publications.get("items", [])[:4]
    rows = []
    for i, item in enumerate(items):
        y = 116 + i * 82
        title = lines(item["title"], 73, 1)[0]
        rows.append(f'''
    <g class="reveal" style="--delay:{.18 + i*.12:.2f}s">
      <rect x="48" y="{y-34}" width="1104" height="68" rx="12" fill="#09162a" stroke="#183b5f"/>
      <text x="72" y="{y-5}" fill="{PURPLE}" font-size="15" font-weight="700">{e(item.get('year', '—'))}</text>
      <text x="132" y="{y-7}" fill="{TEXT}" font-size="15" font-weight="650">{e(title)}</text>
      <text x="132" y="{y+17}" class="small">{e(item.get('venue', 'venue pending'))}</text>
      <rect x="938" y="{y-18}" width="190" height="28" rx="14" fill="#171334" stroke="#513d80"/>
      <text x="1033" y="{y+1}" fill="{PURPLE}" font-size="11" text-anchor="middle">{e(item.get('status', 'status pending').upper())}</text>
    </g>''')
    height = max(250, 160 + len(items) * 82)
    body = [shell(1200, height, "Publications", "Publication entries with explicit review status.")]
    body.append(f'''
  <text x="42" y="52" class="eyebrow reveal" style="--delay:.16s">PUBLICATIONS / TALKS / WRITING</text>
  <text x="1158" y="52" fill="{MAGENTA}" font-size="12" text-anchor="end" class="reveal" style="--delay:.28s">LIST UNDER REVIEW · EDIT data/publications.json</text>
  {''.join(rows) if rows else '<text x="60" y="130" class="body">Publication data is being updated.</text>'}
''')
    body.append(end_svg())
    return "".join(body)


def stats_panel(stats: dict) -> str:
    metrics = [
        ("PUBLIC REPOS", stats.get("public_repos", "—")),
        ("FOLLOWERS", stats.get("followers", "—")),
        ("STARS RECEIVED", stats.get("stars_received", "—")),
        ("FOLLOWING", stats.get("following", "—")),
    ]
    metric_svg = []
    for i, (label, value) in enumerate(metrics):
        x = 54 + i * 190
        metric_svg.append(f'''
    <g class="reveal" style="--delay:{.1+i*.08:.2f}s"><text x="{x}" y="91" class="small">{label}</text><text x="{x}" y="135" fill="{PURPLE if i % 2 else CYAN}" font-size="34" font-weight="700">{e(value)}</text></g>''')
    lang = stats.get("top_languages", [])[:4]
    total = sum(int(x.get("repositories", 0)) for x in lang) or 1
    bar_x, bar_y, bar_w = 830, 100, 310
    bars, labels_svg = [], []
    cursor = bar_x
    colors = [CYAN, PURPLE, BLUE, MAGENTA]
    for i, entry in enumerate(lang):
        width = bar_w * int(entry.get("repositories", 0)) / total
        bars.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{width:.1f}" height="13" fill="{colors[i]}"/>')
        labels_svg.append(f'<circle cx="{bar_x + (i%2)*155}" cy="{132 + (i//2)*24}" r="4" fill="{colors[i]}"/><text x="{bar_x+12+(i%2)*155}" y="{136+(i//2)*24}" class="small">{e(entry.get("name", ""))}</text>')
        cursor += width
    updated = refreshed_label(stats.get("refreshed_at"))
    body = [shell(1200, 205, "GitHub activity snapshot", "Public GitHub repository and follower metrics.")]
    body.append(f'''
  <text x="42" y="47" class="eyebrow reveal" style="--delay:.16s">GITHUB SIGNAL / PUBLIC SNAPSHOT</text>
  {''.join(metric_svg)}
  <g class="reveal" style="--delay:.34s"><path d="M795 58V166" stroke="#183b5f"/><text x="830" y="72" class="small">REPOSITORY LANGUAGES</text></g>
  <g class="reveal" style="--delay:.45s"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="13" rx="6" fill="#13233a"/>{''.join(bars)}{''.join(labels_svg)}</g>
  <text x="1140" y="184" class="small reveal" text-anchor="end" style="--delay:.52s">REFRESHED {e(updated)} · GITHUB API</text>
''')
    body.append(end_svg())
    return "".join(body)


def request_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "EduardoTBuss-profile-generator"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def refresh_github() -> dict:
    user = request_json("https://api.github.com/users/EduardoTBuss")
    repos = request_json("https://api.github.com/users/EduardoTBuss/repos?per_page=100&sort=updated")
    owned = [repo for repo in repos if not repo.get("fork")]
    language_counts = Counter(repo.get("language") for repo in owned if repo.get("language"))
    value = {
        "username": user["login"],
        "public_repos": user["public_repos"],
        "followers": user["followers"],
        "following": user["following"],
        "stars_received": sum(repo.get("stargazers_count", 0) for repo in owned),
        "forks_received": sum(repo.get("forks_count", 0) for repo in owned),
        "top_languages": [
            {"name": name, "repositories": count}
            for name, count in language_counts.most_common(6)
        ],
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_json("github.json", value)
    return value


def scale_seconds(svg: str, factor: float) -> str:
    """Slow every CSS/SMIL time literal in an SVG by a fixed factor."""
    pattern = re.compile(r"(?<![A-Za-z0-9_.])(\d*\.?\d+)s")

    def repl(match: re.Match[str]) -> str:
        return f"{float(match.group(1)) * factor:.3f}".rstrip("0").rstrip(".") + "s"

    return pattern.sub(repl, svg)


def nested_module(svg: str, prefix: str, y: int, width: int, height: int,
                  section_delay: float) -> str:
    """Namespace and place a standalone SVG inside the unified profile SVG."""
    svg = scale_seconds(svg, 1.45)
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{prefix}-{m.group(1)})', svg)
    svg = re.sub(
        r'aria-labelledby="([^"]+)"',
        lambda m: 'aria-labelledby="' + " ".join(f"{prefix}-{part}" for part in m.group(1).split()) + '"',
        svg,
    )
    class_names = [
        "panel2", "panel", "reveal", "draw", "pulse", "signal", "float",
        "gridBoot", "borderBoot", "cornerBoot", "scan", "layerNode",
        "connectionStage", "traveler",
    ]
    keyframe_names = [
        "panelBuild", "reveal", "draw", "pulse", "signal", "float",
        "gridBoot", "scan", "layerNode", "connectionGlow",
    ]
    class_map = {name: f"{prefix}-{name}" for name in class_names}
    for name, replacement in class_map.items():
        svg = re.sub(rf"\.{re.escape(name)}\b", f".{replacement}", svg)

    def replace_classes(match: re.Match[str]) -> str:
        values = [class_map.get(value, value) for value in match.group(1).split()]
        return f'class="{" ".join(values)}"'

    svg = re.sub(r'class="([^"]+)"', replace_classes, svg)
    for name in keyframe_names:
        replacement = f"{prefix}-{name}"
        svg = re.sub(rf"@keyframes\s+{re.escape(name)}\b", f"@keyframes {replacement}", svg)
        svg = re.sub(rf"animation:\s*{re.escape(name)}\b", f"animation: {replacement}", svg)
    svg = re.sub(
        r'begin="(\d*\.?\d+)s"',
        lambda m: f'begin="{float(m.group(1)) + section_delay:.3f}s"',
        svg,
    )

    opening = re.match(r"<svg[^>]*>", svg)
    if not opening:
        raise ValueError(f"Invalid SVG module: {prefix}")
    inner = svg[opening.end():svg.rfind("</svg>")]
    inner = re.sub(
        rf'<rect width="{width}" height="{height}" rx="22" fill="url\(#{prefix}-bg\)"/>',
        "",
        inner,
        count=1,
    )
    return (
        f'<svg x="0" y="{y}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" style="--section-delay:{section_delay}s">{inner}</svg>'
    )


def full_profile(modules: list[tuple[str, str, int, float]]) -> str:
    """Build one tall, self-contained SVG from independent animated modules."""
    gap = 18
    width = 1200
    y = 0
    nested = []
    boundaries = []
    for prefix, svg, height, delay in modules:
        nested.append(nested_module(svg, prefix, y, width, height, delay))
        y += height
        boundaries.append(y + gap / 2)
        y += gap
    total_height = y - gap
    links = []
    for i, boundary in enumerate(boundaries[:-1]):
        links.append(
            f'<path d="M18 {boundary:.1f}H1182" class="sectionLink" '
            f'style="--link-delay:{1.0 + i*.72:.2f}s"/>'
            f'<circle cx="18" cy="{boundary:.1f}" r="4" class="junction" '
            f'style="--junction-delay:{1.0 + i*.72:.2f}s"/>'
            f'<circle cx="1182" cy="{boundary:.1f}" r="4" class="junction" '
            f'style="--junction-delay:{1.18 + i*.72:.2f}s"/>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}" role="img" aria-labelledby="profile-title profile-desc">
  <title id="profile-title">Eduardo Timm Buss — animated research profile</title>
  <desc id="profile-desc">One large scientific interface assembled from an empty field over approximately six seconds.</desc>
  <style>
    .fieldGrid {{ opacity: 0; animation: fieldIn 1.8s ease forwards; }}
    .systemBus {{ fill: none; stroke: url(#rootAccent); stroke-width: 1.6; stroke-dasharray: {total_height * 2}; stroke-dashoffset: {total_height * 2}; animation: rootDraw 6s linear forwards; }}
    .sectionLink {{ fill: none; stroke: #1b5a7b; stroke-width: 1; stroke-dasharray: 1180; stroke-dashoffset: 1180; animation: linkDraw .9s ease forwards; animation-delay: var(--link-delay); }}
    .junction {{ fill: #29e6f2; opacity: 0; filter: url(#rootGlow); animation: junctionIn 1.8s ease-in-out infinite; animation-delay: var(--junction-delay); }}
    .rootScan {{ animation: rootScan 6s linear forwards; }}
    @keyframes fieldIn {{ to {{ opacity: .8; }} }}
    @keyframes rootDraw {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes linkDraw {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes junctionIn {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
    @keyframes rootScan {{ 0% {{ transform: translateY(0); opacity: 0; }} 6% {{ opacity: .75; }} 94% {{ opacity: .35; }} 100% {{ transform: translateY({total_height}px); opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .fieldGrid, .systemBus, .sectionLink, .junction, .rootScan {{ animation-duration: .001ms !important; animation-delay: 0s !important; animation-iteration-count: 1 !important; animation-fill-mode: both !important; }}
    }}
  </style>
  <defs>
    <linearGradient id="rootBackground" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#030713"/><stop offset=".48" stop-color="#061326"/><stop offset="1" stop-color="#080817"/></linearGradient>
    <linearGradient id="rootAccent" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#29e6f2"/><stop offset=".52" stop-color="#38bdf8"/><stop offset="1" stop-color="#a78bfa"/></linearGradient>
    <pattern id="rootGrid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="#123050" stroke-opacity=".22"/></pattern>
    <filter id="rootGlow" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{width}" height="{total_height}" fill="url(#rootBackground)"/>
  <rect width="{width}" height="{total_height}" fill="url(#rootGrid)" class="fieldGrid"/>
  {''.join(nested)}
  <path d="M14 22V{total_height - 22}M1186 22V{total_height - 22}" class="systemBus"/>
  {''.join(links)}
  <rect x="18" y="0" width="1164" height="2" rx="1" fill="url(#rootAccent)" opacity="0" class="rootScan" filter="url(#rootGlow)"/>
</svg>'''


def dashboard_profile(profile: dict, research: dict, projects: list[dict],
                      publications: dict, stats: dict) -> str:
    """Generate the responsive horizontal dashboard used by the README."""
    research_rows = []
    for i, item in enumerate(research.get("items", [])[:4]):
        y = 375 + i * 100
        color = "var(--green)" if item.get("status") == "active" else "var(--purple)"
        status = item.get("status", "active").upper()
        detail = lines(item.get("detail", ""), 38, 1)[0]
        research_rows.append(f'''
      <g class="reveal" style="--d:{1.25 + i*.18:.2f}s">
        <circle cx="58" cy="{y-5}" r="4" fill="{color}"/>
        <text x="75" y="{y}" class="itemTitle">{e(item['title'])}</text>
        <text x="75" y="{y+23}" class="small fine">{e(detail)}</text>
        <text x="392" y="{y+23}" class="researchStatus fine" text-anchor="end" style="fill:{color}">{e(status)}</text>
      </g>''')

    publication_rows = []
    for i, item in enumerate(publications.get("items", [])[:3]):
        y = 795 + i * 91
        title = lines(item.get("title", "Untitled"), 42, 1)[0]
        publication_rows.append(f'''
      <g class="reveal" style="--d:{2.55 + i*.22:.2f}s">
        <rect x="50" y="{y-30}" width="350" height="72" rx="11" class="inner"/>
        <text x="68" y="{y-4}" class="year">{e(item.get('year', '—'))}</text>
        <text x="116" y="{y-5}" class="pubTitle">{e(title)}</text>
        <text x="116" y="{y+19}" class="tiny">{e(item.get('venue', 'venue pending'))}</text>
        <text x="382" y="{y+19}" class="status" text-anchor="end">{e(item.get('status', 'review pending').upper())}</text>
      </g>''')

    project_cards = []
    for i, project in enumerate(projects[:6]):
        col, row = i % 3, i // 3
        x, y = 455 + col * 300, 780 + row * 144
        name = lines(project.get("name", "project"), 26, 1)[0]
        connection = lines(project.get("connection", "research → code"), 34, 1)[0]
        description = lines(project.get("description", ""), 39, 1)[0]
        project_cards.append(f'''
      <g class="reveal" style="--d:{2.75 + i*.16:.2f}s">
        <rect x="{x}" y="{y}" width="282" height="126" rx="13" class="inner"/>
        <rect x="{x}" y="{y}" width="4" height="126" rx="2" fill="{'var(--cyan)' if i % 2 == 0 else 'var(--purple)'}"/>
        <text x="{x+18}" y="{y+27}" class="cardTag">{e(project.get('category', 'PROJECT'))}</text>
        <text x="{x+18}" y="{y+55}" class="cardTitle">{e(name)}</text>
        <text x="{x+18}" y="{y+77}" class="tiny fine">{e(description)}</text>
        <text x="{x+18}" y="{y+96}" class="tiny">{e(project.get('language', ''))}</text>
        <text x="{x+18}" y="{y+114}" class="cardLink">{e(connection)}</text>
      </g>''')

    neural_layers = [
        [(914, 105), (914, 160), (914, 215)],
        [(1030, 83), (1030, 132), (1030, 181), (1030, 230)],
        [(1160, 105), (1160, 160), (1160, 215)],
        [(1305, 160)],
    ]
    edge_groups = []
    edge_back_groups = []
    for stage, (left, right) in enumerate(zip(neural_layers, neural_layers[1:])):
        paths = "".join(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}"/>' for a in left for b in right)
        edge_groups.append(f'<g class="edgeStage" style="--stage:{stage*.92:.2f}s">{paths}</g>')
        edge_back_groups.append(f'<g class="edgeBack" style="--stage:{(2-stage)*.68:.2f}s">{paths}</g>')
    neural_nodes = []
    for stage, layer in enumerate(neural_layers):
        color = "var(--purple)" if stage < 2 else "var(--cyan)"
        for x, y in layer:
            neural_nodes.append(f'''
        <g class="layerStage" style="--stage:{stage*.92:.2f}s">
          <circle cx="{x}" cy="{y}" r="13" fill="{color}" opacity=".12"/>
          <circle cx="{x}" cy="{y}" r="6" fill="{color}"/>
        </g>''')

    language_items = stats.get("top_languages", [])[:4]
    language_total = sum(int(item.get("repositories", 0)) for item in language_items) or 1
    language_bars = []
    language_labels = []
    cursor = 1015.0
    language_colors = ["var(--cyan)", "var(--purple)", "var(--blue)", "var(--magenta)"]
    for i, item in enumerate(language_items):
        width = 300 * int(item.get("repositories", 0)) / language_total
        language_bars.append(f'<rect x="{cursor:.1f}" y="1137" width="{width:.1f}" height="13" fill="{language_colors[i]}"/>')
        language_labels.append(f'{e(item.get("name", "?"))} {e(item.get("repositories", 0))}')
        cursor += width

    # Pseudo-random but deterministic micro-particles; no runtime JS is required.
    variation = max(0.0, min(1.0, float(aleatoriedade_particula)))
    particle_size = max(0.15, float(tamanho_particula))
    particle_count = int(92 + variation * 64)
    dust_particles = []
    for i in range(particle_count):
        wave = abs(math.sin(i * 12.9898 + 4.1414))
        eddy = math.sin(i * 7.233 + 1.73)
        x = int((53 + i * 137 + eddy * 170 * variation) % 1392)
        y = int((37 + i * i * 29 + i * 61 + eddy * 95 * variation) % 1212)
        rx = particle_size * (.55 + wave * (.48 + .32 * variation))
        ry = particle_size * (.28 + (1 - wave) * (.18 + .12 * variation))
        opacity = .10 + wave * (.08 + .07 * variation)
        duration = int(12 + (1 - wave) * 17 + (1 - variation) * 7)
        delay = int((i * 11 + wave * 19) % 31)
        motion = ("dustA", "dustB", "dustC")[int(wave * 997) % 3]
        dust_particles.append(
            f'<ellipse cx="{x}" cy="{y}" rx="{rx:.2f}" ry="{ry:.2f}" '
            f'fill="{e(cor_particula)}" opacity="{opacity:.3f}" '
            f'class="dust {motion}" style="--dur:{duration}s;--delay:-{delay}s"/>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1220" viewBox="0 0 1400 1220" role="img" aria-labelledby="dashboard-title dashboard-desc">
  <title id="dashboard-title">Eduardo Timm Buss — adaptive research dashboard</title>
  <desc id="dashboard-desc">A responsive horizontal scientific profile with one quantum machine-learning circuit, fuzzy inference, layer-by-layer neural propagation, projects, publications and GitHub activity.</desc>
  <style>
    :root {{ --bg:#040916; --bg2:#081326; --panel:#09162a; --inner:#0d1d35; --text:#e8f4ff; --muted:#91a8bd; --line:#1a4267; --grid:#143656; --cyan:#29e6f2; --blue:#38bdf8; --purple:#a78bfa; --magenta:#d56dff; --green:#52e0a4; }}
    text {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace; }}
    .bg {{ fill:var(--bg); }} .grid {{ opacity:0; animation:gridIn 1.8s ease forwards; }}
    .panel {{ fill:var(--panel); stroke:var(--line); stroke-width:1.2; stroke-opacity:.68; fill-opacity:0; stroke-dasharray:2400; stroke-dashoffset:2400; animation:panelBuild 1.45s ease forwards; animation-delay:var(--d,0s); }}
    .inner {{ fill:var(--inner); stroke:var(--line); stroke-width:1; }}
    .reveal {{ opacity:0; transform:translateY(7px); animation:reveal .82s ease forwards; animation-delay:var(--d,0s); }}
    .trace {{ stroke-dasharray:var(--len,900); stroke-dashoffset:var(--len,900); animation:trace 1.9s ease forwards; animation-delay:var(--d,0s); }}
    .eyebrow {{ fill:var(--cyan); font-size:13px; font-weight:750; letter-spacing:1.8px; }}
    .name {{ fill:var(--text); font-size:34px; font-weight:760; }}
    .handle {{ fill:var(--purple); font-size:19px; font-weight:700; }}
    .heading {{ fill:var(--text); font-size:20px; font-weight:720; }}
    .subheading {{ fill:var(--purple); font-size:16px; font-weight:720; }}
    .body {{ fill:var(--muted); font-size:14px; }} .small {{ fill:var(--muted); font-size:12px; }} .tiny {{ fill:var(--muted); font-size:10px; }}
    .code {{ fill:var(--cyan); font-size:12px; }} .itemTitle {{ fill:var(--text); font-size:14px; font-weight:680; }}
    .year {{ fill:var(--purple); font-size:13px; font-weight:750; }} .pubTitle {{ fill:var(--text); font-size:12px; font-weight:680; }} .status,.researchStatus {{ fill:var(--purple); font-size:9px; font-weight:700; letter-spacing:.5px; }}
    .cardTag {{ fill:var(--cyan); font-size:10px; font-weight:750; letter-spacing:1px; }} .cardTitle {{ fill:var(--text); font-size:15px; font-weight:720; }} .cardLink {{ fill:var(--cyan); font-size:10px; }}
    .edgeStage {{ stroke:var(--line); stroke-width:1; opacity:0; animation:edgeSweep 4.8s ease-in-out infinite both; animation-delay:calc(1.5s + var(--stage)); }}
    .edgeBack {{ stroke:var(--purple); stroke-width:1.2; opacity:0; animation:edgeBack 6.2s ease-in-out infinite both; animation-delay:calc(4.6s + var(--stage)); }}
    .layerStage {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:layerSweep 4.8s ease-in-out infinite both; animation-delay:calc(1.5s + var(--stage)); }}
    .gatePulse {{ animation:gatePulse 6s ease-in-out infinite; animation-delay:var(--pulse,0s); }}
    .sphereAura {{ animation:sphereAura 4.6s ease-in-out infinite; transform-box:fill-box; transform-origin:center; }}
    .orbit {{ stroke-dasharray:7 11; animation:orbitDash 7s linear infinite; }}
    .dust {{ pointer-events:none; transform-box:fill-box; transform-origin:center; animation-duration:var(--dur); animation-delay:var(--delay); animation-timing-function:ease-in-out; animation-iteration-count:infinite; animation-direction:alternate; }}
    .dustA {{ animation-name:dustA; }} .dustB {{ animation-name:dustB; }} .dustC {{ animation-name:dustC; }}
    .flowNode {{ fill:var(--inner); stroke:var(--cyan); stroke-width:1; }} .chip {{ fill:var(--inner); stroke:var(--line); stroke-width:1; }}
    .signal {{ stroke-dasharray:5 12; animation:signal 3.2s linear infinite; }}
    .scan {{ animation:scan 6s linear forwards; }} .bus {{ stroke-dasharray:5200; stroke-dashoffset:5200; animation:trace 6s linear forwards; }}
    @keyframes gridIn {{ to {{ opacity:.75; }} }} @keyframes reveal {{ to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes trace {{ to {{ stroke-dashoffset:0; }} }}
    @keyframes panelBuild {{ 0% {{ fill-opacity:0; stroke-dashoffset:2400; }} 58% {{ fill-opacity:0; stroke-dashoffset:0; }} 100% {{ fill-opacity:.72; stroke-dashoffset:0; }} }}
    @keyframes edgeSweep {{ 0%,18% {{ opacity:0; }} 28%,48% {{ opacity:.9; stroke:var(--cyan); }} 62%,100% {{ opacity:.16; }} }}
    @keyframes edgeBack {{ 0%,12% {{ opacity:0; }} 18%,28% {{ opacity:.82; }} 38%,100% {{ opacity:0; }} }}
    @keyframes layerSweep {{ 0%,18% {{ opacity:0; transform:scale(.88); }} 28%,48% {{ opacity:1; transform:scale(1.3); filter:url(#glow); }} 62%,100% {{ opacity:.38; transform:scale(1); }} }}
    @keyframes gatePulse {{ 0%,64%,100% {{ filter:none; }} 70%,80% {{ filter:url(#glow); stroke-width:2; }} }}
    @keyframes sphereAura {{ 0%,100% {{ opacity:.5; transform:scale(.98); }} 50% {{ opacity:1; transform:scale(1.02); }} }}
    @keyframes orbitDash {{ to {{ stroke-dashoffset:-180; }} }}
    @keyframes dustA {{ 0% {{ transform:translate(-18px,2px); }} 34% {{ transform:translate(16px,-5px); }} 71% {{ transform:translate(57px,7px); }} 100% {{ transform:translate(102px,-3px); }} }}
    @keyframes dustB {{ 0% {{ transform:translate(-12px,-4px); }} 29% {{ transform:translate(22px,8px); }} 63% {{ transform:translate(64px,-9px); }} 100% {{ transform:translate(91px,5px); }} }}
    @keyframes dustC {{ 0% {{ transform:translate(-25px,6px); }} 38% {{ transform:translate(31px,-11px); }} 76% {{ transform:translate(73px,4px); }} 100% {{ transform:translate(116px,-7px); }} }}
    @keyframes signal {{ to {{ stroke-dashoffset:-68; }} }} @keyframes scan {{ 0% {{ transform:translateY(0); opacity:0; }} 7% {{ opacity:.8; }} 94% {{ opacity:.3; }} 100% {{ transform:translateY(1220px); opacity:0; }} }}
    @media (prefers-color-scheme:light) {{ :root {{ --bg:#f3f7fd; --bg2:#e6eef9; --panel:#ffffff; --inner:#f2f7fc; --text:#132238; --muted:#4c6078; --line:#9ebbd2; --grid:#bfd2e3; --cyan:#007c91; --blue:#0369a1; --purple:#6d28d9; --magenta:#a21caf; --green:#087f5b; }} }}
    @media (max-width:900px) {{ .fine {{ display:none; }} .body {{ font-size:15px; }} .small {{ font-size:13px; }} .cardTitle {{ font-size:16px; }} }}
    @media (prefers-reduced-motion:reduce) {{ .grid,.panel,.reveal,.trace,.edgeStage,.edgeBack,.layerStage,.gatePulse,.sphereAura,.orbit,.signal,.scan,.bus {{ animation-duration:.001ms!important; animation-delay:0s!important; animation-iteration-count:1!important; animation-fill-mode:both!important; }} .dust {{ animation:none!important; opacity:.08!important; }} }}
  </style>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="1"><stop stop-color="var(--bg)"/><stop offset=".5" stop-color="var(--bg2)"/><stop offset="1" stop-color="var(--bg)"/></linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop stop-color="var(--cyan)"/><stop offset=".55" stop-color="var(--blue)"/><stop offset="1" stop-color="var(--purple)"/></linearGradient>
    <linearGradient id="lowFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="var(--purple)" stop-opacity=".55"/><stop offset="1" stop-color="var(--purple)" stop-opacity=".03"/></linearGradient>
    <linearGradient id="midFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="var(--cyan)" stop-opacity=".5"/><stop offset="1" stop-color="var(--cyan)" stop-opacity=".03"/></linearGradient>
    <linearGradient id="highFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="var(--magenta)" stop-opacity=".5"/><stop offset="1" stop-color="var(--magenta)" stop-opacity=".03"/></linearGradient>
    <radialGradient id="sphereCore"><stop stop-color="var(--cyan)" stop-opacity=".14"/><stop offset=".52" stop-color="var(--blue)" stop-opacity=".06"/><stop offset="1" stop-color="var(--purple)" stop-opacity="0"/></radialGradient>
    <pattern id="dashboardGrid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="var(--grid)" stroke-opacity=".24"/></pattern>
    <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="var(--cyan)"/></marker>
  </defs>
  <rect width="1400" height="1220" fill="url(#background)"/>
  <rect width="1400" height="1220" fill="url(#dashboardGrid)" class="grid"/>
  <!-- Layer 1: translucent module surfaces -->
  <g aria-label="dashboard panel surfaces">
    <rect x="30" y="30" width="390" height="250" rx="17" class="panel" style="--d:.12s"/>
    <rect x="435" y="30" width="420" height="405" rx="17" class="panel" style="--d:.32s"/>
    <rect x="870" y="30" width="500" height="260" rx="17" class="panel" style="--d:.5s"/>
    <rect x="30" y="295" width="390" height="420" rx="17" class="panel" style="--d:.75s"/>
    <rect x="870" y="305" width="500" height="410" rx="17" class="panel" style="--d:.92s"/>
    <rect x="435" y="450" width="420" height="265" rx="17" class="panel" style="--d:1.2s"/>
    <rect x="30" y="730" width="390" height="335" rx="17" class="panel" style="--d:1.9s"/>
    <rect x="435" y="730" width="935" height="335" rx="17" class="panel" style="--d:2.15s"/>
    <rect x="30" y="1080" width="1340" height="110" rx="17" class="panel" style="--d:3.65s"/>
  </g>
  <!-- Layer 2: ambient particles above surfaces, below all meaningful content -->
  <g aria-hidden="true">{''.join(dust_particles)}</g>
  <rect x="1" y="1" width="1398" height="1218" rx="22" fill="none" stroke="var(--line)" class="bus"/>
  <rect x="20" y="0" width="1360" height="2" fill="url(#accent)" opacity="0" class="scan" filter="url(#glow)"/>

  <!-- Layer 3: headings, diagrams, cards and data -->
  <!-- Identity -->
  <g class="reveal" style="--d:.34s">
    <text x="54" y="64" class="eyebrow">RESEARCH PROFILE / ONLINE</text>
    <text x="54" y="111" class="name">{e(profile['name'])}</text>
    <text x="54" y="139" class="handle">@{e(profile['username'])}</text>
    <text x="54" y="174" class="subheading">{e(profile['role'])}</text>
    <text x="54" y="199" class="body">{e(profile['subtitle'])}</text>
    {text_lines(profile['bio'], 54, 229, width=48, step=20, css='small fine', maximum=2)}
    <text x="54" y="263" class="code">{e(profile['location'])}</text>
  </g>

  <!-- Bloch state: scientific identity, not a second VQC -->
  <text x="459" y="64" class="eyebrow reveal" style="--d:.5s">QUANTUM STATE / BLOCH SPHERE</text>
  <g class="reveal" style="--d:.66s">
    <circle cx="645" cy="240" r="151" fill="url(#sphereCore)" stroke="var(--cyan)" stroke-opacity=".18" class="sphereAura" filter="url(#glow)"/>
    <circle cx="645" cy="240" r="145" fill="none" stroke="var(--blue)" stroke-width="1.5" class="trace" style="--len:920;--d:.8s"/>
    <ellipse cx="645" cy="240" rx="145" ry="47" fill="none" stroke="var(--purple)" stroke-width="1.4" class="trace" style="--len:700;--d:1.05s"/>
    <ellipse cx="645" cy="240" rx="58" ry="145" fill="none" stroke="var(--cyan)" opacity=".5" class="trace" style="--len:800;--d:1.25s"/>
    <ellipse cx="645" cy="190" rx="132" ry="34" fill="none" stroke="var(--cyan)" opacity=".22" class="orbit"/>
    <ellipse cx="645" cy="290" rx="132" ry="34" fill="none" stroke="var(--purple)" opacity=".24" class="orbit"/>
    <path d="M493 240H797M645 84V396M530 338L760 142" fill="none" stroke="var(--muted)" opacity=".7" class="trace" style="--len:900;--d:1.38s"/>
    <path d="M645 240H729V141M645 141H729" fill="none" stroke="var(--cyan)" stroke-dasharray="4 7" opacity=".5" class="trace" style="--len:260;--d:1.55s"/>
    <path d="M645 240L729 141" stroke="var(--cyan)" stroke-width="3" marker-end="url(#arrow)" class="trace" style="--len:140;--d:1.65s" filter="url(#glow)"/>
    <path d="M702 173A72 72 0 0 0 645 154" fill="none" stroke="var(--magenta)" stroke-width="2" class="trace" style="--len:150;--d:1.85s"/>
    <circle cx="729" cy="240" r="3" fill="var(--cyan)" opacity=".75"/><circle cx="645" cy="141" r="3" fill="var(--cyan)" opacity=".75"/>
    <circle cx="729" cy="141" r="7" fill="var(--cyan)" filter="url(#glow)"/>
    <text x="739" y="137" class="code">|ψ⟩</text><text x="690" y="169" fill="var(--magenta)" font-size="14">θ</text>
    <text x="633" y="77" class="small">|0⟩</text><text x="633" y="392" class="small">|1⟩</text>
  </g>
  <g class="reveal fine" style="--d:2.05s">
    <rect x="459" y="404" width="88" height="25" rx="12" class="chip"/><text x="503" y="421" class="tiny" text-anchor="middle">QUANTUM</text>
    <rect x="554" y="404" width="88" height="25" rx="12" class="chip"/><text x="598" y="421" class="tiny" text-anchor="middle">FUZZY</text>
    <rect x="649" y="404" width="88" height="25" rx="12" class="chip"/><text x="693" y="421" class="tiny" text-anchor="middle">AI / ML</text>
    <rect x="744" y="404" width="87" height="25" rx="12" class="chip"/><text x="787" y="421" class="tiny" text-anchor="middle">VISION</text>
  </g>

  <!-- Neural flow: no traveling particles, only staged layer activation -->
  <text x="894" y="64" class="eyebrow reveal" style="--d:.7s">NEURAL SIGNAL FLOW / LAYER PROPAGATION</text>
  <g stroke="var(--line)">{''.join(edge_groups)}</g>
  <g>{''.join(edge_back_groups)}</g>
  <g>{''.join(neural_nodes)}</g>
  <text x="1340" y="248" class="tiny reveal fine" text-anchor="end" style="--d:1.25s">FORWARD → REPRESENTATION → OUTPUT</text>
  <text x="1340" y="264" class="tiny reveal fine" text-anchor="end" style="--d:1.35s" fill="var(--purple)">GRADIENT ← LAYER-WISE UPDATE</text>

  <!-- Current research -->
  <text x="54" y="329" class="eyebrow reveal" style="--d:.95s">CURRENT RESEARCH</text>
  {''.join(research_rows)}
  <g class="reveal fine" style="--d:2.0s">
    <path d="M64 677H382" stroke="var(--line)" class="trace" style="--len:320;--d:2.1s"/>
    <circle cx="64" cy="677" r="6" class="flowNode"/><circle cx="170" cy="677" r="6" class="flowNode"/><circle cx="276" cy="677" r="6" class="flowNode"/><circle cx="382" cy="677" r="6" class="flowNode"/>
    <text x="64" y="700" class="tiny" text-anchor="middle">THEORY</text><text x="170" y="700" class="tiny" text-anchor="middle">SIMULATE</text><text x="276" y="700" class="tiny" text-anchor="middle">IMPLEMENT</text><text x="382" y="700" class="tiny" text-anchor="middle">VALIDATE</text>
  </g>

  <!-- One and only VQC -->
  <text x="894" y="339" class="eyebrow reveal" style="--d:1.12s">QUANTUM MACHINE LEARNING</text>
  <text x="894" y="363" class="tiny reveal" style="--d:1.2s">VARIATIONAL QUANTUM CIRCUIT (VQC)</text>
  <text x="1340" y="382" class="tiny reveal fine" text-anchor="end" style="--d:1.3s">ANGLE ENCODING · TRAINABLE ANSATZ · LINEAR CX · ⟨Z⟩</text>
  <g fill="none" stroke="var(--muted)" stroke-width="1.3">
    <path d="M910 410H1335M910 478H1335M910 546H1335M910 614H1335" class="trace" style="--len:430;--d:1.45s"/>
  </g>
  <g class="reveal" style="--d:1.75s" fill="var(--inner)" stroke="var(--blue)">
    <rect x="940" y="391" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.0s"/><rect x="940" y="459" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.1s"/><rect x="940" y="527" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.2s"/><rect x="940" y="595" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.3s"/>
  </g>
  <g class="reveal" style="--d:1.8s" fill="var(--text)" font-size="10" text-anchor="middle"><text x="969" y="414">Rᵧ(xᵢ)</text><text x="969" y="482">Rᵧ(xᵢ)</text><text x="969" y="550">Rᵧ(xᵢ)</text><text x="969" y="618">Rᵧ(xᵢ)</text></g>
  <g class="reveal" style="--d:2.05s" fill="var(--inner)" stroke="var(--purple)">
    <rect x="1030" y="391" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.65s"/><rect x="1030" y="459" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.75s"/><rect x="1030" y="527" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.85s"/><rect x="1030" y="595" width="58" height="38" rx="7" class="gatePulse" style="--pulse:.95s"/>
    <rect x="1100" y="391" width="58" height="38" rx="7" class="gatePulse" style="--pulse:1.3s"/><rect x="1100" y="459" width="58" height="38" rx="7" class="gatePulse" style="--pulse:1.4s"/><rect x="1100" y="527" width="58" height="38" rx="7" class="gatePulse" style="--pulse:1.5s"/><rect x="1100" y="595" width="58" height="38" rx="7" class="gatePulse" style="--pulse:1.6s"/>
  </g>
  <g class="reveal" style="--d:2.12s" fill="var(--text)" font-size="9" text-anchor="middle"><text x="1059" y="414">Rᵧ(θᵢ)</text><text x="1059" y="482">Rᵧ(θᵢ)</text><text x="1059" y="550">Rᵧ(θᵢ)</text><text x="1059" y="618">Rᵧ(θᵢ)</text><text x="1129" y="414">R𝓏(φᵢ)</text><text x="1129" y="482">R𝓏(φᵢ)</text><text x="1129" y="550">R𝓏(φᵢ)</text><text x="1129" y="618">R𝓏(φᵢ)</text></g>
  <g class="reveal" style="--d:2.35s" stroke="var(--cyan)" fill="none" filter="url(#glow)"><path d="M1190 410V478"/><circle cx="1190" cy="478" r="10"/><path d="M1180 478H1200M1190 468V488"/><circle cx="1190" cy="410" r="5" fill="var(--cyan)"/><path d="M1210 478V546"/><circle cx="1210" cy="546" r="10"/><path d="M1200 546H1220M1210 536V556"/><circle cx="1210" cy="478" r="5" fill="var(--cyan)"/><path d="M1230 546V614"/><circle cx="1230" cy="614" r="10"/><path d="M1220 614H1240M1230 604V624"/><circle cx="1230" cy="546" r="5" fill="var(--cyan)"/></g>
  <g class="reveal" style="--d:2.6s" fill="var(--magenta)" font-size="12" text-anchor="middle"><text x="1300" y="414">⟨Z₀⟩</text><text x="1300" y="482">⟨Z₁⟩</text><text x="1300" y="550">⟨Z₂⟩</text><text x="1300" y="618">⟨Z₃⟩</text></g>
  <g class="reveal" style="--d:2.85s"><path d="M1315 649C1270 687 1100 687 1035 654" fill="none" stroke="var(--cyan)" marker-end="url(#arrow)" class="signal"/></g>
  <text x="894" y="687" class="code reveal" style="--d:3.0s">C(θ) → classical optimizer → update θ,φ</text>

  <!-- Fuzzy inference -->
  <text x="459" y="484" class="eyebrow reveal" style="--d:1.42s">FUZZY INFERENCE / CENTROID</text>
  <path d="M472 679H825M482 687V515" stroke="var(--line)" class="trace" style="--len:530;--d:1.7s"/>
  <g class="reveal" style="--d:1.95s"><path d="M482 672C516 672 526 535 574 535S632 672 664 672Z" fill="url(#lowFill)"/></g>
  <g class="reveal" style="--d:2.18s"><path d="M545 672C585 672 610 558 648 558S708 672 744 672Z" fill="url(#midFill)"/></g>
  <g class="reveal" style="--d:2.41s"><path d="M650 672C686 672 718 532 766 532S820 667 825 672Z" fill="url(#highFill)"/></g>
  <path d="M482 672C516 672 526 535 574 535S632 672 664 672M545 672C585 672 610 558 648 558S708 672 744 672M650 672C686 672 718 532 766 532S820 667 825 672" fill="none" stroke="url(#accent)" stroke-width="3" class="trace" style="--len:1200;--d:2.25s"/>
  <path d="M675 522V672" stroke="var(--text)" stroke-dasharray="5 7" class="trace" style="--len:160;--d:2.65s"/><g class="reveal" style="--d:3.1s"><circle cx="675" cy="672" r="5" fill="var(--text)"/></g>
  <text x="459" y="510" class="code reveal" style="--d:1.65s">RULE AGGREGATION → DEFUZZIFICATION</text>
  <g class="reveal fine" style="--d:2.8s"><text x="500" y="701" class="tiny" fill="var(--purple)">LOW</text><text x="622" y="701" class="tiny" fill="var(--cyan)">MID</text><text x="758" y="701" class="tiny" fill="var(--magenta)">HIGH</text><text x="675" y="536" class="tiny" text-anchor="middle">CENTROID y*</text></g>

  <!-- Publications and projects -->
  <text x="54" y="760" class="eyebrow reveal" style="--d:2.15s">TOP 3 PUBLICATIONS</text>
  {''.join(publication_rows)}
  <text x="459" y="760" class="eyebrow reveal" style="--d:2.4s">SELECTED BUILDS / RESEARCH → CODE</text>
  <text x="1340" y="760" class="tiny reveal fine" text-anchor="end" style="--d:2.5s">PYTHON · QISKIT · PYTORCH · NUMPY · VHDL · C++</text>
  {''.join(project_cards)}

  <!-- Compact stats footer -->
  <g class="reveal" style="--d:4.05s">
    <text x="54" y="1111" class="eyebrow">GITHUB SIGNAL</text>
    <text x="54" y="1156" class="heading">{e(stats.get('public_repos','—'))}</text><text x="54" y="1176" class="tiny">PUBLIC REPOS</text>
    <text x="220" y="1156" class="heading">{e(stats.get('followers','—'))}</text><text x="220" y="1176" class="tiny">FOLLOWERS</text>
    <text x="380" y="1156" class="heading">{e(stats.get('stars_received','—'))}</text><text x="380" y="1176" class="tiny">STARS RECEIVED</text>
    <text x="560" y="1156" class="heading">{e(stats.get('following','—'))}</text><text x="560" y="1176" class="tiny">FOLLOWING</text>
    <text x="1015" y="1122" class="tiny">REPOSITORY LANGUAGES</text>
    <rect x="1015" y="1137" width="300" height="13" rx="6" fill="var(--inner)"/>{''.join(language_bars)}
    <text x="1015" y="1173" class="tiny">{' · '.join(language_labels)}</text>
    <text x="1315" y="1122" class="tiny" text-anchor="end">REFRESHED {e(refreshed_label(stats.get('refreshed_at')))}</text>
  </g>
</svg>'''


def navigation_button(label: str, caption: str, accent: str) -> str:
    """Generate a small SVG used as a real clickable README navigation button."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="220" height="48" viewBox="0 0 220 48" role="img" aria-label="{e(label)}: {e(caption)}">
  <style>
    :root {{ --bg:#09162a; --text:#e8f4ff; --muted:#91a8bd; --line:#1a4267; --accent:{accent}; }}
    text {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace; }}
    .frame {{ fill:var(--bg); stroke:var(--line); stroke-width:1; }}
    .beam {{ stroke:var(--accent); stroke-width:2; stroke-dasharray:220; stroke-dashoffset:220; animation:draw 1.4s ease forwards; }}
    .arrow {{ animation:pulse 2.8s ease-in-out infinite; transform-origin:200px 24px; }}
    @keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
    @keyframes pulse {{ 0%,100% {{ opacity:.5; transform:translateX(0); }} 50% {{ opacity:1; transform:translateX(3px); }} }}
    @media (prefers-color-scheme:light) {{ :root {{ --bg:#ffffff; --text:#132238; --muted:#4c6078; --line:#9ebbd2; }} }}
    @media (prefers-reduced-motion:reduce) {{ .beam,.arrow {{ animation:none; stroke-dashoffset:0; }} }}
  </style>
  <rect x="1" y="1" width="218" height="46" rx="11" class="frame"/>
  <path d="M12 46H208" class="beam"/>
  <text x="16" y="21" fill="var(--text)" font-size="12" font-weight="750" letter-spacing="1">{e(label)}</text>
  <text x="16" y="36" fill="var(--muted)" font-size="9">{e(caption)}</text>
  <path d="M194 19L204 24L194 29" fill="none" stroke="var(--accent)" stroke-width="2" class="arrow"/>
</svg>'''


def write_svg(name: str, content: str) -> None:
    normalized = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    (OUT / name).write_text(normalized, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-github", action="store_true", help="refresh public GitHub metrics")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    profile = load("profile.json")
    research = load("research.json")
    projects = load("projects.json")
    publications = load("publications.json")
    github_path = DATA / "github.json"
    stats = refresh_github() if args.refresh_github or not github_path.exists() else load("github.json")

    hero_svg = hero(profile)
    quantum_svg = quantum_panel()
    research_svg = research_panel(research)
    projects_svg = projects_panel(projects)
    publications_svg = publications_panel(publications)
    stats_svg = stats_panel(stats)

    write_svg("hero.svg", hero_svg)
    write_svg("quantum-circuit.svg", quantum_svg)
    write_svg("research.svg", research_svg)
    write_svg("projects.svg", projects_svg)
    write_svg("publications.svg", publications_svg)
    write_svg("github-stats.svg", stats_svg)
    write_svg("profile.svg", dashboard_profile(profile, research, projects, publications, stats))
    write_svg("nav-projects.svg", navigation_button("PROJECTS", "research → code", "#29e6f2"))
    write_svg("nav-publications.svg", navigation_button("PUBLICATIONS", "papers · ORCID", "#a78bfa"))
    write_svg("nav-linkedin.svg", navigation_button("LINKEDIN", "professional profile", "#38bdf8"))
    write_svg("nav-contact.svg", navigation_button("CONTACT", "academic email", "#52e0a4"))
    print("Generated one responsive dashboard, four navigation buttons and six editable module SVGs.")


if __name__ == "__main__":
    main()
