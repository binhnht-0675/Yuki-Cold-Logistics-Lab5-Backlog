"""Search / filters / numeric sort and the SWP-hours view: progressive enhancement only.

Every row, total and table is in the static HTML. The controls and the hours view carry `hidden` and
only the script below shows them, so a reader without JavaScript sees no dead controls. The script is
one fixed constant (the checker accepts exactly this text and nothing else): no network, no eval, no
innerHTML, no inline handlers, text written with textContent only, nothing persisted (no storage).
"""
from __future__ import annotations

from typing import List

from ja_report_html_parts import e
from ja_report_text import label

FILTERS = (("f-discipline", "分野", "discipline", "primaryDiscipline"), ("f-work-type", "作業種別", "workType", "workType"),
           ("f-confidence", "確信度", "confidence", "confidence"), ("f-calibration", "校正", "issueCalibration", None))

ISSUE_HEAD = ('<th><button type="button" class="sort" data-sort="final-swp" title="SWP で並べ替え">SWP</button></th>'
              + "".join(f"<th>{h}</th>" for h in ("issue", "タイトル", "分野", "作業種別", "確信度")))

SCRIPT = r"""(function () {
  'use strict';
  var doc = document;
  var byId = function (id) { return doc.getElementById(id); };
  var list = function (nodes) { return Array.prototype.slice.call(nodes); };
  var controls = byId('controls');
  if (controls) {
    controls.hidden = false;
    var rows = list(doc.querySelectorAll('tr[data-search]'));
    var search = byId('f-search');
    var filters = [['f-discipline', 'discipline'], ['f-work-type', 'workType'],
                   ['f-confidence', 'confidence'], ['f-calibration', 'calibration']];
    var count = byId('f-count');
    var apply = function () {
      var query = search.value.trim().toLowerCase();
      var active = query !== '';
      var shown = 0;
      rows.forEach(function (row) {
        var hide = query !== '' && row.dataset.search.indexOf(query) < 0;
        filters.forEach(function (pair) {
          var wanted = byId(pair[0]).value;
          if (wanted !== '') { active = true; if (row.dataset[pair[1]] !== wanted) { hide = true; } }
        });
        row.hidden = hide;
        if (!hide) { shown += 1; }
      });
      count.textContent = '表示 ' + shown + ' / ' + rows.length + ' 件';
      list(doc.querySelectorAll('details.group')).forEach(function (group) {
        if (active) { group.open = group.querySelector('tr[data-search]:not([hidden])') !== null; }
      });
    };
    search.addEventListener('input', apply);
    filters.forEach(function (pair) { byId(pair[0]).addEventListener('change', apply); });
  }
  list(doc.querySelectorAll('button[data-sort]')).forEach(function (button) {
    button.addEventListener('click', function () {
      var body = button.closest('table').tBodies[0];
      var ascending = button.dataset.dir !== 'asc';
      button.dataset.dir = ascending ? 'asc' : 'desc';
      button.closest('th').setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
      list(body.rows).sort(function (a, b) {
        return (Number(a.dataset.finalSwp) - Number(b.dataset.finalSwp)) * (ascending ? 1 : -1);
      }).forEach(function (row) { body.appendChild(row); });
    });
  });
  var view = byId('hours-view');
  var rate = byId('rate');
  if (view && rate) {
    view.hidden = false;
    var outputs = list(view.querySelectorAll('output[data-from]'));
    var update = function () {
      var perSwp = parseFloat(rate.value);
      outputs.forEach(function (out) {
        var origin = doc.querySelector('[data-v="' + out.dataset.from + '"]');
        var swp = origin ? parseFloat(origin.textContent) : NaN;
        out.textContent = (isFinite(swp) && perSwp > 0) ? (Math.round(swp * perSwp * 10) / 10) + ' 時間' : '—';
      });
    };
    rate.addEventListener('input', update);
    update();
  }
}());"""


def row_attrs(issue: dict, shown_ref: str, shown_title: str) -> str:
    """Filter / sort attributes of an issue row (only text that is also shown in the row)."""
    search = f"{shown_ref} {shown_title}".lower()
    cal = (issue.get("calibration") or {}).get("status")
    return (f' data-search="{e(search)}" data-discipline="{e(issue.get("primaryDiscipline"))}"'
            f' data-work-type="{e(issue.get("workType"))}" data-confidence="{e(issue.get("confidence"))}"'
            f' data-calibration="{e(cal)}" data-final-swp="{e(issue.get("finalSWP"))}"')


def controls_html(issues: List[dict], L: dict) -> str:
    def options(group, field, values=None):
        found = values or sorted({str(i.get(field)) for i in issues if i.get(field) is not None})
        return '<option value="">すべて</option>' + "".join(
            f'<option value="{e(val)}">{e(label(L, group, val))}</option>' for val in found)
    cal = sorted({str(c) for c in ((i.get("calibration") or {}).get("status") for i in issues) if c})
    selects = []
    for sid, name, group, field in FILTERS:
        values = cal if field is None else (["high", "medium", "low"] if field == "confidence" else None)
        selects.append(f'<label>{name} <select id="{sid}">{options(group, field, values)}</select></label>')
    return ('<div class="controls" id="controls" hidden><label>検索 <input type="search" id="f-search" '
            'placeholder="#番号 またはタイトル" autocomplete="off"></label>' + "".join(selects)
            + '<span id="f-count" aria-live="polite"></span></div>')


CSS = """.tablewrap{overflow-x:auto}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
gap:10px;margin:12px 0}.tile{border:1px solid #d0d7de;border-radius:8px;padding:8px 12px}.tile b{display:block;
font-size:1.3rem}.compbar{display:flex;gap:2px;margin:8px 0}.compbar span{padding:2px 8px;color:#fff;
white-space:nowrap;overflow:hidden}.seg-plan{background:#0c6e8c}.seg-bug{background:#9a4a07}
.bar{display:inline-block;height:.8em;background:#0c6e8c;border-radius:2px}.flag{font-size:.8rem;
border-radius:4px;padding:0 4px;margin-left:4px;background:#fff4db;color:#7a4d00}.spread{font-size:.85rem;
color:#57606a;white-space:nowrap}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
button.sort{font:inherit;border:0;background:none;cursor:pointer;padding:0;text-decoration:underline}
:focus-visible{outline:2px solid #0969da;outline-offset:2px}@media (prefers-reduced-motion:reduce){*{
transition:none!important;animation:none!important}}@media print{.controls,#hours{display:none}}
@media (max-width:640px){body{padding:8px}.compbar span{font-size:.75rem}}"""
