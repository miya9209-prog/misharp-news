import html
import json
import re
from datetime import datetime
from urllib.parse import urljoin

import feedparser
import pytz
import requests
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(
    page_title="MISHARP NEWS POST | 패션·IT·소비유통·경제 뉴스 브리핑",
    layout="wide",
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

SITE_URL = "https://misharp-news-post.streamlit.app"
OG_IMAGE_URL = SITE_URL
try:
    SITE_URL = st.secrets.get("SITE_URL", SITE_URL)
    OG_IMAGE_URL = st.secrets.get("OG_IMAGE_URL", OG_IMAGE_URL)
except Exception:
    pass

SEO_TITLE = "MISHARP NEWS POST | 패션·IT·소비유통·경제기사 뉴스·정보 브리핑"
SEO_DESCRIPTION = (
    "MISHARP NEWS POST는 패션, 온라인마케팅, 소비유통, IT, 경제 뉴스를 한 화면에서 정리해 보는 실시간 뉴스 브리핑 페이지입니다. "
    "서울 날씨와 공기지수, 정책·지원 링크, 미샵을 위한 오늘의 인사이트까지 함께 제공합니다."
)
SEO_KEYWORDS = (
    "MISHARP NEWS POST, 패션 뉴스, 유통 뉴스, IT 뉴스, 온라인마케팅 뉴스, 경제 뉴스 브리핑, 서울 날씨, 공기지수, 미샵 인사이트"
)

POLICY_HTML = """
<h1>개인정보처리방침 · 서비스약관</h1>
<h2>1. 서비스 안내</h2>
<p>MISHARP NEWS POST는 공개된 뉴스와 공공기관·전문기관의 공개 정보 링크를 정리해 보여주는 뉴스·정보 브리핑 페이지입니다.</p>
<h2>2. 개인정보 처리</h2>
<p>이 페이지는 별도의 회원가입 없이 이용할 수 있으며, 이용자 식별을 위한 민감한 개인정보를 수집하지 않습니다. 배포 환경에서 기본 접속 로그가 저장될 수 있습니다.</p>
<h2>3. 외부 링크 안내</h2>
<p>기사와 관련 정보 사이트는 외부 페이지로 연결되며, 각 사이트의 정책과 저작권 기준이 우선 적용됩니다.</p>
<h2>4. 면책</h2>
<p>뉴스 요약과 AI 인사이트는 참고용 정보이며, 사업·투자·마케팅·운영의 최종 판단은 이용자 책임입니다.</p>
<h2>5. 문의</h2>
<p>운영 기준은 MISHARP COMPANY by MIYAWA에 따릅니다.</p>
"""


def inject_seo_meta():
    website_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "MISHARP NEWS POST",
        "url": SITE_URL,
        "description": SEO_DESCRIPTION,
        "inLanguage": "ko-KR",
        "publisher": {"@type": "Organization", "name": "MISHARP COMPANY by MIYAWA"},
    }
    webpage_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": SEO_TITLE,
        "url": SITE_URL,
        "description": SEO_DESCRIPTION,
        "inLanguage": "ko-KR",
    }
    seo_html = f"""
    <script>
    (function() {{
        const title = {json.dumps(SEO_TITLE)};
        const description = {json.dumps(SEO_DESCRIPTION)};
        const keywords = {json.dumps(SEO_KEYWORDS)};
        const canonicalUrl = {json.dumps(SITE_URL)};
        const ogImage = {json.dumps(OG_IMAGE_URL)};
        document.title = title;
        function setMeta(attr, key, value) {{
            let el = document.head.querySelector(`meta[${{attr}}="${{key}}"]`);
            if (!el) {{
                el = document.createElement('meta');
                el.setAttribute(attr, key);
                document.head.appendChild(el);
            }}
            el.setAttribute('content', value);
        }}
        function setLink(rel, href) {{
            let el = document.head.querySelector(`link[rel="${{rel}}"]`);
            if (!el) {{
                el = document.createElement('link');
                el.setAttribute('rel', rel);
                document.head.appendChild(el);
            }}
            el.setAttribute('href', href);
        }}
        setMeta('name', 'description', description);
        setMeta('name', 'keywords', keywords);
        setMeta('property', 'og:type', 'website');
        setMeta('property', 'og:title', title);
        setMeta('property', 'og:description', description);
        setMeta('property', 'og:url', canonicalUrl);
        setMeta('property', 'og:image', ogImage);
        setMeta('name', 'twitter:card', 'summary_large_image');
        setMeta('name', 'twitter:title', title);
        setMeta('name', 'twitter:description', description);
        setMeta('name', 'twitter:image', ogImage);
        setLink('canonical', canonicalUrl);
        function upsertJsonLd(id, payload) {{
            let el = document.head.querySelector(`#${{id}}`);
            if (!el) {{
                el = document.createElement('script');
                el.type = 'application/ld+json';
                el.id = id;
                document.head.appendChild(el);
            }}
            el.textContent = JSON.stringify(payload);
        }}
        upsertJsonLd('misharp-news-website', {json.dumps(website_ld, ensure_ascii=False)});
        upsertJsonLd('misharp-news-webpage', {json.dumps(webpage_ld, ensure_ascii=False)});
    }})();
    </script>
    """
    components.html(seo_html, height=0, width=0)


