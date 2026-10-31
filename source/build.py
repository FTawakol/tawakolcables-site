#!/usr/bin/env python3
"""Build the Altawakol Cables static site from conductors.csv into dist/."""
import csv, json, os, shutil, math, datetime, sys
from jinja2 import Environment, FileSystemLoader
sys.path.insert(0, os.path.dirname(__file__))
from i18n import STR, FAMILY, TYPE_TESTS, TYPE_TESTS_AR, STANDARDS, WIRE_TESTS, COND_TESTS

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, 'dist')
SITE_URL = os.environ.get('SITE_URL', 'https://altawakolcables.com')
ROOT = os.environ.get('SITE_ROOT', '')          # '' when the site lives at the domain root
MAIL = os.environ.get('RFQ_MAIL', 'sales@altawakolcables.com')
FORM_ENDPOINT = os.environ.get('FORM_ENDPOINT', '')   # e.g. https://formspree.io/f/xxxx ; empty = mailto fallback
TARGET = os.environ.get('TARGET', 'cpanel')            # 'cpanel' or 'pages'
BUILD = datetime.datetime.now().strftime('%Y%m%d%H%M')
BUILD_DATE = datetime.date.today().strftime('%d %b %Y')

# ---------- data ----------
def load_rows():
    rows = []
    with open(os.path.join(HERE, 'conductors.csv'), newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            r = dict(r)
            for k in ('area_al_mm2','area_steel_mm2','total_area_mm2','overall_diameter_mm','mass_kg_km','dc_resistance_20C_ohm_km','rts_kN','current_rating_A'):
                r[k] = r[k].strip()
            r['designation'] = r['designation'] or ''
            r['designation_or_area'] = r['designation'] or (r['area_al_mm2'] + ' mm²')
            r['series_label'] = 'Metric series' if r['series']=='Metric' else 'BS EN 50182'
            r['series_label_ar'] = 'السلسلة المترية' if r['series']=='Metric' else 'أسماء كودية BS EN 50182'
            rows.append(r)
    return rows

def num(x):
    try: return float(x)
    except: return None

# ---------- cross-section geometry ----------
ACSR_LAYERS = {(6,1):[6], (26,7):[10,16], (30,7):[12,18], (54,7):[12,18,24], (12,7):[12], (18,1):[6,12]}
def parse_str(s):
    n, d = s.lower().replace('×','x').split('x'); return int(n), float(d)

def wires(r):
    """Return list of (x, y, radius, kind) in mm, centred at 0,0."""
    out = []
    na, da = parse_str(r['stranding_al'])
    if r['family'] == 'ACSR':
        ns, ds = parse_str(r['stranding_steel'])
        if ns == 1:
            out.append((0,0,ds/2,'st')); core_r = ds/2
        else:
            out.append((0,0,ds/2,'st'))
            for i in range(6):
                a = i*math.pi/3; out.append((ds*math.cos(a), ds*math.sin(a), ds/2, 'st'))
            core_r = 1.5*ds
        layers = ACSR_LAYERS.get((na,ns)) or [na]
        R = core_r + da/2
        for cnt in layers:
            for i in range(cnt):
                a = 2*math.pi*i/cnt + (math.pi/cnt); out.append((R*math.cos(a), R*math.sin(a), da/2, 'al'))
            R += da
    else:
        out.append((0,0,da/2,'al')); left = na-1; k = 1
        while left > 0:
            cnt = min(6*k, left); R = k*da
            for i in range(cnt):
                a = 2*math.pi*i/cnt; out.append((R*math.cos(a), R*math.sin(a), da/2, 'al'))
            left -= cnt; k += 1
    return out

def section_svg(r, size=220):
    ws = wires(r); od = num(r['overall_diameter_mm']) or 2*max(math.hypot(x,y)+rad for x,y,rad,_ in ws)
    sc = (size-20)/od; c = size/2
    parts = [f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" aria-label="Cross-section {r["product_code"]}">',
             f'<circle cx="{c}" cy="{c}" r="{od*sc/2+3}" fill="none" stroke="#B9C7E2" stroke-dasharray="4 4"/>']
    for x,y,rad,kind in ws:
        fill = '#6B7585' if kind=='st' else '#E9EEF6'
        parts.append(f'<circle cx="{c+x*sc:.1f}" cy="{c+y*sc:.1f}" r="{rad*sc:.1f}" fill="{fill}" stroke="#24356E" stroke-width="1"/>')
    parts.append('</svg>'); return ''.join(parts)

def exploded_svg():
    """ACSR 380/50 shown as four concentric rings pulled apart: steel core, then 12, 18, 24 aluminium."""
    d=3.0; rings=[(7,'st'),(12,'al'),(18,'al'),(24,'al')]; out=['<svg viewBox="0 0 560 560" role="img" aria-label="ACSR 380/50 layers: steel core, 12, 18 and 24 aluminium wires">']
    cx,cy=280,270; sc=8.6
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{13.5*sc+6}" fill="none" stroke="#B9C7E2" stroke-dasharray="5 5"/>')
    labels=[('Steel core · 7 × 3.00 mm',0),('12 × 3.00 mm Al',2),('18 × 3.00 mm Al',3),('24 × 3.00 mm Al',4)]
    for li,(n,kind) in enumerate(rings):
        if li==0:
            pts=[(0,0)]+[(d*math.cos(i*math.pi/3), d*math.sin(i*math.pi/3)) for i in range(6)]
        else:
            R=(li+1)*d; pts=[(R*math.cos(2*math.pi*i/n+math.pi/n), R*math.sin(2*math.pi*i/n+math.pi/n)) for i in range(n)]
        fill='#6B7585' if kind=='st' else '#E9EEF6'
        for x,y in pts:
            out.append(f'<circle cx="{cx+x*sc:.1f}" cy="{cy+y*sc:.1f}" r="{d/2*sc-0.6:.1f}" fill="{fill}" stroke="#24356E" stroke-width="1.2"/>')
    # callouts
    def anchor(R, ang): return (cx+R*sc*math.cos(ang), cy+R*sc*math.sin(ang))
    calls=[(anchor(d, -math.pi/2), 'Steel core · 7 × 3.00 mm ST1A', 'middle', cx, 52),
           (anchor(2*d, -math.pi/4), '12 × 3.00 mm AL1', 'end', cx+270, cy-190),
           (anchor(3*d, math.pi*0.8), '18 × 3.00 mm AL1', 'start', 20, cy+205),
           (anchor(4*d, math.pi/4), '24 × 3.00 mm AL1 · outer layer', 'end', cx+200, cy+215)]
    for (x,y),txt,anc,tx,ty in calls:
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{tx}" y2="{ty-5}" stroke="#1A8FE2" stroke-width="1.2"/><circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" fill="#1A8FE2"/>')
        out.append(f'<text x="{tx}" y="{ty}" text-anchor="{anc}" font-family="Inter,system-ui,sans-serif" font-size="13" font-weight="600" fill="#24356E">{txt}</text>')
    out.append(f'<text x="{cx}" y="{cy+13.5*sc+34}" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="12" fill="#5B6478">Ø 27.0 mm · 1443 kg/km · RTS 121.3 kN · 820 A</text>')
    out.append('</svg>'); return ''.join(out)

PHOTOS = json.load(open(os.path.join(HERE,'photos.json'))) if os.path.exists(os.path.join(HERE,'photos.json')) else {}

# ---------- datasheet PDF ----------
def make_datasheet(r, path, lang_rows):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    W, H = A4; cv = canvas.Canvas(path, pagesize=A4); navy = HexColor('#24356E'); blue = HexColor('#1A8FE2'); grey = HexColor('#5B6478')
    cv.setFillColor(navy); cv.rect(0, H-90, W, 90, stroke=0, fill=1)
    cv.drawImage(os.path.join(HERE,'static','img','logo_gold.png'), 40, H-70, width=170, height=30, mask='auto')
    cv.setFillColor(HexColor('#ffffff')); cv.setFont('Helvetica-Bold', 16); cv.drawRightString(W-40, H-50, 'Overhead conductor datasheet')
    cv.setFont('Helvetica', 9); cv.drawRightString(W-40, H-66, f'{r["product_code"]}  ·  issued {BUILD_DATE}')
    title = f'{r["family"]} {r["code_name"] + " · " if r["code_name"] else ""}{r["designation_or_area"]}'
    cv.setFillColor(navy); cv.setFont('Helvetica-Bold', 22); cv.drawString(40, H-130, title)
    cv.setFillColor(grey); cv.setFont('Helvetica', 10); cv.drawString(40, H-148, f'{FAMILY[r["family"]]["en"]["full"]}  ·  {r["series_label"]}  ·  {r["standards"].replace(";", " ·")}')
    # spec table
    y = H-185; cv.setFont('Helvetica', 10.5)
    for label, val in lang_rows:
        cv.setFillColor(grey); cv.drawString(40, y, label); cv.setFillColor(navy); cv.setFont('Helvetica-Bold', 10.5); cv.drawRightString(330, y, val); cv.setFont('Helvetica', 10.5)
        cv.setStrokeColor(HexColor('#D4DEEB')); cv.line(40, y-5, 330, y-5); y -= 20
    # cross-section
    ws = wires(r); od = num(r['overall_diameter_mm']); sc = 150/od; cx, cy = 450, H-290
    cv.setStrokeColor(HexColor('#B9C7E2')); cv.setDash(3,3); cv.circle(cx, cy, od*sc/2+3, stroke=1, fill=0); cv.setDash()
    for x,yy,rad,kind in ws:
        cv.setFillColor(HexColor('#6B7585') if kind=='st' else HexColor('#E9EEF6')); cv.setStrokeColor(navy); cv.circle(cx+x*sc, cy-yy*sc, rad*sc, stroke=1, fill=1)
    cv.setFillColor(grey); cv.setFont('Helvetica', 9); cv.drawCentredString(cx, cy-105, f'{r["stranding_al"].replace("x"," × ")} mm Al' + (f'  /  {r["stranding_steel"].replace("x"," × ")} mm St' if r['stranding_steel'] else '') + f'  ·  Ø {r["overall_diameter_mm"]} mm')
    if r['type_test']:
        cv.setFillColor(HexColor('#E8F6EE')); cv.roundRect(360, cy-180, 195, 54, 6, stroke=0, fill=1); cv.setFillColor(HexColor('#145C33')); cv.setFont('Helvetica-Bold', 9.5)
        cv.drawString(372, cy-146, 'Type-tested: EHVRC report 568/2026'); cv.setFont('Helvetica', 9); cv.drawString(372, cy-160, '17 of 17 type tests passed, 29 Sep 2026'); cv.drawString(372, cy-172, 'IEC 61089 · BS EN 50182 · EDMS 04-100-1')
    # notes
    y = min(y, cy-200) - 10; cv.setFillColor(grey); cv.setFont('Helvetica', 8.5)
    for line in ['Values are nominal unless stated; mass is approximate. Current rating per IEEE 738: 50 Hz, ambient 35 °C, conductor 80 °C, wind 0.6 m/s,',
                 'solar 900 W/m², emissivity and absorptivity 0.5, sea level; for guidance only. Supplied on wooden or steel drums; grease to EN 50326 on request.',
                 'Every drum ships with its routine test certificate. Other sizes, standards and product codes on request.']:
        cv.drawString(40, y, line); y -= 12
    cv.setFillColor(navy); cv.rect(0, 0, W, 54, stroke=0, fill=1); cv.setFillColor(HexColor('#C9D6EC')); cv.setFont('Helvetica', 8.5)
    cv.drawString(40, 32, 'Altawakol for Cables · a company of Al Tawakol Group · 01 Mall, Mohamed Naguib Axis, 1st Settlement, New Cairo, Egypt · Hotline 19796')
    cv.drawString(40, 19, f'Live page: {SITE_URL}/products/{r["product_code"].lower()}/   ·   Request a quote: {SITE_URL}/contact/?code={r["product_code"]}')
    cv.showPage(); cv.save()

# ---------- helpers ----------
def write(path, html):
    full = os.path.join(DIST, path.lstrip('/'))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f: f.write(html)

def main():
    rows = load_rows()
    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(HERE,'static'), os.path.join(DIST,'assets'))
    if TARGET=='cpanel': shutil.move(os.path.join(DIST,'assets','rfq.php'), os.path.join(DIST,'rfq.php'))
    else: os.remove(os.path.join(DIST,'assets','rfq.php'))
    os.makedirs(os.path.join(DIST,'data')); os.makedirs(os.path.join(DIST,'datasheets'))
    shutil.copy(os.path.join(HERE,'conductors.csv'), os.path.join(DIST,'data','altawakol-conductors.csv'))
    json_rows = [{k:(num(v) if k in ('area_al_mm2','area_steel_mm2','total_area_mm2','overall_diameter_mm','mass_kg_km','dc_resistance_20C_ohm_km','rts_kN','current_rating_A') else v) for k,v in r.items()} for r in rows]
    with open(os.path.join(DIST,'data','conductors.json'),'w',encoding='utf-8') as f: json.dump(json_rows, f, ensure_ascii=False)
    # pattern, favicon, og
    strands = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900">']
    for cx,cy in [(450+ 95*math.cos(a)*k, 450+95*math.sin(a)*k) for k in range(0,5) for a in [2*math.pi*i/max(1,6*k) for i in range(max(1,6*k))]]:
        strands.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="46" fill="none" stroke="#4988D0" stroke-width="1.5"/>')
    strands.append('</svg>'); open(os.path.join(DIST,'assets','img','strands.svg'),'w').write(''.join(strands))
    open(os.path.join(DIST,'favicon.svg'),'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#24356E"/><path d="M14 20h36l-6 10H22l-4 14h-8z M38 30h10l-6 14H32z" fill="#FDB913"/></svg>')
    try:
        from PIL import Image
        og = Image.new('RGB',(1200,630),(0x24,0x35,0x6E)); logo = Image.open(os.path.join(HERE,'static','img','logo_gold.png')).convert('RGBA'); logo = logo.resize((720, int(720*logo.height/logo.width)))
        og.paste(logo,(240, 230), logo); og.save(os.path.join(DIST,'assets','img','og.png'))
    except Exception as e: print('og skipped', e)

    env = Environment(loader=FileSystemLoader(os.path.join(HERE,'templates')), autoescape=True)
    by_fam = {f:[r for r in rows if r['family']==f] for f in ('ACSR','AAAC','AAC')}
    counts = {f:len(v) for f,v in by_fam.items()}
    sample = {'ACSR': next(r for r in rows if r['product_code']=='ATC-ACS-012'), 'AAAC': next(r for r in rows if r['product_code']=='ATC-AAA-011'), 'AAC': next(r for r in rows if r['product_code']=='ATC-AAC-011')}
    sections = {f: section_svg(sample[f], 120) for f in sample}
    urls = []

    for lang in ('en','ar'):
        T = STR[lang]; t = lambda k: T.get(k, k)
        pre = '/ar' if lang=='ar' else ''
        u = lambda p: ROOT + pre + p
        js_strings = json.dumps({k:T[k] for k in ('showing','of','sel_none','u_mm2','u_a','u_mm','u_kgkm','u_kn','u_nomm','u_ohmkm','specification','hero_cta2','compare_empty','compare_remove','f_sending','f_ok','f_ok2','f_err','f_mailto','filter_series','th_name','th_designation','th_area_al','th_area_st','th_area_total','th_stranding_al','th_stranding_st','th_diameter','th_mass','th_resistance','th_rts','th_current','add_compare')} | {'th_family': 'Family' if lang=='en' else 'العائلة', 'added_compare': 'In compare list' if lang=='en' else 'في قائمة المقارنة'}, ensure_ascii=False)
        fams = {f: FAMILY[f][lang] for f in FAMILY}
        def render(tpl, path, title, section='', desc='', **ctx):
            en_path = path.replace('/ar/','/',1) if lang=='ar' else path
            ar_path = path if lang=='ar' else ('/ar' + path if path != '/' else '/ar/')
            other = ROOT + (ar_path if lang=='en' else en_path)
            html = env.get_template(tpl).render(lang=lang, t=t, u=u, root=ROOT, site_url=SITE_URL, path=ROOT+path, en_path=ROOT+en_path, ar_path=ROOT+ar_path, other_lang_url=other,
                                                title=title, desc=desc, section=section, build=BUILD, build_date=BUILD_DATE, js_strings=js_strings, families=fams, counts=counts, sections=sections, mail=MAIL, form_endpoint=FORM_ENDPOINT, **ctx)
            write(path + ('index.html' if path.endswith('/') else ''), html)
            if lang=='en': urls.append(path)
        home = pre + '/'
        render('home.html', home, t('tagline'), 'home', photos=PHOTOS, exploded_svg=exploded_svg())
        render('products.html', pre + '/products/', t('products_title'), 'products')
        for fam, frows in by_fam.items():
            F = fams[fam]
            render('family.html', pre + f'/products/{fam.lower()}/', f'{F["name"]} {F["full"]}', 'products', f'{F["full"]}: {counts[fam]} sizes, {F["range"]}. {F["desc"][:120]}',
                   fam=fam, F=F, rows=frows, section_svg=section_svg(sample[fam], 200), section_cap=f'{sample[fam]["family"]} {sample[fam]["designation_or_area"]} · {sample[fam]["stranding_al"].replace("x"," × ")}' + (f' / {sample[fam]["stranding_steel"].replace("x"," × ")}' if sample[fam]['stranding_steel'] else ''))
            for i, r in enumerate(frows):
                same = [x for x in frows if x['series']==r['series']]; j = same.index(r); neigh = same[max(0,j-3):j+4]
                main = f'{r["family"]} {r["code_name"] or r["designation_or_area"]}'
                sub = (r['designation_or_area'] if r['code_name'] else '')
                name_en = f'{r["family"]} {r["code_name"] + " " if r["code_name"] else ""}{r["designation_or_area"]}'
                ld = json.dumps({"@context":"https://schema.org","@type":"Product","name":name_en,"sku":r['product_code'],"brand":{"@type":"Brand","name":"Altawakol Cables"},"description":f'{FAMILY[r["family"]]["en"]["full"]}, {r["area_al_mm2"]} mm² aluminium, {r["overall_diameter_mm"]} mm, {r["mass_kg_km"]} kg/km, RTS {r["rts_kN"]} kN, {r["current_rating_A"]} A. {r["standards"]}.',
                                 "additionalProperty":[{"@type":"PropertyValue","name":"Overall diameter","value":r['overall_diameter_mm'],"unitText":"mm"},{"@type":"PropertyValue","name":"Mass","value":r['mass_kg_km'],"unitText":"kg/km"},{"@type":"PropertyValue","name":"Rated tensile strength","value":r['rts_kN'],"unitText":"kN"},{"@type":"PropertyValue","name":"DC resistance at 20 °C","value":r['dc_resistance_20C_ohm_km'],"unitText":"Ω/km"},{"@type":"PropertyValue","name":"Current rating","value":r['current_rating_A'],"unitText":"A"}]}, ensure_ascii=False)
                desc = f'{name_en} ({r["product_code"]}): {r["area_al_mm2"]} mm² Al, {r["stranding_al"].replace("x"," × ")} mm, Ø {r["overall_diameter_mm"]} mm, {r["mass_kg_km"]} kg/km, RTS {r["rts_kN"]} kN, {r["current_rating_A"]} A. {r["standards"]}. Datasheet and quotation.'
                render('code.html', pre + f'/products/{r["product_code"].lower()}/', f'{name_en} conductor, {r["product_code"]}', 'products', desc,
                       r=r, F=F, neighbours=neigh, title_main=main, title_sub=sub, product_ld=ld, section_svg=section_svg(r, 220),
                       section_cap=f'{r["stranding_al"].replace("x"," × ")} mm' + (f' / {r["stranding_steel"].replace("x"," × ")} mm' if r['stranding_steel'] else '') + f' · Ø {r["overall_diameter_mm"]} mm')
        render('selector.html', pre + '/tools/selector/', t('selector_title'), 'selector')
        render('compare.html', pre + '/tools/compare/', t('compare_title'), 'compare')
        render('documents.html', pre + '/documents/', t('docs_title'), 'documents')
        tests = [(TYPE_TESTS_AR[i] if lang=='ar' else tt[0], tt[1], tt[2], tt[3]) for i, tt in enumerate(TYPE_TESTS)]
        render('quality.html', pre + '/quality/', t('quality_title'), 'quality', standards=STANDARDS, wire_tests=WIRE_TESTS[lang], cond_tests=COND_TESTS[lang], type_tests=tests)
        render('company.html', pre + '/company/', t('company_title'), 'company')
        render('news.html', pre + '/news/', t('news_title'), 'news')
        render('contact.html', pre + '/contact/', t('contact_title'), 'contact', codes=[r['product_code'] for r in rows] + [f'{r["family"]} {r["code_name"]}' for r in rows if r['code_name']] + [f'{r["family"]} {r["designation"]}' for r in rows if r['designation']])
        render('404.html', pre + '/404.html', '404', '')

    # datasheets
    for r in rows:
        spec = [('Product code', r['product_code'])] + ([('Code name', r['code_name'])] if r['code_name'] else []) + [('Designation', r['designation_or_area']), ('Aluminium area', f'{r["area_al_mm2"]} mm²')]
        if r['area_steel_mm2']: spec += [('Steel area', f'{r["area_steel_mm2"]} mm²'), ('Total area', f'{r["total_area_mm2"]} mm²')]
        spec += [('Stranding, aluminium', f'{r["stranding_al"].replace("x"," x ")} mm')]
        if r['stranding_steel']: spec += [('Stranding, steel', f'{r["stranding_steel"].replace("x"," x ")} mm')]
        spec += [('Overall diameter', f'{r["overall_diameter_mm"]} mm'), ('Approx. mass', f'{r["mass_kg_km"]} kg/km'), ('DC resistance at 20 °C', f'{r["dc_resistance_20C_ohm_km"]} Ohm/km'), ('Rated tensile strength', f'{r["rts_kN"]} kN'), ('Current rating', f'{r["current_rating_A"]} A')]
        make_datasheet(r, os.path.join(DIST,'datasheets', f'{r["product_code"]}.pdf'), spec)

    # sitemap, robots, htaccess
    with open(os.path.join(DIST,'sitemap.xml'),'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">')
        for p in urls:
            if p.endswith('404.html'): continue
            ar = '/ar' + p if p != '/' else '/ar/'
            f.write(f'<url><loc>{SITE_URL}{ROOT}{p}</loc><xhtml:link rel="alternate" hreflang="en" href="{SITE_URL}{ROOT}{p}"/><xhtml:link rel="alternate" hreflang="ar" href="{SITE_URL}{ROOT}{ar}"/></url>')
            f.write(f'<url><loc>{SITE_URL}{ROOT}{ar}</loc></url>')
        f.write('</urlset>')
    open(os.path.join(DIST,'robots.txt'),'w').write(f'User-agent: *\nAllow: /\nDisallow: /rfq-log.csv\nSitemap: {SITE_URL}{ROOT}/sitemap.xml\n')
    if TARGET=='pages':
        open(os.path.join(DIST,'CNAME'),'w').write(SITE_URL.replace('https://','').replace('http://','')+'\n'); open(os.path.join(DIST,'.nojekyll'),'w').write('')
    if TARGET=='cpanel': open(os.path.join(DIST,'.htaccess'),'w').write('''# Altawakol Cables
DirectoryIndex index.html
ErrorDocument 404 /404.html
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</IfModule>
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/css "access plus 1 month"
ExpiresByType application/javascript "access plus 1 month"
ExpiresByType image/png "access plus 1 year"
ExpiresByType image/jpeg "access plus 1 year"
ExpiresByType image/svg+xml "access plus 1 year"
ExpiresByType application/pdf "access plus 1 week"
</IfModule>
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
<Files "rfq-log.csv">
Require all denied
</Files>
AddDefaultCharset UTF-8
''')
    print('built', len(rows), 'codes;', len(urls), 'EN pages (+AR)')

if __name__ == '__main__':
    main()
