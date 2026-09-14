"""NextGen Analytics — FINAL Upgraded Analyzer | Triple System: Web + Marketing + Power BI + AI"""

import requests
from bs4 import BeautifulSoup
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False

def normalize_url(url):
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_EMAIL_IGNORE_DOMAINS = ("sentry.io","wixpress.com","example.com","godaddy.com","schema.org","w3.org","gstatic.com","google.com","cloudflare.com")
_EMAIL_IGNORE_EXT = (".png",".jpg",".jpeg",".gif",".svg",".webp")

def _extract_email(soup, html_text):
    # Prefer mailto: links
    for link in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
        candidate = link["href"].split("mailto:",1)[1].split("?")[0].strip()
        if candidate and EMAIL_REGEX.fullmatch(candidate):
            return candidate
    # Fallback regex scan
    for match in EMAIL_REGEX.findall(html_text):
        domain = match.split("@")[-1].lower()
        if match.lower().endswith(_EMAIL_IGNORE_EXT):
            continue
        if any(bad in domain for bad in _EMAIL_IGNORE_DOMAINS):
            continue
        return match
    return None

def detect_opportunity(lead, website_report, lead_type):
    """
    TRIPLE SYSTEM: Detect opportunity based on selected lead_type
    lead_type: all, web, marketing, powerbi, ai
    """
    issues = []
    bonus = 0
    is_hot = False
    opportunity_label = ""

    name = (lead.get("name") or "").lower()
    category = (lead.get("category") or "").lower()
    combined = f"{name} {category}"
    
    try:
        reviews = int(str(lead.get("reviews",0)).replace(",","").strip() or 0)
    except:
        reviews = 0
    try:
        rating = float(str(lead.get("rating",0)).strip() or 0)
    except:
        rating = 0

    # ─── WEB DEV LOGIC ───
    if lead_type in ["web", "all"]:
        if not website_report.get("exists"):
            issues.append("💻 No website at all — Hot Web Dev client")
            bonus += 25
            is_hot = True
            opportunity_label = "WEB"
        elif website_report.get("score",0) >= 60:
            issues.append(f"💻 Bad website ({website_report.get('score')} score) — Needs redesign")
            bonus += 15
            is_hot = True
            if not opportunity_label:
                opportunity_label = "WEB"

    # ─── MARKETING LOGIC ───
    if lead_type in ["marketing", "all"]:
        marketing_threshold = getattr(config, 'MARKETING_LOW_RATING_THRESHOLD', 4.0)
        low_reviews_threshold = getattr(config, 'MARKETING_LOW_REVIEWS_THRESHOLD', 30)
        
        if rating > 0 and rating < marketing_threshold and reviews >= 5:
            issues.append(f"📢 Low rating {rating}★ with {reviews} reviews — Needs reputation marketing")
            bonus += 20
            is_hot = True
            opportunity_label = "MARKETING" if lead_type=="marketing" else (opportunity_label + "+MARKETING" if opportunity_label else "MARKETING")
        if reviews < low_reviews_threshold and reviews >= 3:
            issues.append(f"📢 Only {reviews} reviews — Needs review growth + local SEO")
            bonus += 15
            is_hot = True
            if not opportunity_label:
                opportunity_label = "MARKETING"
        if not website_report.get("has_modern_meta") and website_report.get("exists"):
            issues.append("📢 No OG tags / SEO meta — Marketing opportunity")
            bonus += 5

    # ─── POWER BI / FABRIC LOGIC ───
    if lead_type in ["powerbi", "all"]:
        powerbi_cats = getattr(config, 'POWER_BI_CATEGORIES', [])
        for hot_cat in powerbi_cats:
            if hot_cat in combined:
                issues.append(f"📊 High-data business ({lead.get('category','')}) — Perfect for Power BI / Fabric Dashboard")
                bonus += 20
                is_hot = True
                opportunity_label = "POWER BI" if lead_type=="powerbi" else (opportunity_label + "+POWER BI" if opportunity_label else "POWER BI")
                break
        if reviews >= 100:
            issues.append(f"📊 {reviews}+ reviews but no data system — Needs Power BI for analytics")
            bonus += 25
            is_hot = True
            if not opportunity_label:
                opportunity_label = "POWER BI"
        elif reviews >= 50:
            issues.append(f"📊 {reviews} reviews — Growing, needs automated reporting")
            bonus += 10
            is_hot = True
        if not website_report.get("exists") and reviews >= 20:
            issues.append(f"📊 No website + {reviews} reviews — Needs Web + Power BI combo (high ticket $950+)")
            bonus += 30
            is_hot = True

    # ─── AI & AUTOMATION LOGIC ───
    if lead_type in ["ai", "all"]:
        if reviews >= 80:
            issues.append(f"🤖 {reviews} reviews — High volume, needs AI chatbot & auto replies")
            bonus += 15
            is_hot = True
            if not opportunity_label:
                opportunity_label = "AI"
        if "restaurant" in combined or "clinic" in combined or "hotel" in combined or "salon" in combined:
            issues.append("🤖 Booking-based business — Perfect for AI appointment bot")
            bonus += 10
            is_hot = True

    return is_hot, issues, bonus, opportunity_label

