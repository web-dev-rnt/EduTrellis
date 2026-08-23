"""Verified public facts shown on edutrellis.in and /websitecreation.

This context is injected for every model, not learned from chat replies.  Keep
it in sync with the public templates when company copy, prices, or contacts
change; it is intentionally authoritative so a model cannot invent details.
"""
import re


_BRAND_RE = re.compile(r"\b(edutrellis|edutrellis\.in|websitecreation)\b", re.IGNORECASE)
_UNAMBIGUOUS_FOLLOWUP_RE = re.compile(
    r"\b(sales\s*team\s*(?:phone|number|contact)?|your\s+(?:company|services?|"
    r"packages?|prices?|pricing|phone|number|e-?mail|address|office|instagram|"
    r"facebook|linkedin|social\s*(?:media|handles?)|founder|ceo|team)|"
    r"company's\s+(?:phone|number|e-?mail|address|office|social)|"
    r"website\s+creation\s+(?:price|pricing|package|service))\b",
    re.IGNORECASE,
)


def is_company_query(text):
    text = text or ''
    return bool(_BRAND_RE.search(text) or _UNAMBIGUOUS_FOLLOWUP_RE.search(text))


PUBLIC_SITE_CONTEXT = """VERIFIED EDUTRELLIS PUBLIC WEBSITE DATA (authoritative):
Use only these details for EduTrellis company answers. Never invent a phone
number, email, address, price, person, statistic, social handle, or URL. If a
requested detail is absent, say it is not published on the supplied pages.

Company: EduTrellis is a website-development and digital-growth company in
Lucknow, Uttar Pradesh, India. Founded in 2020 by Vijay Tiwari, Founder & CEO.
Rudra Narayan Tiwari leads the Sales and Tech teams and built EduTrellis AI;
he is not the founder. Public founder email: ceo@edutrellis.in. Founder
LinkedIn: https://www.linkedin.com/in/vijaytiwariii/

Official contacts: support@edutrellis.in; call/WhatsApp +91 96959 53183.
Office: P-109, Prembagh, Shahpur, Chinhat, Lucknow, Uttar Pradesh 226028.
Public hours on /websitecreation: Monday-Saturday 9 AM-8 PM; Sunday 10 AM-6 PM.
Instagram: https://www.instagram.com/edutrellis (@edutrellis)
LinkedIn: https://www.linkedin.com/company/edutrellis
Facebook: https://www.facebook.com/profile.php?id=61590850943948

Official pages: https://www.edutrellis.in/ and
https://www.edutrellis.in/websitecreation/. The website-creation page offers a
free quote/consultation. Do not claim that prices are unpublished: the main
public page displays these prices:
- Complete Website Management: ₹2,999/month; includes end-to-end management,
  logo/banner updates, content upload/optimization, Instagram/Facebook/Google
  marketing, social-handle creation/growth, SEO, and a dedicated manager.
- Static Business Website: ₹8,999; single-page site with hero, about,
  products/services, contact form/map, responsive and SEO-ready design, plus
  one month of maintenance.
- Dynamic/E-commerce Website: ₹14,999; catalog/search, admin, Razorpay/PayU/UPI,
  cart/checkout/coupons, customer dashboard/order tracking.
- Custom Big Projects: shown from ₹19,999 (the enquiry form labels it ₹19,999+);
  custom web apps, LMS, multi-vendor/multi-role systems, APIs, analytics,
  project management, training and documentation.
- Complete Manager Package: ₹29,999 for 6 months; custom website, design assets,
  Google Business/Maps and local SEO, social/digital marketing, traffic/SEO,
  and a dedicated manager.
- Logo, Banner & Thumbnail Design: ₹2,999 for 2 months.
- Google Business & Maps Setup: ₹3,499.

Other public services include WordPress customization/maintenance, landing
pages and funnels, custom web applications, redesign/revamp, SEO-ready site
structure, content management, maintenance/support and payment integration.
The pages visually show service/product illustrations, portfolio imagery,
gallery images, and real team portraits. Image captions/topics include website
management, static websites, e-commerce, custom projects, branding, SEO,
digital marketing, mobile-first design and the EduTrellis team. Do not infer
facts about people or projects merely from stock/illustrative images.

Public website claims include 1200+ clients, 500+ projects/sites delivered,
98% satisfaction, 5-star average rating and 24/7 support. /websitecreation also
shows 545+ website-management clients and 200+ e-commerce stores built. State
these as claims displayed by the website, not independently verified facts.
"""