inject_seo_meta()

st.markdown(
    """
<style>
:root{
  --text:#f8fafc;
  --muted:#9fb0c8;
  --line:rgba(90,110,139,.28);
  --blue:#9cc8ff;
}
html, body, [data-testid="stAppViewContainer"]{
  background: linear-gradient(180deg,#020817 0%, #071122 100%);
  color: var(--text);
}
[data-testid="stSidebar"]{display:none !important;}
.block-container{
  padding-top:4rem !important;
  padding-bottom:2.2rem;
  max-width:1460px;
}
.main-title{
  font-size:4.8rem;
  line-height:1.04;
  font-weight:900;
  color:#ffffff;
  margin:0 0 .3rem 0;
}
.main-sub{
  font-size:1.12rem;
  color:#d8e4f3;
  line-height:1.55;
  margin-bottom:1rem;
  font-weight:700;
}
.title-line{
  margin:1.2rem 0 1.35rem 0;
  border-top:1px solid rgba(130,160,205,.22);
}
.info-box{
  background: rgba(15,29,51,.72);
  border:1px solid rgba(80,110,150,.30);
  border-radius:14px;
  padding:12px 15px;
  color:#edf2f7;
  font-weight:700;
  font-size:.96rem;
  margin-bottom:12px;
  min-height:76px;
}
.section-title{
  font-size:1.55rem;
  font-weight:900;
  margin:1.05rem 0 .8rem 0;
  color:#fff;
}
.news-divider{
  width:1px;
  background:rgba(120,145,185,.26);
  align-self:stretch;
  margin:0 6px;
}
.news-item{
  display:block;
  background: rgba(20,38,64,.88);
  border:1px solid rgba(74,101,141,.34);
  border-radius:14px;
  padding:12px 14px;
  color:#f5f7fb !important;
  text-decoration:none;
  line-height:1.45;
  margin-bottom:10px;
}
.news-item:hover{background: rgba(26,46,76,.98);}
.news-title{font-size:1rem; font-weight:800; color:#f8fbff;}
.news-meta{display:flex; justify-content:space-between; gap:10px; margin-top:5px; font-size:.83rem; color:var(--muted);}
.link-box{
  margin-top:0;
  padding:20px 18px 16px 18px;
  border:1px solid rgba(89,115,156,.30);
  border-radius:18px;
  background: linear-gradient(180deg, rgba(12,24,42,.92) 0%, rgba(18,30,49,.92) 100%);
}
.link-grid{
  display:grid;
  grid-template-columns:repeat(4, minmax(0,1fr));
  gap:10px 14px;
}
.link-grid a{
  display:block;
  color:#eaf1fb !important;
  text-decoration:none;
  background:rgba(20,38,64,.45);
  border:1px solid rgba(74,101,141,.26);
  border-radius:12px;
  padding:10px 12px;
  font-size:.93rem;
  line-height:1.35;
}
.link-grid a:hover{background:rgba(28,48,80,.82);}
.guide-box{
  margin-top:0;
  padding:20px 18px 16px 18px;
  border:1px solid rgba(89,115,156,.30);
  border-radius:18px;
  background: linear-gradient(180deg, rgba(12,24,42,.92) 0%, rgba(18,30,49,.92) 100%);
}
.guide-text{color:#d7e2f1; line-height:1.85; font-size:.98rem;}
.footer{
  margin-top:28px;
  padding-top:16px;
  border-top:1px solid rgba(90,110,139,.25);
  color:#8ea0ba;
  text-align:center;
  line-height:1.9;
  font-size:.92rem;
}
.footer a{color:#9cc8ff !important; text-decoration:none;}

.soft-divider{margin:1.1rem 0 1.6rem 0; border-top:1px solid rgba(130,160,205,.18);} 
.section-gap-top{margin-top:1.9rem;} 
.section-gap-mid{margin-top:1.55rem;} 
.weather-wrap{margin-bottom:.6rem;} 
.insight-intro{margin-bottom:.4rem;} 
.stButton > button{
  border-radius:12px !important;
  font-weight:800 !important;
  color:#0b1220 !important;
  background:#eef3fb !important;
  border:1px solid #c8d4e6 !important;
}
.stButton > button:hover{
  color:#0b1220 !important;
  background:#f7f9fd !important;
  border:1px solid #b8c8dc !important;
}
.stButton > button p, .stButton > button span, .stButton > button div{color:#0b1220 !important;}
@media (max-width: 1100px){
  .link-grid{grid-template-columns:repeat(2, minmax(0,1fr));}
  .news-divider{display:none;}
}
@media (max-width: 900px){
  .block-container{padding-left:14px !important; padding-right:14px !important;}
  .main-title{font-size:2.6rem;}
  .main-sub{font-size:1rem;}
  .link-grid{grid-template-columns:repeat(1, minmax(0,1fr));}
}
</style>
""",
    unsafe_allow_html=True,
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def smart_date(entry):
    for attr in ["published_parsed", "updated_parsed"]:
        value = getattr(entry, attr, None)
        if value:
            try:
                return datetime(*value[:6]).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
    for attr in ["published", "updated"]:
        value = getattr(entry, attr, None)
        if value:
            return str(value)[:16]
    return ""


def dedupe_items(items):
    seen = set()
    out = []
    for item in items:
        key = (item.get("title", "").strip(), item.get("link", "").strip())
        if not key[0] or not key[1] or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def is_valid_article_url(href: str) -> bool:
    if not href:
        return False
    href = href.strip()
    if href.startswith("javascript:") or href.startswith("#"):
        return False
    return href.startswith("http://") or href.startswith("https://") or href.startswith("/")


def looks_like_article_title(title: str) -> bool:
    title = normalize_text(title)
    if len(title) < 10:
        return False
    bad = ["로그인", "회원가입", "전체보기", "더보기", "구독", "제보", "이전", "다음", "광고문의"]
    return not any(b in title for b in bad)


@st.cache_data(ttl=1800)
def fetch_rss_items(source_name, url, category_tag=None, max_items=10):
    items = []
    try:
        parsed = feedparser.parse(url)
        for ent in parsed.entries[:max_items]:
            title = normalize_text(getattr(ent, "title", ""))
            link = normalize_text(getattr(ent, "link", ""))
            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "source": source_name,
                    "date": smart_date(ent),
                    "category": category_tag or "",
                })
    except Exception:
        return []
    return items


