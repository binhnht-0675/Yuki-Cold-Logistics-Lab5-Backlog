"""Pattern table of the content guard (content_guard.py re-exports every name here).

Every literal that a rule looks for is split, put in a character class or written as an escape,
so this file (and the plan-side leak scanner that reuses these rules) does not flag itself.
Rules other than `ctrl` run on the NFKC view of a line with the invisible characters removed.
"""
from __future__ import annotations

import re
from typing import List, Tuple

CATEGORY_JA = {
    "vi": "1 ベトナム語の文字", "ctrl": "2 制御文字", "path": "3 内部パス", "secret": "4 秘密情報のパターン",
    "email": "5 メールアドレス", "term": "6 公開しない固有の用語", "internal": "7 社内・要ログインの URL / 社名",
}
MASKED = {"secret", "email", "internal"}

VI_RX = re.compile(  # Vietnamese letters with diacritics, precomposed (NFC) and combining (NFD, incl. breve)
    "[\u00c0-\u00c3\u00c8-\u00ca\u00cc\u00cd\u00d2-\u00d5\u00d9\u00da\u00dd"
    "\u00e0-\u00e3\u00e8-\u00ea\u00ec\u00ed\u00f2-\u00f5\u00f9\u00fa\u00fd"
    "\u0102\u0103\u0110\u0111\u0128\u0129\u0168\u0169\u01a0\u01a1\u01af\u01b0\u1ea0-\u1ef9"
    "\u0300-\u0303\u0306\u0309\u031b\u0323]")
# C0 / C1 controls except \t \n, every format character (Unicode category Cf: soft hyphen, zero-width,
# bidi, invisible operators, tags ...), combining grapheme joiner, variation selectors, Hangul fillers,
# line / paragraph separators. A test checks that every Cf code point of the running Python is covered.
CTRL_RX = re.compile(
    "[\x00-\x08\x0b-\x1f\x7f-\x9f\u00ad\u034f\u0600-\u0605\u061c\u06dd\u070f\u0890\u0891\u08e2"
    "\u115f\u1160\u180e\u200b-\u200f\u2028-\u202e\u2060-\u2064\u2066-\u206f\u3164"
    "\ufe00-\ufe0f\ufeff\uffa0\ufff9-\ufffb\U000110bd\U000110cd\U00013430-\U0001343f"
    "\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0001\U000e0020-\U000e007f\U000e0100-\U000e01ef]")
# Same pattern strings as the plan-side leak scanner (tools/leak_patterns.py re-exports them).
# EMAIL_OK_RX is anchored at the start ("mynoreply@..." is NOT a noreply address).
EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}")
EMAIL_OK_RX = re.compile(r"^(noreply|no-reply)@|@(example\.(com|org|net|invalid)|users\.noreply\.github\.com)$", re.I)
CO1, CO2 = "fram" + "gia", "sun-" + "asterisk"
COMPANY_RX = re.compile(
    re.escape(CO1) + r"|su[n][\s_*-]*asterisk|(?<![a-z])su[n]\s?\*|\u30b5\u30f3[\u30fb\s]?\u30a2\u30b9\u30bf\u30ea\u30b9\u30af",
    re.I)
