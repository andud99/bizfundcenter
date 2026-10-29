#!/usr/bin/env python3
"""기업자금센터 칼럼 블로그 빌드 스크립트.

posts/*.md 를 읽어 정적 HTML 사이트를 만든다.
사용법: python3 build.py   (필요 패키지: pip install markdown)
"""
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"].rstrip("/")
FULL = SITE["url"].rstrip("/") + BASE
KST = timezone(timedelta(hours=9))

CATEGORIES = {
    "현장 사례": "cases",
    "정책자금": "policy",
    "기술개발자금": "rnd",
    "창업지원금": "startup",
    "세금·구조": "tax",
    "공고 체크": "notice",
}
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
GENERATED_DIRS = ["p", "c"]


def esc(s):
    return html.escape(str(s), quote=True)


def parse_post(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: 맨 위에 --- 로 감싼 머리말이 없습니다")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    for key in ("title", "date", "category", "description"):
        if not meta.get(key):
            raise SystemExit(f"{path.name}: 머리말에 {key} 가 없습니다")
    if meta["category"] not in CATEGORIES:
        raise SystemExit(f"{path.name}: category 는 {list(CATEGORIES)} 중 하나여야 합니다")
    fm = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", path.name)
    if not fm:
        raise SystemExit(f"{path.name}: 파일명은 YYYY-MM-DD-slug.md 형식이어야 합니다")
    date = datetime.strptime(meta["date"], "%Y-%m-%d").replace(hour=7, tzinfo=KST)
    body_md = m.group(2).strip()
    body_html = markdown.markdown(body_md, extensions=["extra", "sane_lists"])
    chars = len(re.sub(r"\s", "", re.sub(r"<[^>]+>", "", body_html)))
    return {
        "title": meta["title"],
        "date": date,
        "category": meta["category"],
        "description": meta["description"],
        "slug": fm.group(2),
        "url": f"{BASE}/p/{fm.group(2)}/",
        "body": body_html,
        "minutes": max(1, round(chars / 500)),
    }


def fmt_date(d):
    return f"{d.year}. {d.month}. {d.day}. ({WEEKDAYS[d.weekday()]})"


HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{ogtype}">
<meta property="og:site_name" content="{site}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<link rel="alternate" type="application/rss+xml" title="{site}" href="{full}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="{base}/assets/style.css">
</head>
<body>
<header class="masthead">
  <div class="wrap masthead-row">
    <a class="brand" href="{base}/">기업자금센터 <span>자금정보</span></a>
    <nav class="nav">
      <a href="{base}/">전체 글</a>
      <a href="{base}/limit/">한도 계산</a>
      <a href="{home}" rel="noopener">기업자금센터 홈</a>
      <a class="nav-cta" href="{base}/apply/">상담 신청</a>
    </nav>
  </div>
</header>
<main>
"""

FOOT = """</main>
<footer class="foot">
  <div class="wrap foot-row">
    <div>
      <p class="foot-brand">기업자금센터</p>
      <p>{address}</p>
      <p>2013년부터 정책자금·운전자금·시설자금 컨설팅</p>
    </div>
    <div class="foot-links">
      <a href="{home}" rel="noopener">홈페이지</a>
      <a href="{base}/apply/">상담 신청</a>
      <a href="{base}/feed.xml">RSS</a>
    </div>
  </div>
  <div class="wrap"><p class="foot-note">칼럼은 일반적인 정보 제공을 위한 글입니다. 실제 자금 신청 요건과 한도는 기관 공고와 회사 상황에 따라 달라집니다.</p></div>
</footer>
</body>
</html>
"""


def page(title, desc, canonical, content, ogtype="website"):
    ctx = dict(
        title=esc(title), desc=esc(desc), canonical=esc(canonical), ogtype=ogtype,
        site=esc(SITE["title"]), full=FULL, base=BASE, home=esc(SITE["homepage"]),
        address=esc(SITE["address"]),
    )
    return HEAD.format(**ctx) + content + FOOT.format(**ctx)


def chip(cat):
    return f'<a class="chip chip-{CATEGORIES[cat]}" href="{BASE}/c/{CATEGORIES[cat]}/">{esc(cat)}</a>'


def row(p):
    return f"""<li class="row">
  <time datetime="{p['date']:%Y-%m-%d}">{p['date'].month}.{p['date'].day}<small>{WEEKDAYS[p['date'].weekday()]}</small></time>
  <div>
    {chip(p['category'])}
    <h3><a href="{p['url']}">{esc(p['title'])}</a></h3>
    <p>{esc(p['description'])}</p>
  </div>
</li>"""


CTA = """<aside class="cta">
  <p class="cta-q">우리 회사는 어떤 자금이 맞을까요?</p>
  <p>업력, 매출, 부채 상황을 보고 받을 수 있는 자금과 순서를 정리해 드립니다. 상담은 무료입니다.</p>
  <a class="btn" href="{base}/apply/">무료 상담 신청하기</a>
</aside>
"""


def topic_strip():
    plan = [("사례", "현장 사례", "사례"), ("정책", "정책자금", "정책"), ("R&D", "기술개발자금", "R&D"), ("창업", "창업지원금", "창업"), ("세무", "세금·구조", "세무"), ("공고", "공고 체크", "공고")]
    cells = "".join(
        f'<li><b>{esc(d)}</b><a href="{BASE}/c/{CATEGORIES[c]}/" aria-label="{esc(c)}"><span class="long">{esc(c)}</span><span class="short" aria-hidden="true">{esc(s)}</span></a></li>'
        for d, c, s in plan
    )
    return f'<ol class="strip" aria-label="칼럼 주제">{cells}</ol>'


def build_list_page(posts, heading, lead, canonical, out):
    if posts:
        first, rest = posts[0], posts[1:]
        feature = f"""<article class="feature">
  <div class="feature-meta">{chip(first['category'])}<time datetime="{first['date']:%Y-%m-%d}">{fmt_date(first['date'])}</time></div>
  <h2><a href="{first['url']}">{esc(first['title'])}</a></h2>
  <p>{esc(first['description'])}</p>
  <a class="more" href="{first['url']}">읽기 · {first['minutes']}분</a>
</article>"""
        items = "\n".join(row(p) for p in rest)
        listing = f'<ul class="ledger">{items}</ul>' if rest else ""
    else:
        feature = '<p class="empty">아직 이 주제의 글이 없습니다. 다른 주제의 칼럼을 먼저 읽어보세요.</p>'
        listing = ""
    content = f"""<section class="hero">
  <div class="wrap">
    <h1>{esc(heading)}</h1>
    <p class="lead">{esc(lead)}</p>
    {topic_strip()}
  </div>
</section>
<section class="wrap list">
{feature}
{listing}
</section>
<div class="wrap">{CTA.format(base=BASE)}</div>
"""
    write(out, page(heading if heading != SITE["title"] else SITE["title"], lead, canonical, content))


def build_post(p, posts):
    same = [q for q in posts if q["category"] == p["category"] and q["slug"] != p["slug"]][:3]
    related = ""
    if same:
        related = '<section class="related"><h2>같은 주제의 글</h2><ul class="ledger">' + "".join(row(q) for q in same) + "</ul></section>"
    content = f"""<article class="post wrap">
  <header class="post-head">
    <div class="feature-meta">{chip(p['category'])}<time datetime="{p['date']:%Y-%m-%d}">{fmt_date(p['date'])}</time><span>{p['minutes']}분 읽기</span></div>
    <h1>{esc(p['title'])}</h1>
    <p class="lead">{esc(p['description'])}</p>
  </header>
  <div class="prose">
{p['body']}
  </div>
  {CTA.format(base=BASE)}
  {related}
</article>
"""
    write(f"p/{p['slug']}/index.html", page(f"{p['title']} | {SITE['title']}", p["description"], FULL + f"/p/{p['slug']}/", content, "article"))


def build_apply():
    content = f"""<section class="wrap apply">
  <h1>무료 상담 신청</h1>
  <p class="lead">아래 내용을 남겨주시면 담당자가 확인 후 연락드립니다. 회사 상황에 맞는 자금 종류와 신청 순서를 함께 정리해 드립니다.</p>
  <form id="fundForm" action="{esc(SITE['formspree'])}" method="POST">
    <label>성함<input type="text" name="name" autocomplete="name" required></label>
    <label>회사명<input type="text" name="company" autocomplete="organization" required></label>
    <label>연락처<input type="tel" name="phone" autocomplete="tel" required></label>
    <label>이메일<input type="email" name="email" autocomplete="email" required></label>
    <label>관심 있는 자금
      <select name="type">
        <option>운전자금</option>
        <option>시설자금</option>
        <option>창업자금</option>
        <option>기술개발(R&amp;D)자금</option>
        <option>잘 모르겠어요</option>
      </select>
    </label>
    <label>필요 금액 (백만원)<input type="number" name="amount" min="0" inputmode="numeric"></label>
    <label>사업 개요<textarea name="desc" rows="5" placeholder="업종, 업력, 최근 매출, 자금이 필요한 이유를 적어주시면 더 정확히 안내드릴 수 있습니다."></textarea></label>
    <input type="hidden" name="_source" value="칼럼 블로그">
    <button class="btn" type="submit">상담 신청하기</button>
    <p class="form-note" id="formNote" role="status"></p>
  </form>
  <div id="thanks" class="thanks" hidden>
    <h2>상담 신청이 접수되었습니다</h2>
    <p>담당자가 확인 후 영업일 기준 1~2일 안에 연락드립니다.</p>
    <a class="more" href="{BASE}/">칼럼 계속 읽기</a>
  </div>
</section>
<script>
(function () {{
  var form = document.getElementById('fundForm');
  var note = document.getElementById('formNote');
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var btn = form.querySelector('button');
    btn.disabled = true; note.textContent = '보내는 중입니다...';
    fetch(form.action, {{ method: 'POST', body: new FormData(form), headers: {{ 'Accept': 'application/json' }} }})
      .then(function (r) {{
        if (!r.ok) throw new Error();
        form.hidden = true; document.getElementById('thanks').hidden = false;
      }})
      .catch(function () {{
        btn.disabled = false;
        note.textContent = '신청이 전송되지 않았습니다. 잠시 후 다시 눌러주시거나 전화로 문의해 주세요.';
      }});
  }});
}})();
</script>
"""
    write("apply/index.html", page(f"무료 상담 신청 | {SITE['title']}", "회사 상황에 맞는 정책자금과 신청 순서를 무료로 상담해 드립니다.", FULL + "/apply/", content))


def build_limit():
    content = f"""<section class="wrap apply limit">
  <h1>예상 자금 한도 계산</h1>
  <p class="lead">회사 정보 몇 가지만 넣으면 지금 받을 수 있는 운영자금의 대략적인 범위를 보여드립니다. 입력한 내용은 저장되지 않습니다.</p>
  <form id="calcForm" novalidate>
    <fieldset class="lim-grid">
      <label>업종
        <select id="ind" required>
          <option value="mfg">제조</option>
          <option value="tech">IT·소프트웨어·지식서비스</option>
          <option value="whole">도소매·유통</option>
          <option value="cons">건설·공사</option>
          <option value="svc">음식·숙박·기타 서비스</option>
        </select>
      </label>
      <label>업력
        <select id="age" required>
          <option value="1">3년 미만 (결산 3년치 없음)</option>
          <option value="2" selected>3년 이상 7년 미만</option>
          <option value="3">7년 이상</option>
        </select>
      </label>
      <label>최근 1년 매출 (억 원)<input id="rev" type="number" min="0" step="0.1" inputmode="decimal" placeholder="예: 25" required></label>
      <label>최근 결산 영업이익
        <select id="profit">
          <option value="plus">흑자</option>
          <option value="minus">적자</option>
        </select>
      </label>
      <label>지금 쓰고 있는 정책자금·기관 자금 (억 원)<input id="debt" type="number" min="0" step="0.1" inputmode="decimal" placeholder="없으면 0" value="0"></label>
      <label>대표님 개인 신용점수
        <select id="score">
          <option value="a">840점 이상</option>
          <option value="b" selected>740~839점</option>
          <option value="c">640~739점</option>
          <option value="d">640점 미만</option>
          <option value="b">잘 모르겠음</option>
        </select>
      </label>
    </fieldset>
    <fieldset class="lim-checks">
      <legend>보유 인증 (해당하는 것 모두)</legend>
      <label><input type="checkbox" name="cert">벤처기업</label>
      <label><input type="checkbox" name="cert">이노비즈·메인비즈</label>
      <label><input type="checkbox" name="cert">기업부설연구소·전담부서</label>
      <label><input type="checkbox" name="cert">특허</label>
    </fieldset>
    <fieldset class="lim-checks">
      <legend>해당 사항</legend>
      <label><input type="checkbox" id="tax">밀린 세금(부가세·4대보험 등)이 있음</label>
      <label><input type="checkbox" id="land">회사나 대표님 명의 부동산이 있음</label>
    </fieldset>
    <button class="btn" type="submit">예상 한도 보기</button>
    <p class="form-note" id="calcNote" role="status"></p>
  </form>

  <div id="result" class="lim-result" hidden>
    <p class="lim-eyebrow">예상 운영자금 한도</p>
    <p class="lim-range" id="range"></p>
    <ul class="lim-notes" id="notes"></ul>
    <p class="lim-disc">입력하신 정보로 계산한 참고용 범위입니다. 실제 금액은 재무제표, 기존 거래, 신청 시기와 기관 판단에 따라 달라집니다.</p>
  </div>

  <div id="detail" class="lim-detail" hidden>
    <h2>우리 회사는 어디서, 어떤 순서로?</h2>
    <p>같은 한도라도 어느 기관에 먼저 들어가느냐, 결산 전후 언제 신청하느냐에 따라 결과가 크게 달라집니다. 연락처를 남겨 주시면 담당자가 우리 회사에 맞는 순서를 정리해 연락드립니다.</p>
    <form id="leadForm" action="{esc(SITE['formspree'])}" method="POST">
      <label>성함<input type="text" name="name" autocomplete="name" required></label>
      <label>회사명<input type="text" name="company" autocomplete="organization" required></label>
      <label>연락처<input type="tel" name="phone" autocomplete="tel" required></label>
      <input type="hidden" name="calc" id="calcSummary">
      <input type="hidden" name="_source" value="예상 한도 계산">
      <button class="btn" type="submit">맞춤 순서 안내받기</button>
      <p class="form-note" id="leadNote" role="status"></p>
    </form>
    <div id="thanks" class="thanks" hidden>
      <h2>접수되었습니다</h2>
      <p>담당자가 확인 후 영업일 기준 1~2일 안에 연락드립니다.</p>
      <a class="more" href="{BASE}/c/cases/">현장 사례 읽기</a>
    </div>
  </div>