@st.cache_data(ttl=1800)
def fetch_html_list_items(source_name, url, base_url=None, category_tag=None, include_keywords=None, max_items=10):
    include_keywords = include_keywords or []
    base_url = base_url or url
    found = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()
            title = normalize_text(a.get_text(" ", strip=True))
            if not is_valid_article_url(href) or not looks_like_article_title(title):
                continue
            full = urljoin(base_url, href)
            if include_keywords:
                low = title.lower()
                if not any(k.lower() in low for k in include_keywords):
                    continue
            found.append({
                "title": title,
                "link": full,
                "source": source_name,
                "date": "실시간 수집",
                "category": category_tag or "",
            })
            if len(found) >= max_items:
                break
    except Exception:
        return []
    return found


FASHION_IT_SOURCES = [
    {"type": "html", "name": "한국패션뉴스", "url": "https://www.kfashionnews.com/", "keywords": ["패션", "유통", "브랜드", "트렌드", "소비", "온라인", "커머스", "마케팅"]},
    {"type": "html", "name": "패션엔", "url": "https://www.fashionn.com/board/list_new.php?table=1004", "keywords": ["패션", "브랜드", "트렌드", "유통", "마케팅"]},
    {"type": "html", "name": "패션비즈", "url": "https://fashionbiz.co.kr/", "keywords": ["패션", "브랜드", "유통", "소비", "트렌드"]},
    {"type": "html", "name": "한국섬유신문", "url": "http://www.ktnews.com/", "keywords": ["패션", "섬유", "유통", "브랜드", "트렌드"]},
    {"type": "html", "name": "소비자경제", "url": "https://www.consumernews.co.kr/news/articleList.html?sc_multi_code=S3&view_type=sm", "keywords": ["소비", "유통", "온라인", "플랫폼", "커머스", "마케팅", "트렌드"]},
    {"type": "rss", "name": "전자신문", "url": "https://www.etnews.com/rss/section/0300.xml", "category": "IT"},
    {"type": "html", "name": "블로터", "url": "https://www.bloter.net/", "keywords": ["IT", "AI", "플랫폼", "커머스", "마케팅", "디지털"]},
    {"type": "html", "name": "지디넷코리아", "url": "https://zdnet.co.kr/", "keywords": ["IT", "AI", "플랫폼", "디지털", "커머스"]},
    {"type": "html", "name": "AI타임즈", "url": "https://www.aitimes.com/", "keywords": ["AI", "IT", "플랫폼", "마케팅"]},
    {"type": "html", "name": "디지털투데이", "url": "https://www.digitaltoday.co.kr/", "keywords": ["IT", "AI", "플랫폼", "온라인", "커머스"]},
]