INTERNAL_LINK_RX = re.compile(r"https?://(docs|drive|sheets|slides)\.google\.com/\S*", re.I)
KEY_RXS = [
    re.compile("sb" + r"_secret_[A-Za-z0-9_-]{8,}"),
    re.compile("ey" + r"J[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"),
    re.compile("gh" + r"[pousr]_[A-Za-z0-9]{20,}"),
    re.compile("github" + r"_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])s" + r"k-[A-Za-z0-9_-]{20,}"),
    re.compile("-----BEGIN" + r" [A-Z ]*PRIVATE KEY-----"),
    re.compile("AK" + r"IA[0-9A-Z]{16}"),
    re.compile("xo" + r"x[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile("AI" + r"za[0-9A-Za-z_-]{35}"),
    re.compile(r"(?<![A-Za-z0-9])sb" + r"p_[A-Za-z0-9]{20,}"),  # Supabase personal access token
]
NO_SCHEME = r"(?<![\w./-])"  # a bare host (the https:// form is matched by the rule before it)

RULES: List[Tuple[str, str, re.Pattern]] = [
    ("vi", "vi-letter", VI_RX),
    ("ctrl", "control-char", CTRL_RX),
    ("path", "plans-dir", re.compile(r"(?<![\w.-])plan[s]/")),
    ("path", "prototype-dir", re.compile(r"(?<![\w.-])prototyp[e]/")),
    ("path", "users-home", re.compile(r"/User[s]/")),
    ("path", "home-dir", re.compile(r"(?<![\w.])/hom[e]/[\w.-]+/")),
    ("path", "tilde-home", re.compile(r"(?<![\w~])~/[\w.-]")),
    ("path", "windows-home", re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]+User[s][\\/]", re.I)),
    ("path", "private-tmp", re.compile(r"/privat[e]/(tmp|var)/")),
    ("path", "submission-dir", re.compile("nop" + r"[-_ ]?bai", re.I)),
    ("path", "brief-dir", re.compile("de" + r"[-_]bai", re.I)),
    ("path", "env-file", re.compile(r"(?<![\w.])\.en[v](?!\w)(?!\.(example|sample|template)\b)")),
    *[("secret", f"key-pattern-{n}", rx) for n, rx in enumerate(KEY_RXS, 1)],
    ("secret", "jwt-header", re.compile("ey" + r"JhbGciOi")),
    ("secret", "url-credentials", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@'\"<>]+:[^\s/@'\"<>]+@", re.I)),
    ("secret", "password-value", re.compile(r"(?<![A-Za-z])(passwor[d]|passw[d])\s*[:=]", re.I)),
    ("email", "email", EMAIL_RX),
    ("term", "internal-term-1", re.compile(r"(?<![A-Za-z])LAB[-_ ]?\d", re.I)),
    ("term", "internal-term-2", re.compile("\u63a1\u70b9")),
    ("term", "internal-term-3", re.compile("\u8b1b\u5e2b")),
    ("term", "internal-term-4", re.compile("\u8ab2\u984c")),
    ("term", "internal-term-5", re.compile("\u8b1b\u5ea7")),
    ("internal", "google-docs", INTERNAL_LINK_RX),
    ("internal", "google-docs", re.compile(r"https?://(forms|sites)\.google\.com/\S*", re.I)),
    ("internal", "google-docs", re.compile(NO_SCHEME + r"(docs|drive|sheets|slides|forms|sites)\.google\.com/", re.I)),
    ("internal", "company-name", COMPANY_RX),
    ("internal", "login-saas", re.compile(
        r"(?:https?://|" + NO_SCHEME + r")(?:[\w-]+\.)*(atlassian\.net|slack\.com|notion\.so|notion\.site|"
        r"sharepoint\.com|box\.com)\b\S*", re.I)),
    ("internal", "gist", re.compile(r"(?:https?://|" + NO_SCHEME + r")gist\.github(usercontent)?\.com/", re.I)),
]
# A URL that names a GitHub repository (or a user / org Project: owner in group 2 after users|orgs):
# github.com[:port]/<o>/<r>, raw.githubusercontent.com/<o>/<r>, api.github.com/repos/<o>/<r>,
# with or without https:// and user info.
GITHUB_URL_RX = re.compile(
    r"(?:https?://(?:[^\s/@]+@)?|(?<![\w./-]))(?:www\.)?"
    r"(?:github\.com(?::\d+)?|raw\.githubusercontent\.com|api\.github\.com(?::\d+)?/repos)"
    r"/([\w.-]+)/([\w-]+(?:\.(?!git\b)[\w-]+)*)(?:\.git)?", re.I)
PROJECT_OWNER_SEGMENTS = {"users", "orgs"}
TRAVERSAL_RX = re.compile(r"(?:^|/)\.\.(?:/|$|[?#])")
DECODE_LAYERS = 16  # percent-decoding beyond this many layers is itself a finding (deep-percent-encoding)