</section>
<script>
(function () {{
  /* ── 산식 설정: 숫자만 고치면 계산이 바뀝니다 ───────────────── */
  var RULES = {{
    revenueRate: {{ mfg: 1/4, tech: 0.30, whole: 1/6, cons: 0.20, svc: 0.20 }}, // 매출 대비 기본 비율 (제조 1/4, 도소매 1/6)
    ageCap:      {{ 1: 3, 2: 10, 3: 30 }},       // 업력별 최대치 (억) — 재무제표 3개년이 없으면(3년 미만) 3억까지
    startupFloor: 1,                            // 업력 7년 미만, 신용 양호 시 최소 기대치 (억)
    scoreRate:   {{ a: 1.0, b: 0.85, c: 0.6, d: 0.3 }}, // 대표 신용점수 반영
    lossRate:    0.7,                           // 적자일 때 반영
    certBonus:   0.1, certBonusMax: 0.3,        // 인증 1개당 가산, 최대
    debtWeight:  1.0,                           // 기존 자금 차감 비율
    rangeLow:    0.7                            // 범위 하단 = 상단 x 이 값
  }};
  /* ─────────────────────────────────────────────────────────── */

  function $(id) {{ return document.getElementById(id); }}
  function eok(v) {{
    if (v < 1) return Math.round(v * 10) * 1000 + '만 원';
    return (Math.round(v * 10) / 10).toString().replace(/\\.0$/, '') + '억 원';
  }}

  var calc = $('calcForm');
  calc.addEventListener('submit', function (e) {{
    e.preventDefault();
    var rev = parseFloat($('rev').value);
    if (!(rev >= 0)) {{ $('calcNote').textContent = '최근 1년 매출을 숫자로 넣어 주세요.'; $('rev').focus(); return; }}
    $('calcNote').textContent = '';
    var ind = $('ind').value, age = $('age').value, score = $('score').value;
    var debt = Math.max(0, parseFloat($('debt').value) || 0);
    var certs = calc.querySelectorAll('input[name=cert]:checked').length;
    var loss = $('profit').value === 'minus';

    var base = rev * RULES.revenueRate[ind];
    if (age !== '3' && (score === 'a' || score === 'b')) base = Math.max(base, RULES.startupFloor);
    base = Math.min(base, RULES.ageCap[age]);
    base *= RULES.scoreRate[score];
    if (loss) base *= RULES.lossRate;
    base *= 1 + Math.min(certs * RULES.certBonus, RULES.certBonusMax);
    var high = Math.max(0, base - debt * RULES.debtWeight);
    var low = high * RULES.rangeLow;

    var notes = [];
    if ($('tax').checked) notes.push('밀린 세금이 있으면 대부분의 심사가 그 단계에서 멈춥니다. 세금 정리가 먼저입니다.');
    if (high < 0.3) notes.push('계산상 추가 여력은 작게 나옵니다. 하지만 담보, 인증, 신청 경로에 따라 길이 열리는 경우가 많습니다.');
    if (score === 'c' || score === 'd') notes.push('대표님 신용점수가 한도를 누르고 있습니다. 점수를 올리면 같은 회사라도 범위가 달라집니다.');
    if (loss) notes.push('적자 결산은 한도를 줄입니다. 흑자로 돌아선 결산이 나온 뒤가 유리할 수 있습니다.');
    if ($('land').checked) notes.push('부동산이 있다면 위 범위와 별도로 담보를 활용한 자금도 가능합니다.');
    if (certs === 0 && (ind === 'mfg' || ind === 'tech')) notes.push('제조·기술 업종은 인증을 갖추면 범위가 넓어지는 경우가 많습니다.');

    $('range').textContent = high < 0.3 ? '추가 여력 확인 필요' : eok(low) + ' ~ ' + eok(high);
    var ul = $('notes'); ul.innerHTML = '';
    notes.forEach(function (t) {{ var li = document.createElement('li'); li.textContent = t; ul.appendChild(li); }});
    ul.hidden = notes.length === 0;

    $('calcSummary').value = [
      '업종 ' + $('ind').selectedOptions[0].text, '업력 ' + $('age').selectedOptions[0].text,
      '매출 ' + rev + '억', loss ? '적자' : '흑자', '기존 ' + debt + '억',
      '신용 ' + $('score').selectedOptions[0].text, '인증 ' + certs + '개',
      $('tax').checked ? '체납 있음' : '', $('land').checked ? '부동산 있음' : '',
      '예상 ' + $('range').textContent
    ].filter(Boolean).join(' / ');

    $('result').hidden = false; $('detail').hidden = false;
    $('result').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});

  var lead = $('leadForm');
  lead.addEventListener('submit', function (e) {{
    e.preventDefault();
    var btn = lead.querySelector('button');
    btn.disabled = true; $('leadNote').textContent = '보내는 중입니다...';
    fetch(lead.action, {{ method: 'POST', body: new FormData(lead), headers: {{ 'Accept': 'application/json' }} }})
      .then(function (r) {{ if (!r.ok) throw new Error(); lead.hidden = true; $('thanks').hidden = false; }})
      .catch(function () {{ btn.disabled = false; $('leadNote').textContent = '전송되지 않았습니다. 잠시 후 다시 눌러 주세요.'; }});
  }});
}})();
</script>
"""
    write("limit/index.html", page(f"예상 자금 한도 계산 | {SITE['title']}", "업종, 업력, 매출, 신용점수를 넣으면 지금 받을 수 있는 운영자금의 대략적인 범위를 보여드립니다.", FULL + "/limit/", content))


def build_widget(posts):
    items = "".join(
        f'<li><a href="{FULL}/p/{p["slug"]}/" target="_top"><span>{esc(p["category"])}</span>{esc(p["title"])}</a><time>{p["date"]:%Y.%m.%d}</time></li>'
        for p in posts[:4]
    )
    w = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>최신 자금정보</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;overflow-x:hidden}}
body{{font-family:Pretendard,system-ui,sans-serif;background:transparent;color:#1f2430;word-break:keep-all;padding:0 20px}}
.w{{border-top:3px solid #f39200;padding:14px 0 4px;max-width:100%}}
.w-head{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:0 0 6px}}
.w-head b{{font-size:17px}} .w-head a{{font-size:14px;color:#b85e00;text-decoration:none;white-space:nowrap}}
ul{{list-style:none;margin:0;padding:0}}
li{{display:flex;justify-content:space-between;gap:12px;padding:11px 0;border-bottom:1px solid #e3e3de;font-size:15px}}
li a{{color:#1f2430;text-decoration:none;line-height:1.45;min-width:0}} li a:hover{{color:#b85e00}}
li span{{color:#d97f00;font-weight:600;margin-right:8px;font-size:13px}}
time{{color:#5d6270;font-size:13px;white-space:nowrap;padding-top:2px;flex:none}}
@media (max-width:520px){{
  body{{padding:0 16px}}
  li{{flex-direction:column;gap:4px}}
  li span{{display:block;margin:0 0 2px}}
  time{{padding-top:0;font-size:12px}}
  li:nth-child(n+3){{display:none}}
}}
</style></head>
<body><div class="w"><div class="w-head"><b>최신 자금정보</b><a href="{FULL}/" target="_top">전체 보기</a></div><ul>{items}</ul></div></body></html>
"""
    write("widget.html", w)


def build_feed(posts):
    now = datetime.now(KST).strftime("%a, %d %b %Y %H:%M:%S +0900")
    items = "".join(
        f"""<item><title>{esc(p['title'])}</title><link>{FULL}/p/{p['slug']}/</link><guid>{FULL}/p/{p['slug']}/</guid>
<pubDate>{p['date'].strftime('%a, %d %b %Y %H:%M:%S +0900')}</pubDate><category>{esc(p['category'])}</category>
<description>{esc(p['description'])}</description></item>"""
        for p in posts[:30]
    )
    write("feed.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(SITE['title'])}</title><link>{FULL}/</link>
<description>{esc(SITE['description'])}</description><language>ko</language><lastBuildDate>{now}</lastBuildDate>
{items}</channel></rss>
""")
    urls = [f"{FULL}/", f"{FULL}/apply/", f"{FULL}/limit/"] + [f"{FULL}/p/{p['slug']}/" for p in posts]
    urls += [f"{FULL}/c/{v}/" for v in CATEGORIES.values()]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {FULL}/sitemap.xml\n")


def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    for d in GENERATED_DIRS:
        shutil.rmtree(ROOT / d, ignore_errors=True)
    today = datetime.now(KST).date()
    posts = [parse_post(p) for p in sorted((ROOT / "posts").glob("*.md"))]
    # 날짜가 미래인 글은 그날이 오기 전까지 공개하지 않는다
    posts = [p for p in posts if p["date"].date() <= today]
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    slugs = [p["slug"] for p in posts]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("같은 slug 를 쓰는 글이 두 개 있습니다")

    build_list_page(posts, SITE["title"], SITE["tagline"], FULL + "/", "index.html")
    for cat, key in CATEGORIES.items():
        sub = [p for p in posts if p["category"] == cat]
        build_list_page(sub, cat, f"{cat} 칼럼 모음", FULL + f"/c/{key}/", f"c/{key}/index.html")
    for p in posts:
        build_post(p, posts)
    build_apply()
    build_limit()
    build_widget(posts)
    build_feed(posts)
    (ROOT / ".nojekyll").touch()
    print(f"완료: 글 {len(posts)}개")


if __name__ == "__main__":
    main()