ECONOMY_SOURCES = [
    {"type": "html", "name": "정책브리핑", "url": "https://www.korea.kr/news/policyNewsList.do", "keywords": ["경제", "소비", "유통", "물가", "수출", "중소기업"]},
    {"type": "html", "name": "머니투데이", "url": "https://news.mt.co.kr/", "keywords": ["경제", "금리", "증시", "물가", "환율"]},
    {"type": "html", "name": "비즈니스포스트", "url": "https://www.businesspost.co.kr/", "keywords": ["경제", "증시", "금리", "산업"]},
    {"type": "html", "name": "서울파이낸스", "url": "https://www.seoulfn.com/", "keywords": ["경제", "금융", "증시", "물가", "환율"]},
    {"type": "html", "name": "파이낸셜뉴스", "url": "https://www.fnnews.com/", "keywords": ["경제", "금융", "주식", "환율", "부동산"]},
    {"type": "html", "name": "헤럴드경제", "url": "https://biz.heraldcorp.com/", "keywords": ["경제", "금융", "산업", "소비"]},
    {"type": "rss", "name": "한겨레", "url": "https://www.hani.co.kr/rss/economy/", "category": "경제"},
    {"type": "rss", "name": "경향신문", "url": "https://www.khan.co.kr/rss/rssdata/economy_news.xml", "category": "경제"},
    {"type": "rss", "name": "매일경제", "url": "https://www.mk.co.kr/rss/30100041/", "category": "경제"},
    {"type": "html", "name": "한국일보", "url": "https://www.hankookilbo.com/", "keywords": ["경제", "산업", "물가", "소비"]},
]