def check_website(url):
    """
    Full website quality analyzer — from old version (more detailed)
    """
    report = {
        "url": url,
        "exists": False,
        "is_responsive": False,
        "has_ssl": False,
        "load_time": None,
        "has_modern_meta": False,
        "tech_signals": [],
        "issues": [],
        "email": None,
        "score": getattr(config, 'SCORE_NO_WEBSITE', 85),
    }

    normalized = normalize_url(url)
    if not normalized:
        report["issues"].append("No website URL provided")
        return report

    report["url"] = normalized

    try:
        resp = requests.get(
            normalized,
            timeout=getattr(config, 'WEBSITE_CHECK_TIMEOUT', 10),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            allow_redirects=True,
        )
        report["load_time"] = resp.elapsed.total_seconds()
    except requests.exceptions.SSLError:
        report["exists"] = True
        report["issues"].append("SSL certificate error")
        report["score"] = getattr(config, 'SCORE_BAD_WEBSITE', 75)
        return report
    except requests.exceptions.ConnectionError:
        report["issues"].append("Website unreachable / domain dead")
        report["score"] = getattr(config, 'SCORE_NO_WEBSITE', 85)
        return report
    except requests.exceptions.Timeout:
        report["exists"] = True
        report["issues"].append("Website extremely slow (timed out)")
        report["score"] = getattr(config, 'SCORE_BAD_WEBSITE', 75)
        return report
    except Exception as e:
        report["issues"].append(f"Error checking website: {e}")
        return report

    report["exists"] = True

    if resp.url.startswith("https://"):
        report["has_ssl"] = True
    else:
        report["issues"].append("No HTTPS / SSL")

    if report["load_time"] and report["load_time"] > 5:
        report["issues"].append(f"Very slow load time: {report['load_time']:.1f}s")

    soup = BeautifulSoup(resp.text, "html.parser")
    html_lower = resp.text.lower()

    report["email"] = _extract_email(soup, resp.text)

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        report["is_responsive"] = True
    else:
        report["issues"].append("No viewport meta tag (not mobile-friendly)")

    og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})
    if og_tags:
        report["has_modern_meta"] = True
        report["tech_signals"].append("Open Graph tags")

    # Tech detection
    if "wordpress" in html_lower or "wp-content" in html_lower:
        report["tech_signals"].append("WordPress")
    if "wix.com" in html_lower:
        report["tech_signals"].append("Wix")
    if "squarespace" in html_lower:
        report["tech_signals"].append("Squarespace")
    if "shopify" in html_lower:
        report["tech_signals"].append("Shopify")
    if "weebly" in html_lower:
        report["tech_signals"].append("Weebly")
    if "godaddy" in html_lower:
        report["tech_signals"].append("GoDaddy Website Builder")
    if "react" in html_lower or "next.js" in html_lower or "__next" in html_lower:
        report["tech_signals"].append("React/Next.js")
    if "angular" in html_lower:
        report["tech_signals"].append("Angular")
    if "vue" in html_lower:
        report["tech_signals"].append("Vue.js")

    # Copyright year
    copyright_match = re.search(r'(?:©|&copy;|copyright)\s*(\d{4})', html_lower)
    if copyright_match:
        year = int(copyright_match.group(1))
        if year < 2023:
            report["issues"].append(f"Copyright year outdated: {year}")

    all_links = soup.find_all("a", href=True)
    all_images = soup.find_all("img")

    if len(all_links) < 3:
        report["issues"].append("Very few links (sparse site)")
    if len(all_images) < 2:
        report["issues"].append("Almost no images")

    broken_imgs = [img for img in all_images if not img.get("src") or img["src"].startswith("data:image/svg")]
    if len(broken_imgs) > 2:
        report["issues"].append("Multiple placeholder/broken images")

    title = soup.find("title")
    if not title or not title.text.strip():
        report["issues"].append("Missing page title")

    desc = soup.find("meta", attrs={"name": "description"})
    if not desc:
        report["issues"].append("Missing meta description")

    # Scoring
    issue_count = len(report["issues"])
    if not report["is_responsive"] and issue_count >= 3:
        report["score"] = getattr(config, 'SCORE_BAD_WEBSITE', 75)
    elif issue_count >= 4:
        report["score"] = getattr(config, 'SCORE_BAD_WEBSITE', 75)
    elif issue_count >= 2:
        report["score"] = getattr(config, 'SCORE_OUTDATED_WEBSITE', 60)
    elif issue_count >= 1:
        report["score"] = getattr(config, 'SCORE_DECENT_WEBSITE', 30)
    else:
        report["score"] = getattr(config, 'SCORE_GOOD_WEBSITE', 10)

    return report

