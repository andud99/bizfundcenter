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
<meta name="naver-site-verification" content="d2a2f0fcdc7f80510ab42e256d2caefc279a14d4" />
<meta name="google-site-verification" content="44HQXpzdSIIOnvWg4qA-urNnDeNAu5dnSopqffZYgrE" />
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
      <a href="{base}/results/">지원 사례</a>
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
  <div class="feature-meta">{chip(first['category'])}</div>
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
    _d = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))
    def _eok(v):
        return float(v.replace("억", "")) if "억" in v else float(v.replace("천만", "").replace("천", "")) * 0.1
    n_cases = len(_d)
    sum_eok = int(sum(_eok(f[1]) for x in _d for f in x["fund"]))
    years = datetime.now(KST).year - 2013
    content = f"""<section class="lim-hero">
  <div class="lim-hero-in">
    <div class="lim-copy">
      <p class="lim-badge">무료 한도 점검</p>
      <h1>운전자금,<br>우리 회사는 <em>얼마까지</em> 될까요?</h1>
      <p class="lim-sub">매출과 업종, 지금 쓰고 있는 자금만 넣으면 <br>받을 수 있는 운전자금의 <b>예상 범위</b>를 바로 보여드립니다. <br>결산이 바뀌기 전에 미리 확인해 두세요.</p>
      <ul class="lim-stats">
        <li><span>상반기 진행 사례</span><b>120<small>건</small></b></li>
        <li><span>상반기 자금 합계</span><b>370<small>억 원</small></b></li>
        <li><span>기업자금 현장</span><b class="lim-since">SINCE 2013</b></li>
      </ul>
      <p class="lim-statnote">2026년 상반기 기업자금센터 진행 기준</p>
    </div>

    <div class="lim-card" id="calcCard">
      <div class="lim-card-head">
        <p class="lim-chip-dark">예상 운전자금 계산</p>
        <ol class="lim-prog" aria-label="진행 단계"><li class="on">회사</li><li>자금 이용</li><li>연락처</li></ol>
      </div>
      <form id="calcForm" novalidate>
        <div class="lim-page" data-page="1">
          <div class="lim-field"><p class="lim-q">업종</p>
            <div class="lim-chips" role="radiogroup">
              <label><input type="radio" name="ind" value="mfg" checked><span>제조</span></label>
              <label><input type="radio" name="ind" value="tech"><span>IT·지식서비스</span></label>
              <label><input type="radio" name="ind" value="whole"><span>도소매·유통</span></label>
              <label><input type="radio" name="ind" value="cons"><span>건설·공사</span></label>
              <label><input type="radio" name="ind" value="svc"><span>음식·기타 서비스</span></label>
            </div>
          </div>
          <div class="lim-field"><p class="lim-q">업력</p>
            <div class="lim-chips c3" role="radiogroup">
              <label><input type="radio" name="age" value="1"><span>3년 미만</span></label>
              <label><input type="radio" name="age" value="2" checked><span>3~7년</span></label>
              <label><input type="radio" name="age" value="3"><span>7년 이상</span></label>
            </div>
          </div>
          <div class="lim-field"><p class="lim-q">소재지</p>
            <div class="lim-chips c2" role="radiogroup">
              <label><input type="radio" name="region" value="cap" checked><span>수도권</span></label>
              <label><input type="radio" name="region" value="local"><span>지방</span></label>
            </div>
          </div>
          <div class="lim-row2">
            <label class="lim-in"><span>최근 1년 매출 <small>(억 원)</small></span><input id="rev" type="number" min="0" step="0.1" inputmode="decimal" placeholder="예: 25"></label>
            <label class="lim-in"><span>상시 직원 수 <small>(명)</small></span><input id="emp" type="number" min="0" step="1" inputmode="numeric" placeholder="대표 제외"></label>
          </div>
          <div class="lim-field"><p class="lim-q">최근 결산</p>
            <div class="lim-chips c2" role="radiogroup">
              <label><input type="radio" name="profit" value="plus" checked><span>흑자</span></label>
              <label><input type="radio" name="profit" value="minus"><span>적자</span></label>
            </div>
          </div>
          <button class="lim-next" type="button" data-go="2">다음</button>
        </div>

        <div class="lim-page" data-page="2" hidden>
          <div class="lim-field"><p class="lim-q">대표님 개인 신용점수</p>
            <div class="lim-chips c2" role="radiogroup">
              <label><input type="radio" name="score" value="a"><span>840점 이상</span></label>
              <label><input type="radio" name="score" value="b" checked><span>740~839점</span></label>
              <label><input type="radio" name="score" value="c"><span>640~739점</span></label>
              <label><input type="radio" name="score" value="d"><span>640점 미만</span></label>
            </div>
          </div>
          <div class="lim-row2">
            <label class="lim-in">회사 신용등급
              <select id="grade">
                <option value="0">잘 모르겠음</option>
                <option value="0">B 이하</option>
                <option value="1">B+ ~ BB</option>
                <option value="2">BB+ 이상</option>
              </select>
            </label>
            <label class="lim-in"><span>연평균 수출액 <small>(만 달러)</small></span><input id="exp" type="number" min="0" step="1" inputmode="numeric" value="0"></label>
          </div>
          <p class="lim-q">지금 쓰고 있는 정책자금 <small>(없으면 0)</small></p>
          <div class="lim-row2">
            <label class="lim-in"><span>신보·기보 합계 <small>(억)</small></span><input id="useA" type="number" min="0" step="0.1" inputmode="decimal" value="0"></label>
            <label class="lim-in"><span>지역 재단 <small>(억)</small></span><input id="useB" type="number" min="0" step="0.1" inputmode="decimal" value="0"></label>
            <label class="lim-in"><span>중진공 운전자금 <small>(억)</small></span><input id="useCamt" type="number" min="0" step="0.1" inputmode="decimal" value="0"></label>
            <label class="lim-in"><span>소진공 직접대출 <small>(억)</small></span><input id="useD" type="number" min="0" step="0.1" inputmode="decimal" value="0"></label>
          </div>
          <label class="lim-in">중진공 직접대출 받은 횟수
            <select id="useC">
              <option value="0">받은 적 없음</option>
              <option value="1">1~2회 (올해는 아직)</option>
              <option value="y">올해 이미 받음</option>
              <option value="3">3회 모두 받음</option>
            </select>
          </label>
          <p class="lim-q">해당하는 것 모두</p>
          <div class="lim-tags">
            <label><input type="checkbox" name="cert"><span>벤처기업</span></label>
            <label><input type="checkbox" name="cert"><span>이노비즈·메인비즈</span></label>
            <label><input type="checkbox" name="cert"><span>기업부설연구소</span></label>
            <label><input type="checkbox" name="cert"><span>특허</span></label>
            <label><input type="checkbox" id="ipsales"><span>매출 비중이 큰 특허</span></label>
            <label><input type="checkbox" id="lead"><span>유망·선도 업종</span></label>
            <label><input type="checkbox" id="agri"><span>농수산물 원료 제조</span></label>
            <label><input type="checkbox" id="land"><span>부동산 보유</span></label>
            <label><input type="checkbox" id="tax"><span>밀린 세금 있음</span></label>
          </div>
          <div class="lim-nav"><button class="lim-back" type="button" data-go="1">이전</button><button class="lim-next" type="button" data-go="3">다음</button></div>
        </div>

        <div class="lim-page" data-page="3" hidden>
          <p class="lim-q">결과 받으실 연락처</p>
          <div class="lim-row2">
            <label class="lim-in">성함<input id="cName" type="text" autocomplete="name" placeholder="대표자 성함"></label>
            <label class="lim-in">회사명<input id="cCompany" type="text" autocomplete="organization"></label>
            <label class="lim-in">연락처<input id="cPhone" type="tel" autocomplete="tel" inputmode="tel" placeholder="010-0000-0000"></label>
            <label class="lim-in">사업자등록번호<input id="cBiz" type="text" inputmode="numeric" placeholder="000-00-00000" maxlength="12"></label>
          </div>
          <div class="lim-consent">
            <label><input type="checkbox" id="cAgree"> 개인정보 수집·이용에 동의합니다 (필수)</label>
            <details>
              <summary>내용 보기</summary>
              <ul>
                <li>수집 항목: 성함, 회사명, 연락처, 사업자등록번호, 이 화면에 입력한 회사 정보</li>
                <li>수집 목적: 예상 한도 안내 및 자금 상담 연락</li>
                <li>보유 기간: 수집일로부터 1년. 기간이 지나거나 삭제를 요청하시면 지체 없이 파기합니다.</li>
                <li>처리 위탁: 접수 내용은 양식 전송 서비스(Formspree, 미국)를 거쳐 기업자금센터 담당자 메일로 전달됩니다.</li>
                <li>동의를 거부할 수 있으며, 거부하시면 예상 한도 결과를 보실 수 없습니다.</li>
              </ul>
            </details>
          </div>
          <div class="lim-nav"><button class="lim-back" type="button" data-go="2">이전</button><button class="btn lim-submit" type="submit">예상 한도 보기</button></div>
        </div>
        <p class="form-note" id="calcNote" role="status"></p>
      </form>
      <p class="lim-foot">상담 비용 0원 · 입력하신 정보는 상담 목적으로만 사용됩니다</p>
    </div>
  </div>
</section>

<section class="wrap lim-after">
  <div id="result" class="lim-result" hidden>
    <p class="lim-eyebrow">예상 운전자금 한도</p>
    <p class="lim-range" id="range"></p>
    <p class="lim-doors" id="doors"></p>
    <ul class="lim-notes" id="notes"></ul>
    <p class="lim-disc">입력하신 정보로 계산한 참고용 범위입니다. 실제 금액은 재무제표, 기존 거래, 신청 시기와 기관 판단에 따라 달라집니다. 공장·설비 같은 시설자금은 따로 봐야 합니다.</p>
  </div>

  <div id="detail" class="lim-detail" hidden>
    <h2>어느 문부터, 어떤 순서로?</h2>
    <p>같은 한도라도 어디에 먼저 들어가느냐, 결산 전후 언제 신청하느냐에 따라 결과가 크게 달라집니다. 순서를 잘못 잡으면 뒤의 문이 닫히기도 합니다. 우리 회사에 맞는 순서가 궁금하시면 상담을 신청해 주세요.</p>
    <div class="lim-ask" id="askBox">
      <label>편한 연락 시간
        <select id="askTime">
          <option>언제든 괜찮음</option>
          <option>오전 (9~12시)</option>
          <option>오후 (1~6시)</option>
        </select>
      </label>
      <label>궁금한 점 (선택)<textarea id="askMsg" rows="3" placeholder="예: 다음 달까지 운전자금이 필요합니다"></textarea></label>
      <button class="btn" type="button" id="askBtn">무료 상담 신청하기</button>
      <p class="form-note" id="askNote" role="status"></p>
    </div>
    <div id="thanks" class="thanks" hidden>
      <h2>상담 신청이 접수되었습니다</h2>
      <p>담당자가 확인 후 영업일 기준 1~2일 안에 연락드립니다.</p>
      <a class="more" href="{BASE}/results/">지원 사례 보기</a>
    </div>
  </div>
</section>

<section class="lim-svc">
  <div class="wrap lim-svc-in">
    <p class="lim-eyebrow2">ONE-STOP</p>
    <h2>한 번의 상담으로 자금·세금·구조까지</h2>
    <p class="lim-svc-lead">필요한 자금을 마련하는 데서 끝나지 않습니다. 회사 구조와 세금까지 함께 보고, 맞는 순서로 진행합니다.</p>
    <ul class="lim-svc-grid">
      <li><b>운전자금</b><span>원자재·인건비처럼 회사가 돌아가는 데 필요한 자금</span></li>
      <li><b>시설자금</b><span>공장·기계설비 구입과 증설 자금</span></li>
      <li><b>기술·특허자금</b><span>특허와 기술력을 평가받아 연결하는 자금</span></li>
      <li><b>수출자금</b><span>수출 실적이 있는 기업을 위한 별도 자금</span></li>
      <li><b>기업인증</b><span>벤처·이노비즈·메인비즈·연구소 설립</span></li>
      <li><b>세금·구조</b><span>가지급금, 법인전환, 재무구조 개선</span></li>
    </ul>
    <a class="lim-svc-btn" href="{BASE}/results/">진행 사례 보기</a>
  </div>
</section>

<section class="lim-band">
  <div class="wrap">
    <h2>같은 회사라도,<br>결과가 달라집니다</h2>
    <p>어느 기관에 먼저 들어가느냐, 결산 전후 언제 신청하느냐. <br>우리 회사에 맞는 순서를 무료로 점검해 드립니다.</p>
    <a class="btn" href="#calcCard">지금 무료로 계산하기</a>
  </div>
</section>
<script>
(function () {{
  /* 산식 설정 — 숫자만 고치면 계산이 바뀝니다. 금액 단위: 억 원 */
  var R = {{
    A: {{ rate: {{ mfg: 1/4, tech: 1/6, whole: 1/6, cons: 1/6, svc: 1/6 }},
         ageCap: {{ 1: 3, 2: 10, 3: 15 }}, startupFloor: 1, branchCap: 15 }},  // 지점 한도 15억 (신·기보 중복 안 됨)
    B: {{ totalCap: 8, max: 2 }},
    C: {{ low: 1, high: 2, times: 3,
         total: {{ cap: [2, 3], local: [3, 5] }} }},  // 1년 1회 1~2억, 누적 수도권 2~3억 / 지방 3~5억
    D: {{ empMax: {{ mfg: 10, cons: 10, tech: 5, whole: 5, svc: 5 }}, low: 0.5,
         totalMfgExport: 2, totalOther: 1, region: {{ cap: 0.8, local: 1.0 }} }},  // 누적 상한: 제조+수출 2억, 그 외 1억
    H: {{ revMin: 100, useMin: 15, low: 7, high: 10 }},  // 매출 100억 이상 + 신기보 15억 사용 시 추가 (유동화)
    E: {{ rate: 1/4, max: 5 }},
    G: {{ low: 1, high: 3 }},                      // 매출 비중이 큰 특허 활용
    leadRate: 1/4,                                // 유망·선도 업종은 제조와 같은 비율
    F: {{ fx: 0.000014, directMin: 1, directMax: 100, directRevMax: 100,
         direct: {{ 0: 0, 1: 0.5, 2: 1 }}, low: 0.10, high: 0.20 }},
    score: {{ a: 1.0, b: 0.85, c: 0.6, d: 0.3 }},
    loss: 0.7, certBonus: 0.1, certMax: 0.3, rangeLow: 0.7
  }};

  var FORM_URL = '{esc(SITE['formspree'])}';
  var last = null;
  function $(id) {{ return document.getElementById(id); }}
  function num(id) {{ var v = parseFloat($(id).value); return v > 0 ? v : 0; }}
  function eok(v) {{
    if (v < 1) return Math.round(v * 10) * 1000 + '만 원';
    return (Math.round(v * 10) / 10).toString().replace(/\\.0$/, '') + '억 원';
  }}
  function val(n) {{ var r = document.querySelector('input[name="' + n + '"]:checked'); return r ? r.value : $(n).value; }}
  function txt(n) {{ var r = document.querySelector('input[name="' + n + '"]:checked'); return r ? r.nextElementSibling.textContent : $(n).selectedOptions[0].text; }}
  function validBiz(d) {{
    if (!/^\\d{{10}}$/.test(d)) return false;
    var w = [1, 3, 7, 1, 3, 7, 1, 3, 5], sum = 0;
    for (var i = 0; i < 9; i++) sum += Number(d[i]) * w[i];
    sum += Math.floor(Number(d[8]) * 5 / 10);
    return (10 - (sum % 10)) % 10 === Number(d[9]);
  }}

  var calc = $('calcForm');
  function go(n) {{
    calc.querySelectorAll('.lim-page').forEach(function (pg) {{ pg.hidden = pg.dataset.page !== String(n); }});
    document.querySelectorAll('.lim-prog li').forEach(function (li, i) {{ li.classList.toggle('on', i < n); }});
    $('calcNote').textContent = '';
  }}
  calc.querySelectorAll('[data-go]').forEach(function (b) {{
    b.addEventListener('click', function () {{
      var n = Number(b.dataset.go);
      if (n === 2 && !(parseFloat($('rev').value) >= 0)) {{ $('calcNote').textContent = '최근 1년 매출을 숫자로 넣어 주세요.'; $('rev').focus(); return; }}
      go(n);
      $('calcCard').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
  }});
  calc.addEventListener('submit', function (e) {{
    e.preventDefault();
    var rev = parseFloat($('rev').value);
    if (!(rev >= 0)) {{ go(1); $('calcNote').textContent = '최근 1년 매출을 숫자로 넣어 주세요.'; $('rev').focus(); return; }}
    var bizDigits = $('cBiz').value.replace(/\\D/g, '');
    var phoneDigits = $('cPhone').value.replace(/\\D/g, '');
    if (!$('cName').value.trim()) {{ $('calcNote').textContent = '성함을 넣어 주세요.'; $('cName').focus(); return; }}
    if (!$('cCompany').value.trim()) {{ $('calcNote').textContent = '회사명을 넣어 주세요.'; $('cCompany').focus(); return; }}
    if (phoneDigits.length < 9) {{ $('calcNote').textContent = '연락 가능한 번호를 넣어 주세요.'; $('cPhone').focus(); return; }}
    if (!validBiz(bizDigits)) {{ $('calcNote').textContent = '사업자등록번호 10자리를 정확히 넣어 주세요.'; $('cBiz').focus(); return; }}
    if (!$('cAgree').checked) {{ $('calcNote').textContent = '개인정보 수집·이용에 동의하셔야 결과를 보실 수 있습니다.'; $('cAgree').focus(); return; }}
    $('calcNote').textContent = '';

    var ind = val('ind'), age = val('age'), sc = val('score'), grade = $('grade').value;
    var emp = num('emp'), exp = num('exp'), useA = num('useA'), useB = num('useB');
    var useC = $('useC').value, useD = num('useD'), region = val('region');
    var certs = calc.querySelectorAll('input[name=cert]:checked').length;
    var loss = val('profit') === 'minus';
    var adj = R.score[sc] * (loss ? R.loss : 1);

    // 갈래 A
    var rate = R.A.rate[ind];
    if ($('lead').checked) rate = Math.max(rate, R.leadRate);
    var a = rev * rate;
    if (age !== '3' && (sc === 'a' || sc === 'b')) a = Math.max(a, R.A.startupFloor);
    a = Math.min(a, R.A.ageCap[age]) * adj * (1 + Math.min(certs * R.certBonus, R.certMax));
    a = Math.max(0, Math.min(a, R.A.branchCap) - useA);

    // 갈래 B: 전체 합계 상한 안에서만
    var room = R.B.totalCap - (useA + a + useB);
    var b = Math.max(0, Math.min(R.B.max - useB, room)) * R.score[sc];

    // 갈래 C: 1년 1회, 최대 횟수
    var cOk = useC === '0' || useC === '1';
    var useCamt = num('useCamt');
    var ct = R.C.total[region];
    var cLow = cOk ? Math.min(R.C.low, Math.max(0, ct[0] - useCamt)) * adj : 0;
    var cHigh = cOk ? Math.min(R.C.high, Math.max(0, ct[1] - useCamt)) * adj : 0;

    // 갈래 D: 소규모 사업장, 횟수 제한
    var dTotal = (ind === 'mfg' && exp > 0) ? R.D.totalMfgExport : R.D.totalOther;
    var dRoom = Math.max(0, dTotal - useD);
    var dOk = emp < R.D.empMax[ind] && sc !== 'd' && dRoom > 0;
    var dHigh = dOk ? dRoom * R.D.region[region] : 0;
    var dLow = dOk ? Math.min(R.D.low, dHigh) : 0;

    // 갈래 H: 대형 기업 추가
    var hOk = rev >= R.H.revMin && useA >= R.H.useMin;
    var hLow = hOk ? R.H.low : 0, hHigh = hOk ? R.H.high : 0;

    // 갈래 E: 농수산물 원료 제조
    var eAmt = 0;
    if ($('agri').checked && ind === 'mfg') eAmt = Math.min(R.E.max, Math.max(0, rev * R.E.rate - (useA + a + useB + b))) * adj;

    // 갈래 F: 수출 실적
    var fLow = 0, fHigh = 0, fWay = '';
    if (exp > 0) {{
      var gen = exp * 10000 * R.F.fx;
      var gLow = gen * R.F.low, gHigh = gen * R.F.high;
      var direct = (exp >= R.F.directMin && exp < R.F.directMax && rev < R.F.directRevMax) ? R.F.direct[grade] : 0;
      fLow = Math.max(direct, gLow); fHigh = Math.max(direct, gHigh);
      fWay = direct >= gHigh ? 'F간편' : (direct > 0 ? 'F간편/일반 비교' : 'F일반');
    }}

    var gAmt = $('ipsales').checked ? R.G.high * R.score[sc] : 0;
    var gLow = $('ipsales').checked ? R.G.low * R.score[sc] : 0;

    var parts = [
      ['A', a * R.rangeLow, a], ['B', b * R.rangeLow, b], ['C', cLow, cHigh],
      ['D', dLow, dHigh], ['E', eAmt * R.rangeLow, eAmt], ['F', fLow, fHigh], ['G', gLow, gAmt], ['H', hLow, hHigh]
    ];
    var low = 0, high = 0, doors = 0;
    parts.forEach(function (p) {{ low += p[1]; high += p[2]; if (p[2] >= 0.1) doors++; }});

    var notes = [];
    if ($('tax').checked) notes.push('밀린 세금이 있으면 대부분의 심사가 그 단계에서 멈춥니다. 세금 정리가 먼저입니다.');
    if (sc === 'c' || sc === 'd') notes.push('대표님 신용점수가 한도를 누르고 있습니다. 점수를 올리면 같은 회사라도 범위가 달라집니다.');
    if (loss) notes.push('적자 결산은 한도를 줄입니다. 흑자로 돌아선 결산이 나온 뒤가 유리할 수 있습니다.');
    if (age === '1') notes.push('결산이 3년치 쌓이기 전에는 한도가 작게 묶이는 경우가 많습니다.');
    if (exp > 0) notes.push('수출 실적이 있으면 일반 운영자금과 별도로 열리는 문이 있습니다. 수출 규모에 따라 유리한 방식이 다릅니다.');
    if ($('ipsales').checked) notes.push('매출로 이어지는 특허는 그 자체로 자금을 끌어오는 자산이 될 수 있습니다.');
    if ($('land').checked) notes.push('부동산이 있다면 위 범위와 별도로 담보를 활용한 자금도 가능합니다.');
    if (certs === 0 && (ind === 'mfg' || ind === 'tech')) notes.push('제조·기술 업종은 인증을 갖추면 범위가 넓어지는 경우가 많습니다.');

    $('range').textContent = high < 0.3 ? '추가 여력 확인 필요' : eok(low) + ' ~ ' + eok(high);
    $('doors').textContent = doors > 0 ? '우리 회사가 두드릴 수 있는 문: ' + doors + '곳' : '';
    var ul = $('notes'); ul.innerHTML = '';
    notes.forEach(function (t) {{ var li = document.createElement('li'); li.textContent = t; ul.appendChild(li); }});
    ul.hidden = notes.length === 0;

    var r1 = function (v) {{ return Math.round(v * 10) / 10; }};
    var summary = [
      '업종 ' + txt('ind'), '업력 ' + txt('age'), '매출 ' + rev + '억', '직원 ' + emp + '명',
      loss ? '적자' : '흑자', '수출 ' + exp + '만불', '대표신용 ' + txt('score'), '기업등급 ' + txt('grade'),
      '기존A ' + useA + '억', '기존B ' + useB + '억', '기존C ' + useCamt + '억', 'C이력 ' + txt('useC'), '기존D ' + useD + '억', '소재지 ' + txt('region'),
      '인증 ' + certs + '개', $('lead').checked ? '유망·선도' : '', $('ipsales').checked ? '매출 특허' : '', $('agri').checked ? '농수산 원료' : '', $('land').checked ? '부동산 있음' : '',
      $('tax').checked ? '체납 있음' : '',
      '계산: ' + parts.filter(function (p) {{ return p[2] > 0; }}).map(function (p) {{ return p[0] + ' ' + r1(p[1]) + '~' + r1(p[2]); }}).join(', ') + (fWay ? ' (' + fWay + ')' : ''),
      '합계 ' + $('range').textContent
    ].filter(Boolean).join(' / ');

    $('result').hidden = false; $('detail').hidden = false;
    var fd = new FormData();
    fd.append('name', $('cName').value.trim());
    fd.append('company', $('cCompany').value.trim());
    fd.append('phone', $('cPhone').value.trim());
    fd.append('bizno', bizDigits.replace(/(\\d{{3}})(\\d{{2}})(\\d{{5}})/, '$1-$2-$3'));
    fd.append('calc', summary);
    last = {{ fd: fd, company: $('cCompany').value.trim(), phone: $('cPhone').value.trim() }};
    fd.append('consent', '개인정보 수집·이용 동의함 (' + new Date().toLocaleString('ko-KR') + ')');
    fd.append('_subject', '[예상 한도] ' + $('cCompany').value.trim() + ' / ' + $('range').textContent);
    fd.append('_source', '예상 한도 계산');
    var btn = calc.querySelector('button[type=submit]');
    btn.disabled = true;
    fetch(FORM_URL, {{ method: 'POST', body: fd, headers: {{ 'Accept': 'application/json' }} }})
      .then(function (r) {{ if (!r.ok) throw new Error(); }})
      .catch(function () {{}})
      .then(function () {{ btn.disabled = false; }});
    $('result').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});

  $('askBtn').addEventListener('click', function () {{
    if (!last) return;
    var btn = $('askBtn');
    btn.disabled = true; $('askNote').textContent = '보내는 중입니다...';
    var fd = new FormData();
    last.fd.forEach(function (v, k) {{ if (k !== '_subject' && k !== '_source') fd.append(k, v); }});
    fd.append('time', $('askTime').value);
    fd.append('message', $('askMsg').value.trim());
    fd.append('_subject', '[상담 신청] ' + last.company + ' / ' + last.phone);
    fd.append('_source', '예상 한도 계산 → 상담 신청');
    fetch(FORM_URL, {{ method: 'POST', body: fd, headers: {{ 'Accept': 'application/json' }} }})
      .then(function (r) {{ if (!r.ok) throw new Error(); $('askBox').hidden = true; $('thanks').hidden = false; }})
      .catch(function () {{ btn.disabled = false; $('askNote').textContent = '신청이 전송되지 않았습니다. 잠시 후 다시 눌러 주세요.'; }});
  }});
}})();
</script>
"""
    write("limit/index.html", page(f"예상 운전자금 한도 계산 | {SITE['title']}", "업종, 매출, 신용, 지금 쓰는 정책자금을 넣으면 받을 수 있는 운전자금의 대략적인 범위를 보여드립니다.", FULL + "/limit/", content))