def collect_news(source_configs, overall_limit=50):
    items = []
    for cfg in source_configs:
        if cfg["type"] == "rss":
            items.extend(fetch_rss_items(cfg["name"], cfg["url"], cfg.get("category"), max_items=8))
        else:
            items.extend(fetch_html_list_items(cfg["name"], cfg["url"], cfg.get("base_url"), cfg.get("category"), cfg.get("keywords", []), max_items=8))
    return dedupe_items(items)[:overall_limit]


@st.cache_data(ttl=1800)
def get_fashion_news():
    return collect_news(FASHION_IT_SOURCES, overall_limit=50)


@st.cache_data(ttl=1800)
def get_economy_news():
    return collect_news(ECONOMY_SOURCES, overall_limit=50)


@st.cache_data(ttl=1800)
def get_seoul_weather():
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780"
        "&current=temperature_2m,weather_code,is_day,apparent_temperature,precipitation,cloud_cover"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=Asia%2FSeoul&forecast_days=1"
    )
    air_url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=37.5665&longitude=126.9780"
        "&current=pm10,pm2_5,us_aqi&timezone=Asia%2FSeoul"
    )
    weather = {}
    air = {}
    try:
        weather = requests.get(weather_url, headers=HEADERS, timeout=12).json()
    except Exception:
        pass
    try:
        air = requests.get(air_url, headers=HEADERS, timeout=12).json()
    except Exception:
        pass
    code_map = {0: "맑음", 1: "대체로 맑음", 2: "부분적으로 흐림", 3: "흐림", 45: "안개", 48: "안개", 51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비", 61: "약한 비", 63: "비", 65: "강한 비", 71: "약한 눈", 73: "눈", 75: "강한 눈", 80: "소나기", 81: "강한 소나기", 82: "매우 강한 소나기", 95: "뇌우"}
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}
    air_current = air.get("current", {}) if isinstance(air, dict) else {}
    aqi = air_current.get("us_aqi")
    if aqi is None:
        air_text = "공기지수 정보 없음"
    elif aqi <= 50:
        air_text = f"공기지수 좋음 ({int(aqi)})"
    elif aqi <= 100:
        air_text = f"공기지수 보통 ({int(aqi)})"
    elif aqi <= 150:
        air_text = f"공기지수 민감군 주의 ({int(aqi)})"
    else:
        air_text = f"공기지수 나쁨 ({int(aqi)})"
    return {
        "temp": current.get("temperature_2m"),
        "feel": current.get("apparent_temperature"),
        "code_text": code_map.get(current.get("weather_code"), "날씨 정보 확인 중"),
        "rain_prob": (daily.get("precipitation_probability_max") or [None])[0],
        "min": (daily.get("temperature_2m_min") or [None])[0],
        "max": (daily.get("temperature_2m_max") or [None])[0],
        "air": air_text,
    }


def fmt_temp(v):
    try:
        return f"{float(v):.1f}°C"
    except Exception:
        return "-"