def analyze_leads(leads, lead_type="all", progress_callback=None):
    """
    Main function — supports both old signature (progress_callback only) and new (lead_type + callback)
    """
    # Handle old signature where second arg was progress_callback
    if callable(lead_type) and progress_callback is None:
        progress_callback = lead_type
        lead_type = "all"

    total = len(leads)
    completed = 0
    main_thread_ctx = get_script_run_ctx() if _STREAMLIT_AVAILABLE else None

    def _check_one(lead):
        nonlocal completed
        if main_thread_ctx is not None:
            add_script_run_ctx(threading.current_thread(), main_thread_ctx)

        url = lead.get("website")
        if url:
            report = check_website(url)
        else:
            report = {
                "url": None, "exists": False, "is_responsive": False, "has_ssl": False,
                "load_time": None, "has_modern_meta": False, "tech_signals": [],
                "issues": ["No website at all"], "email": None,
                "score": getattr(config, 'SCORE_NO_WEBSITE', 85),
            }

        is_hot, extra_issues, bonus, label = detect_opportunity(lead, report, lead_type)

        lead["website_report"] = report
        lead["powerbi_opportunity"] = is_hot if lead_type in ["powerbi", "all"] else False
        lead["marketing_opportunity"] = is_hot if lead_type in ["marketing", "all"] else False
        lead["web_opportunity"] = is_hot if lead_type in ["web", "all"] else False
        lead["ai_opportunity"] = is_hot if lead_type in ["ai", "all"] else False
        lead["is_hot_opportunity"] = is_hot
        lead["opportunity_label"] = label or lead_type.upper()
        lead["extra_issues"] = extra_issues
        lead["lead_score"] = min(100, report["score"] + bonus)
        lead["email"] = report.get("email")
        lead["lead_type"] = lead_type

        completed += 1
        if progress_callback:
            progress_callback(completed, total, f"Checked: {lead.get('name', '?')} [{label or 'checked'}]")
        return lead

    max_workers = getattr(config, 'MAX_CONCURRENT_CHECKS', 5)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_check_one, lead): lead for lead in leads}
        for future in as_completed(futures):
            future.result()

    # Sort: hot first, then score
    leads.sort(key=lambda x: (x.get("is_hot_opportunity", False), x.get("lead_score", 0)), reverse=True)
    return leads