def build_results():
    data = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))
    groups = {"mfg": "제조", "trade": "도소매·유통", "svc": "서비스·기타"}
    icon = {
        "mfg": '<path d="M14 100V56l26 16V56l26 16V56l26 16V24h14v76z"/><path d="M34 86h10M58 86h10M82 86h10"/>',
        "trade": '<path d="M18 40l42-20 42 20v44l-42 20-42-20z"/><path d="M18 40l42 20 42-20M60 60v44"/>',
        "svc": '<rect x="16" y="38" width="88" height="62" rx="6"/><path d="M44 38V26h32v12M16 64h88"/>',
    }
    cards = []
    for d in data:
        rows = "".join(f'<div class="rs-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in d["fund"])
        cards.append(f'''<li class="rs-card" data-grp="{d['grp']}">
  <div class="rs-top"><img src="{BASE}/assets/results/{d['img']}.jpg" alt="{esc(d['ind'])} 참고 이미지" loading="lazy" width="1024" height="560" style="object-position:{d['pos']} center{';transform:scaleX(-1)' if d['flip'] else ''}"><span class="rs-tag rs-{d['grp']}">{groups[d['grp']]}</span></div>
  <div class="rs-body">
    <h2>{esc(d['ind'])}</h2>
    <dl>
      <div class="rs-row"><dt>위치</dt><dd>{esc(d['loc'])}</dd></div>
      <div class="rs-row"><dt>매출규모</dt><dd>{esc(d['rev'])}</dd></div>
      {rows}
    </dl>
  </div>
</li>''')
    chips = '<button type="button" class="rs-chip" aria-pressed="true" data-f="all">전체</button>' + "".join(
        f'<button type="button" class="rs-chip" aria-pressed="false" data-f="{k}">{v}</button>' for k, v in groups.items())
    content = f"""<section class="wrap results">
  <p class="rs-eyebrow">기업자금센터 진행 사례</p>
  <h1>이런 회사들이 자금을 마련했습니다</h1>
  <p class="lead">2026년 상반기 지점에서 진행한 사례 {len(data)}건을 업종과 매출 규모로 정리했습니다. 우리 회사와 비슷한 곳을 찾아보세요.</p>
  <div class="rs-chips" role="group" aria-label="업종으로 보기">{chips}</div>
  <ul class="rs-grid" id="rsGrid">
{''.join(cards)}
  </ul>
  <p class="rs-note">업체명과 자세한 진행 내역은 개인정보 보호를 위해 공개하지 않습니다. 같은 조건이라도 결과는 회사 상황, 시기, 기관 판단에 따라 달라집니다.<br>사진은 이해를 돕기 위해 AI로 만든 참고 이미지이며, 실제 고객사와 관련이 없습니다.</p>
  <div class="rs-cta">
    <div>
      <h2>우리 회사는 얼마나 가능할까요?</h2>
      <p>회사 정보 몇 가지로 예상 운전자금 범위를 바로 확인해 보세요.</p>
    </div>
    <div class="rs-cta-btns">
      <a class="btn" href="{BASE}/limit/">예상 한도 계산하기</a>
      <a class="more" href="{BASE}/c/cases/">사례 이야기 읽기</a>
    </div>
  </div>
</section>
<script>
(function () {{
  var chips = document.querySelectorAll('.rs-chip');
  var cards = document.querySelectorAll('.rs-card');
  chips.forEach(function (c) {{
    c.addEventListener('click', function () {{
      chips.forEach(function (x) {{ x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); }});
      var f = c.dataset.f;
      cards.forEach(function (k) {{ k.hidden = !(f === 'all' || k.dataset.grp === f); }});
    }});
  }});
}})();
</script>
"""
    write("results/index.html", page(f"지원 사례 모음 | {SITE['title']}", f"기업자금센터가 2026년 상반기에 진행한 자금 사례 {len(data)}건. 업종, 지역, 매출 규모별로 어떤 자금을 얼마나 마련했는지 확인해 보세요.", FULL + "/results/", content))


def build_widget(posts):
    items = "".join(
        f'<li><a href="{FULL}/p/{p["slug"]}/" target="_top"><span>{esc(p["category"])}</span>{esc(p["title"])}</a></li>'
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
    urls = [f"{FULL}/", f"{FULL}/apply/", f"{FULL}/limit/", f"{FULL}/results/"] + [f"{FULL}/p/{p['slug']}/" for p in posts]
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
    build_results()
    build_widget(posts)
    build_feed(posts)
    (ROOT / ".nojekyll").touch()
    print(f"완료: 글 {len(posts)}개")


if __name__ == "__main__":
    main()