RELATED_LINKS = [
    ("정책브리핑", "https://www.korea.kr/"),
    ("기업마당", "https://www.bizinfo.go.kr/"),
    ("중소벤처24", "https://www.smes.go.kr/"),
    ("정책지원조회", "https://mybiz.pay.naver.com/subvention/search/"),
    ("한국패션협회", "http://www.koreafashion.org/"),
    ("한국패션뉴스", "https://www.kfashionnews.com/"),
    ("패션엔", "https://www.fashionn.com/"),
    ("패션비즈", "https://fashionbiz.co.kr/"),
    ("한국섬유신문", "http://www.ktnews.com/"),
    ("소비자경제", "https://www.consumernews.co.kr/news/articleList.html?sc_multi_code=S3&view_type=sm"),
    ("통계청", "https://kostat.go.kr/"),
    ("중소벤처기업부", "https://www.mss.go.kr/"),
    ("창조경제혁신센터", "https://ccei.creativekorea.or.kr/"),
    ("DASH", "https://startup.daegu.go.kr/"),
    ("창업진흥원", "https://www.kised.or.kr/index.es?sid=a1"),
    ("스타트업지원센터", "https://www.k-startup.go.kr/onestop"),
    ("시동위키", "https://www.youtube.com/channel/UCdwlSE2aW2VCCQIS5aJwTsA"),
    ("삼프로TV", "https://www.youtube.com/@3protv"),
    ("김작가TV", "https://www.youtube.com/@lucky_tv"),
    ("머니포차", "https://www.youtube.com/@mssbiz"),
]


def build_news_digest(items, section_name):
    lines = []
    for item in items[:12]:
        lines.append(f"- [{item['source']}] {item['title']}")
    return f"{section_name}\n" + "\n".join(lines)


@st.cache_data(ttl=1800, show_spinner=False)
def generate_misharp_insight(fashion_items, economy_items):
    api_key = ""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        return "OPENAI_API_KEY가 설정되지 않아 AI 인사이트를 생성할 수 없습니다."
    if OpenAI is None:
        return "openai 패키지가 설치되지 않아 AI 인사이트를 생성할 수 없습니다."
    prompt = f"""
당신은 4050 여성 타깃 여성의류 브랜드 미샵(MISHARP)의 실무형 MD이자 마케팅 전략가입니다.
아래 오늘의 뉴스 브리핑을 바탕으로, 오늘 미샵에 실제로 도움이 되는 인사이트를 한국어로 작성하세요.

반드시 아래 형식으로 작성하세요.
1. 오늘 체크할 시장 흐름 3가지
2. 미샵에 바로 적용할 상품/콘텐츠/광고 아이디어 3가지
3. 오늘의 한줄 실행 제안

조건:
- 추상적인 말 말고 실무형으로 작성
- 4050 여성 패션몰 관점 반영
- 온라인 쇼핑몰, 콘텐츠, 광고, 재고, 가격, 프로모션 관점 포함
- 각 항목은 짧고 명확하게 작성

[패션·IT·유통·온라인마케팅 뉴스]
{build_news_digest(fashion_items, '패션/IT/유통/온라인마케팅 뉴스')}

[경제 뉴스]
{build_news_digest(economy_items, '경제 뉴스')}
"""
    try:
        client = OpenAI(api_key=api_key)
        res = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return (res.output_text or "인사이트 생성 결과가 비어 있습니다.").strip()
    except Exception as e:
        return f"AI 인사이트 생성 중 오류가 발생했습니다: {e}"


