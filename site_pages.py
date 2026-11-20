# -*- coding: utf-8 -*-
"""홈페이지(회사소개·자금지원·경영지원·첫 화면) 페이지 빌드.

build.py 의 main() 에서 build_site_pages(posts, ctx) 로 불린다.
ctx 에는 build.py 의 page, write, esc, chip, fmt_date, BASE, FULL, SITE, ROOT 가 들어 있다.
"""
import json


def build_site_pages(posts, ctx):
    page, write, esc, chip = ctx["page"], ctx["write"], ctx["esc"], ctx["chip"]
    BASE, FULL, SITE, ROOT = ctx["BASE"], ctx["FULL"], ctx["SITE"], ctx["ROOT"]
    ORG = "기업자금센터"
    results = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))
    years = 2026 - int(SITE.get("since", "2013"))

    def sub_hero(eyebrow, title, lead):
        return f"""<section class="sp-hero">
  <div class="wrap wide">
    <p class="sp-eyebrow">{esc(eyebrow)}</p>
    <h1>{esc(title)}</h1>
    <p class="lead">{esc(lead)}</p>
  </div>
</section>"""

    def facts(rows):
        return '<dl class="sp-facts">' + "".join(
            f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in rows) + "</dl>"

    cta_band = f"""<section class="sp-band">
  <div class="wrap wide sp-band-row">
    <div>
      <h2>우리 회사는 얼마까지 가능할까요?</h2>
      <p>매출과 업력 몇 가지만 넣으면 예상 운전자금 범위를 바로 볼 수 있습니다. 상담은 무료입니다.</p>
    </div>
    <div class="sp-band-btns">
      <a class="btn" href="{BASE}/limit/">예상 한도 계산</a>
      <a class="btn btn-ghost" href="{BASE}/apply/">무료 상담 신청</a>
    </div>
  </div>
</section>"""

    # ---------- 첫 화면 ----------
    case_cards = "".join(
        f"""<li class="hm-case">
  <img src="{BASE}/assets/results/{d['img']}.jpg" alt="" loading="lazy" width="1024" height="560" style="object-position:{d['pos']} center{';transform:scaleX(-1)' if d['flip'] else ''}">
  <div>
    <p class="hm-case-loc">{esc(d['loc'])} · 매출 {esc(d['rev'])}</p>
    <h3>{esc(d['ind'])}</h3>
    <p class="hm-case-fund">{' · '.join(esc(k) + ' <b>' + esc(v) + '</b>' for k, v in d['fund'])}</p>
  </div>
</li>""" for d in results[:3])
    post_rows = "".join(
        f"""<li><a href="{p['url']}">{chip(p['category'])}<span class="hm-post-t">{esc(p['title'])}</span></a></li>""".replace(
            f'<a class="chip', '<span class="chip').replace(f'</a><span class="hm-post-t">', '</span><span class="hm-post-t">')
        for p in posts[:5])
    services = [
        ("운전자금", "인건비·원자재·운영비처럼 회사를 돌리는 데 드는 자금. 정부기관 직접융자와 1금융권 융자를 비교해 가장 유리한 순서로 진행합니다.", f"{BASE}/funding/working/"),
        ("시설자금", "공장·사무소 매입, 신축, 기계 도입에 쓰는 자금. 부지나 기계를 사기 전에 미리 설계해야 한도와 금리가 달라집니다.", f"{BASE}/funding/facility/"),
        ("인증지원", "기업부설연구소·연구개발전담부서 설립을 돕습니다. 세제 혜택과 기관 평가에서 가점을 받을 수 있습니다.", f"{BASE}/support/#certification"),
        ("경영·재무지원", "재무구조와 기업등급을 관리해, 다음 자금을 더 좋은 조건으로 받을 수 있는 회사로 만듭니다.", f"{BASE}/support/#finance"),
    ]
    svc = "".join(f'<li><a href="{u}"><h3>{esc(t)}</h3><p>{esc(d)}</p><span class="more">자세히 보기</span></a></li>' for t, d, u in services)
    home = f"""<section class="hm-hero">
  <div class="wrap wide">
    <p class="sp-eyebrow">기업자금 컨설팅 · {SITE.get('since', '2013')}년부터</p>
    <h1>자금 결정 앞에서,<br>가장 현실적인 답을 드립니다</h1>
    <p class="lead">운전자금·시설자금부터 인증, 재무구조까지. 회사 상황을 숫자로 보고 받을 수 있는 자금과 순서를 정리해 드립니다.</p>
    <div class="hm-btns">
      <a class="btn" href="{BASE}/limit/">예상 한도 계산하기</a>
      <a class="btn btn-ghost" href="{BASE}/apply/">무료 상담 신청</a>
    </div>
    <ul class="hm-stats">
      <li><b>{years}년</b><span>{SITE.get('since', '2013')}년부터 기업자금 현장</span></li>
      <li><b>{SITE.get('team', '85')}명</b><span>지점 자금·세무·구조 전문 인력</span></li>
      <li><b>{SITE.get('cases_year', '315')}건</b><span>지점 연간 자금 진행</span></li>
    </ul>
  </div>
</section>
<section class="wrap wide hm-sec">
  <div class="hm-sec-head"><h2>무엇을 도와드리나요</h2></div>
  <ul class="hm-svc">{svc}</ul>
</section>
<section class="hm-alt">
  <div class="wrap wide hm-sec">
    <div class="hm-sec-head"><h2>최근 지원사례</h2><a class="more" href="{BASE}/results/">사례 {len(results)}건 모두 보기</a></div>
    <ul class="hm-cases">{case_cards}</ul>
  </div>
</section>
<section class="wrap wide hm-sec">
  <div class="hm-sec-head"><h2>자금정보</h2><a class="more" href="{BASE}/info/">전체 글 보기</a></div>
  <p class="hm-sec-lead">매주 월·수요일, 현장 사례와 정책자금 소식을 정리합니다.</p>
  <ul class="hm-posts">{post_rows}</ul>
</section>
{cta_band}
"""
    write("index.html", page(f"{ORG} | 운전자금·시설자금·정책자금 컨설팅",
                             "2013년부터 중소기업 운전자금·시설자금·정책자금을 컨설팅해 온 기업자금센터. 예상 한도 계산과 무료 상담을 받아보세요.",
                             FULL + "/", home))

    # ---------- 회사소개: 인사말 ----------
    vision = [
        ("고객 중심의 서비스", "기업의 현재 상황과 니즈, 향후 성장까지 함께 고려해 가장 알맞은 방법을 제안합니다."),
        ("최고의 컨설팅", "차별화된 금융·컨설팅 서비스로 결과로 증명합니다."),
        ("다양한 영역", "자금 외에도 인증, 재무관리 등 기업에 필요한 종합 컨설팅을 제공합니다."),
        ("지속 가능한 성장", "끊임없는 변화와 혁신으로 고객과 함께 성장하는 것을 목표로 합니다."),
    ]
    # 사진: assets/about/ceo.jpg 파일을 넣으면 자동으로 인사말에 나온다 (없으면 글만)
    photo = ""
    if (ROOT / "assets" / "about" / "ceo.jpg").exists():
        photo = f'<img class="sp-photo" src="{BASE}/assets/about/ceo.jpg" alt="기업자금센터 대표 {esc(SITE.get('ceo', ''))}" width="875" height="1024">'
    vis = "".join(f'<li><b>0{i + 1}</b><h3>{esc(t)}</h3><p>{esc(d)}</p></li>' for i, (t, d) in enumerate(vision))
    about = f"""{sub_hero('회사소개', '인사말', '기업의 지속성장을 함께 설계하는 전략 파트너')}
<section class="wrap wide sp-body sp-split">
  <div>{photo}<blockquote class="sp-quote">기업의 지속성장을 함께 설계하는<br>당신의 전략 파트너.</blockquote></div>
  <div class="prose">
    <p>안녕하십니까.</p>
    <p>저희 기업자금센터는 급변하는 경영환경 속에서 중소·중견기업이 겪는 자금조달의 어려움과 경영의 불확실성을 해결하기 위해 설립되었습니다.</p>
    <p>수많은 기업을 현장에서 직접 만나고 지원해 오며 깨달은 한 가지는, <strong>기업의 성장은 올바른 자금 전략과 체계적인 경영 시스템에서 비롯된다</strong>는 것입니다.</p>
    <p>저희는 단순한 자금 알선이나 컨설팅이 아닌, 각 기업의 상황을 정밀하게 분석하여 맞춤형 자금 솔루션, 경영개선 전략, 지속성장 구조의 설계까지 함께 고민하고 실행합니다.</p>
    <p>앞으로도 고객 기업이 더 큰 시장에서 경쟁력을 갖추고 성장할 수 있도록, 가장 가까운 곳에서 가장 현실적인 해답을 제시하는 파트너가 되겠습니다. 고객의 신뢰를 최우선 가치로 삼아 변함없이 함께하겠습니다.</p>
    <p>감사합니다.</p>
    <p class="sp-sign">기업자금센터 대표 <b>{esc(SITE.get('ceo', ''))}</b></p>
  </div>
</section>
<section class="hm-alt">
  <div class="wrap wide hm-sec">
    <div class="hm-sec-head"><h2>기업자금센터의 비전</h2></div>
    <ul class="sp-vision">{vis}</ul>
  </div>
</section>
{cta_band}
"""
    write("about/index.html", page(f"인사말 | {ORG}", "기업의 지속성장을 함께 설계하는 전략 파트너, 기업자금센터 대표 인사말.", FULL + "/about/", about))

    # ---------- 회사소개: 오시는 길 ----------
    q = "서울 마포구 마포대로 144"
    loc = f"""{sub_hero('회사소개', '오시는 길', '공덕역 4번 출구에서 걸어서 5분입니다.')}
<section class="wrap wide sp-body sp-split">
  <div>
    {facts([('주소', SITE['address']), ('전화', SITE['phone']), ('이메일', SITE['email']), ('교통', '지하철 5·6호선, 경의중앙선, 공항철도 공덕역 4번 출구 직진, 도보 5분')])}
    <div class="hm-btns">
      <a class="btn" href="https://map.naver.com/p/search/{q}" target="_blank" rel="noopener">네이버 지도로 보기</a>
      <a class="btn btn-ghost" href="tel:{SITE['phone'].replace('-', '')}">전화 걸기</a>
    </div>
  </div>
  <div class="sp-map"><iframe title="기업자금센터 위치 지도" src="https://maps.google.com/maps?q={q}&amp;z=16&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>
</section>
"""
    write("about/location/index.html", page(f"오시는 길 | {ORG}", f"{SITE['address']} · 공덕역 4번 출구 도보 5분", FULL + "/about/location/", loc))

    # ---------- 자금지원 ----------
    docs = "재무제표, 사업자등록증 사본, 부가세 과세표준증명원"
    working = f"""{sub_hero('자금지원', '운전자금', '회사 운영에 필요한 단기·유동자금 확보 컨설팅')}
<section class="wrap wide sp-body sp-split">
  <div class="prose">
    <h2>운전자금이란</h2>
    <p>운전자금은 인건비, 원자재 구매, 임차료처럼 회사를 매달 굴러가게 하는 데 드는 자금입니다. 매출이 늘수록 먼저 나가는 돈도 커지기 때문에, 성장하는 회사일수록 운전자금이 막히는 경우가 많습니다.</p>
    <p>기업자금센터는 정부기관 직접융자와 1금융권 융자를 함께 비교해, 회사 등급과 상황에서 가장 낮은 금리와 높은 한도를 받을 수 있는 순서로 진행합니다.</p>
  </div>
  <div>
    <h2 class="sp-h">지원 세부사항</h2>
    {facts([('지원 대상', '매출 10억 원 이상의 개인사업자 및 법인사업자'), ('지원 종류', '정부기관 직접융자 및 1금융권 융자 등'), ('융자 한도', '최대 90억 원 (기업 등급에 따름)'), ('연 금리', '3%~ (기업별 차등)'), ('융자 기간', '5년~10년'), ('상환 방식', '거치 후 원리금 균등분할 또는 만기 일시상환'), ('상담 시 필요 서류', docs)])}
  </div>
</section>
{cta_band}
"""
    write("funding/working/index.html", page(f"운전자금 | {ORG}", "매출 10억 원 이상 개인·법인사업자를 위한 운전자금 컨설팅. 정부기관 직접융자와 1금융권 융자를 비교해 진행합니다.", FULL + "/funding/working/", working))

    facility = f"""{sub_hero('자금지원', '시설자금', '고정시설에 투자되는 기초 자금 확보')}
<section class="wrap wide sp-body sp-split">
  <div class="prose">
    <h2>시설자금이란</h2>
    <p>시설자금은 공장 건물, 사무소, 점포처럼 영업 활동의 기초가 되는 고정시설에 투자하는 자금입니다. 시설물의 매입이나 공사 착공을 위한 자금으로 볼 수 있습니다.</p>
    <p>일반적으로 부지나 기계를 매입하거나 공사를 시작하기 <strong>전에</strong> 시설자금 대출을 진행하며, 신청 기관마다 조건 차이가 큽니다. 기업자금센터는 다수의 조달 실적을 바탕으로 정부 정책자금과 은행 자금을 분석해 가장 합리적인 방법을 찾습니다.</p>
    <p class="sp-note">지원이 어려운 경우: 국세·지방세 체납 기업, 대표자 신용이 불량한 기업 등</p>
  </div>
  <div>
    <h2 class="sp-h">지원 세부사항</h2>
    {facts([('지원 대상', '매출 10억 원 이상의 개인사업자 및 법인사업자'), ('지원 종류', '정부 지원 및 1금융권 대리융자'), ('융자 한도', '최대 200억 원 (기업 등급에 따름)'), ('연 금리', '3%~ (기업별 차등)'), ('융자 기간', '5년~10년'), ('상환 방식', '거치 후 원리금 균등분할 또는 만기 일시상환'), ('상담 시 필요 서류', docs)])}
  </div>
</section>
{cta_band}
"""
    write("funding/facility/index.html", page(f"시설자금 | {ORG}", "공장·사무소 매입, 신축, 기계 도입을 위한 시설자금 컨설팅. 최대 200억 원, 기업 등급에 따라 진행합니다.", FULL + "/funding/facility/", facility))

    # ---------- 경영지원 ----------
    support = f"""{sub_hero('경영지원', '인증지원 · 경영·재무지원', '자금을 받은 다음, 더 좋은 조건으로 다음 자금을 받는 회사로')}
<section class="wrap wide sp-body sp-split" id="certification">
  <div>
    <p class="sp-eyebrow">인증지원</p>
    <h2 class="sp-h">기업부설연구소 · 연구개발전담부서</h2>
  </div>
  <div class="prose">
    <p>기업부설연구소와 연구개발전담부서는 회사가 가진 핵심 기술을 체계적으로 개발하고, 새로운 제품·서비스·공정을 꾸준히 만들어 내기 위한 R&amp;D 조직입니다. 기술 중심의 사업 구조를 갖추고, 중장기적으로 안정적인 성장 기반을 마련하는 데 목적이 있습니다.</p>
    <h3>설립하면 달라지는 점</h3>
    <ol>
      <li>세제 혜택과 비용 절감</li>
      <li>정부·기관 제도 활용 범위 확대</li>
      <li>기술의 자산화와 기업가치 향상</li>
      <li>내부 R&amp;D 역량 강화</li>
    </ol>
  </div>
</section>
<section class="hm-alt" id="finance">
  <div class="wrap wide sp-body sp-split">
    <div>
      <p class="sp-eyebrow">경영·재무지원</p>
      <h2 class="sp-h">재무관리 · 기업등급 관리</h2>
    </div>
    <div class="prose">
      <p>회사가 마주한 재무 위험을 미리 진단하고 재무 전략을 세워, 현금흐름 안정과 재무구조 개선, 자금조달 효율화를 함께 이룹니다.</p>
      <p>평가기관과 금융권의 심사 기준에 맞춰 기업등급을 관리하고 올리는 전략을 제시합니다. 등급이 오르면 같은 회사라도 더 유리한 조건으로 금융거래와 사업 확장을 할 수 있습니다.</p>
    </div>
  </div>
</section>
{cta_band}
"""
    write("support/index.html", page(f"경영지원 | {ORG}", "기업부설연구소 인증지원과 재무관리·기업등급 관리. 다음 자금을 더 좋은 조건으로 받는 회사를 만듭니다.", FULL + "/support/", support))

    # ---------- 개인정보처리방침 ----------
    privacy = f"""{sub_hero('안내', '개인정보처리방침', '기업자금센터가 상담을 위해 받는 개인정보와 그 처리 방법')}
<section class="wrap sp-body">
  <div class="prose">
    <p>기업자금센터(이하 '회사')는 고객의 개인정보를 소중히 여기며, 「개인정보 보호법」 등 관련 법령을 지킵니다.</p>
    <h3>1. 수집하는 개인정보 항목</h3>
    <p>성함, 회사명, 연락처, 이메일, 사업자등록번호, 상담 내용, 한도 계산에 입력한 회사 정보(업종·매출·업력 등), 방문 경로</p>
    <h3>2. 수집 방법</h3>
    <p>홈페이지의 상담 신청, 예상 한도 계산, 입사 지원 양식</p>
    <h3>3. 수집 및 이용 목적</h3>
    <p>상담 내용 확인과 연락, 자금 진행 가능성 안내, 입사 지원자 연락</p>
    <h3>4. 보유 및 이용 기간</h3>
    <p>목적이 달성되면 지체 없이 파기하며, 보유 기간은 최대 3년을 넘기지 않습니다. 법령에 따로 정한 경우에는 그 기간 동안 보관합니다.</p>
    <h3>5. 제3자 제공</h3>
    <p>고객의 동의 없이 개인정보를 외부에 제공하지 않습니다. 자금 신청을 위해 기관에 제출이 필요한 경우에는 미리 동의를 받습니다.</p>
    <h3>6. 쿠키 사용</h3>
    <p>이 홈페이지는 맞춤 서비스를 위한 쿠키를 사용하지 않습니다.</p>
    <h3>7. 개인정보 보호책임자</h3>
    <p>책임자: {esc(SITE.get('ceo', ''))} · 전화: {esc(SITE['phone'])} · 이메일: {esc(SITE['email'])}</p>
    <p>이 방침은 2026년 12월 1일부터 시행합니다.</p>
  </div>
</section>
"""
    write("privacy/index.html", page(f"개인정보처리방침 | {ORG}", "기업자금센터 개인정보처리방침", FULL + "/privacy/", privacy))

    # ---------- 옛 주소 이동 (카페24 시절 주소 → 새 주소) ----------
    moves = {
        "contact": "/apply/",
        "인사말": "/about/",
        "오시는-길": "/about/location/",
        "사업분야-디자인-1": "/funding/working/",
        "시설자금": "/funding/facility/",
        "제품소개": "/funding/working/",
        "인증지원": "/support/#certification",
        "경영_재무-2": "/support/#finance",
        "support/news": "/results/",
        "terms_page/privacy-policy": "/privacy/",
    }
    for old, new in moves.items():
        target = BASE + new
        write(f"{old}/index.html", f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>이동 중 | {ORG}</title><meta name="robots" content="noindex">
<link rel="canonical" href="{FULL}{new}"><meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(target)});</script></head>
<body><p><a href="{target}">새 페이지로 이동</a></p></body></html>
""")
    return ["/", "/about/", "/about/location/", "/funding/working/", "/funding/facility/", "/support/", "/info/", "/privacy/"]