def render_news_section(items, title, state_prefix):
    limit_key = f"{state_prefix}_limit"
    if limit_key not in st.session_state:
        st.session_state[limit_key] = 10
    visible = items[: st.session_state[limit_key]]
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if visible:
        for item in visible:
            date_text = item.get("date") or "실시간 수집"
            st.markdown(
                f"""
                <a class="news-item" href="{html.escape(item['link'])}" target="_blank">
                    <div class="news-title">{html.escape(item['title'])}</div>
                    <div class="news-meta"><span>{html.escape(item['source'])}</span><span>{html.escape(date_text)}</span></div>
                </a>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
    b1, b2 = st.columns(2)
    with b1:
        if st.session_state[limit_key] < min(50, len(items)):
            if st.button("기사 더보기", key=f"{state_prefix}_more", use_container_width=True):
                st.session_state[limit_key] = min(50, st.session_state[limit_key] + 10)
                st.rerun()
    with b2:
        if st.session_state[limit_key] > 10:
            if st.button("접기", key=f"{state_prefix}_collapse", use_container_width=True):
                st.session_state[limit_key] = 10
                st.rerun()


def render_related_links():
    html_block = '<div class="link-box"><div class="section-title" style="margin-top:0;">관련 정보 사이트</div><div class="link-grid">'
    html_block += ''.join([f'<a href="{html.escape(url)}" target="_blank">{html.escape(name)}</a>' for name, url in RELATED_LINKS])
    html_block += '</div></div>'
    st.markdown(html_block, unsafe_allow_html=True)


def render_guide():
    st.markdown('<div class="guide-box"><div class="section-title" style="margin-top:0;">미샵 뉴스 포스트 안내</div>', unsafe_allow_html=True)
    st.markdown('<div class="guide-text">이 페이지는 패션, 유통, 소비, IT, 온라인마케팅, 경제 흐름을 한 화면에서 빠르게 파악하려는 관련 업계 실무자들을 위한 뉴스·정보 브리핑 페이지입니다. 브랜드 운영자, 쇼핑몰 실무자, 마케터, MD, 콘텐츠 기획자, 창업 준비자까지 폭넓게 참고할 수 있도록 구성했습니다.</div>', unsafe_allow_html=True)
    if st.button("안내 내용 펼치기", key="show_guide_btn"):
        st.session_state["show_guide"] = not st.session_state.get("show_guide", False)
    if st.session_state.get("show_guide", False):
        st.markdown(
            """
            <div class="guide-text" style="margin-top:14px; white-space:pre-wrap;">
<b>1. 이 페이지에서 확인하는 정보</b>
서울 기준 실시간 시간과 날씨, 공기지수, 패션·유통·IT·온라인마케팅 뉴스, 주요 경제뉴스, 관련 기관·전문매체 링크, 그리고 기사 흐름을 바탕으로 정리하는 버튼형 인사이트까지 한 번에 볼 수 있습니다.

<b>2. 누가 활용하면 좋은가</b>
패션 브랜드 운영자, 온라인 쇼핑몰 대표, 유통 실무자, 마케터, 콘텐츠 기획자, 창업 준비자, 정책지원사업을 찾는 소상공인과 스타트업 실무자에게 특히 유용합니다. 업계 흐름을 한 번에 살피고, 당일 업무 우선순위를 정하는 데 도움을 줍니다.

<b>3. 인사이트는 어떻게 활용하나</b>
인사이트 버튼은 당일 수집된 기사 흐름을 바탕으로 상품기획, 콘텐츠 주제, 광고 방향, 프로모션 포인트, 고객 커뮤니케이션 아이디어를 빠르게 정리하는 용도로 활용할 수 있습니다. 아침 회의 전 체크리스트로 쓰거나, 카드뉴스·릴스·블로그 주제를 뽑는 출발점으로 사용해도 좋습니다.

<b>4. 실무 활용 예시</b>
소비심리와 유통 뉴스가 약세면 가격 메시지와 혜택 문구를 보수적으로 조정하고, 패션 트렌드와 플랫폼 이슈가 강하면 신상품 노출, 코디 제안, 콘텐츠 업로드 순서를 앞당기는 방식으로 연결할 수 있습니다. 정책·지원 링크는 지원사업 탐색, 정부 공지 확인, 창업·운영 관련 참고 자료 확인용으로 활용할 수 있습니다.

<b>5. 참고 안내</b>
기사와 관련 사이트는 외부 페이지로 연결되며, 뉴스 수집 결과는 각 매체의 공개 영역과 응답 상태에 따라 달라질 수 있습니다. 인사이트 내용은 참고용 자료이며, 최종 사업 판단과 실행은 사용자의 기준에 맞춰 결정해 주세요.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


page = st.query_params.get("page", "home")
if page == "policy":
    st.markdown('<div class="main-title" style="font-size:2.4rem;">개인정보처리방침 · 서비스약관</div>', unsafe_allow_html=True)
    st.markdown('<div class="title-line"></div>', unsafe_allow_html=True)
    st.markdown(POLICY_HTML, unsafe_allow_html=True)
    st.markdown('<div class="footer"><a href="?page=home">메인으로 돌아가기</a></div>', unsafe_allow_html=True)
    st.stop()

kst = datetime.now(pytz.timezone("Asia/Seoul"))
weather = get_seoul_weather()
fashion_news = get_fashion_news()
economy_news = get_economy_news()

st.markdown('<div class="main-title">MISHARP NEWS POST</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">패션/IT/소비유통/경제기사 뉴스/정보 브리핑</div>', unsafe_allow_html=True)

w1, w2 = st.columns([1.2, 1.2])
with w1:
    st.markdown(
        f'<div class="info-box weather-wrap">한국시간 · 서울 · {kst.strftime("%Y-%m-%d (%a) %H:%M:%S")}<br>'
        f'현재 {fmt_temp(weather.get("temp"))} / 체감 {fmt_temp(weather.get("feel"))} / {weather.get("code_text", "날씨 정보 확인 중")}</div>',
        unsafe_allow_html=True,
    )
with w2:
    rain = weather.get("rain_prob")
    rain_text = f'강수확률 {int(rain)}%' if rain is not None else '강수확률 정보 없음'
    st.markdown(
        f'<div class="info-box weather-wrap">서울 실시간 날씨 · 최저 {fmt_temp(weather.get("min"))} / 최고 {fmt_temp(weather.get("max"))}<br>'
        f'{rain_text} · {weather.get("air", "공기지수 정보 없음")}</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title" style="margin-top:0;">미샵을 위한 오늘의 인사이트</div>', unsafe_allow_html=True)
st.markdown('<div class="guide-text insight-intro">오늘 수집된 패션·소비유통·IT·경제 뉴스를 바탕으로, 4050 여성 패션 브랜드 미샵에 도움이 될 만한 상품기획·콘텐츠·광고 실행 아이디어를 버튼 클릭으로 생성합니다.</div>', unsafe_allow_html=True)
if st.button("오늘의 인사이트 생성", key="generate_misharp_insight", use_container_width=False):
    with st.spinner("기사 흐름을 분석해 미샵 인사이트를 생성하는 중입니다..."):
        st.session_state["misharp_insight_text"] = generate_misharp_insight(fashion_news, economy_news)
if st.session_state.get("misharp_insight_text"):
    st.markdown(f'<div class="guide-box"><div class="guide-text" style="white-space:pre-wrap;">{html.escape(st.session_state["misharp_insight_text"])}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-gap-mid"></div>', unsafe_allow_html=True)

left_col, mid_col, right_col = st.columns([1, 0.03, 1])
with left_col:
    render_news_section(fashion_news, "오늘의 패션, 온라인마케팅, 유통, IT 뉴스", "fashion_news")
with mid_col:
    st.markdown('<div class="news-divider"></div>', unsafe_allow_html=True)
with right_col:
    render_news_section(economy_news, "오늘 주요 경제뉴스", "economy_news")

st.markdown('<div class="soft-divider section-gap-top"></div>', unsafe_allow_html=True)
render_related_links()

st.markdown('<div class="soft-divider section-gap-top"></div>', unsafe_allow_html=True)
render_guide()

st.markdown(
    '<div class="footer">2026 MISHARP COMPANY by MIYAWA<br>무단 게재, 복제, 전재를 금합니다.<br>'
    '<a href="?page=policy">개인정보처리방침 · 서비스약관</a></div>',
    unsafe_allow_html=True,
)
