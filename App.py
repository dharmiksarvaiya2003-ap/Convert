from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Raj Jacquard Designer</title>
  <meta name="description" content="Bespoke Jacquard textile design by Raj."/>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #FAF7F2; --card: #F2EDE4; --primary: #7C2D3E;
      --gold: #B8862A; --fg: #1C1007; --muted: #7A6E65;
      --border: #DDD3C5; --white: #FFFFFF;
    }
    html { scroll-behavior: smooth; }
    body { font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--fg); overflow-x: hidden; }
    h1,h2,h3,h4 { font-family: 'Playfair Display', serif; }

    /* NAV */
    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 50;
      padding: 1.25rem 3rem; display: flex; align-items: center; justify-content: space-between;
      background: rgba(250,247,242,0.93); backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
    }
    .brand { font-family:'Playfair Display',serif; font-size:1.6rem; font-weight:700; color:var(--primary); text-decoration:none; letter-spacing:.1em; }
    .nav-links { display:flex; gap:2rem; list-style:none; }
    .nav-links a { text-decoration:none; font-size:.8rem; font-weight:600; letter-spacing:.12em; color:var(--fg); transition:color .3s; }
    .nav-links a:hover { color:var(--primary); }
    .btn-nav { background:var(--primary); color:#fff; border:none; padding:.7rem 1.6rem; font-family:'Playfair Display',serif; font-size:.85rem; letter-spacing:.1em; cursor:pointer; text-decoration:none; }
    .btn-nav:hover { background:#5e2030; }

    /* HERO */
    #hero { min-height:100vh; display:flex; align-items:center; padding:7rem 3rem 4rem; background:linear-gradient(135deg,var(--bg) 60%,#f0e6d8 100%); }
    .hero-inner { max-width:1200px; margin:0 auto; width:100%; display:grid; grid-template-columns:1fr 1fr; gap:4rem; align-items:center; }
    .hero-label { display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem; }
    .hero-label-line { width:48px; height:1px; background:var(--gold); }
    .hero-label span { color:var(--gold); font-size:.75rem; font-weight:600; letter-spacing:.2em; text-transform:uppercase; }
    .hero-title { font-size:clamp(2.8rem,5vw,4.5rem); line-height:1.1; margin-bottom:1.5rem; }
    .hero-title em { color:var(--primary); font-style:italic; font-weight:400; }
    .hero-sub { font-size:1.1rem; color:var(--muted); line-height:1.8; font-weight:300; max-width:480px; margin-bottom:2.5rem; }
    .hero-btns { display:flex; gap:1.25rem; flex-wrap:wrap; }
    .btn-primary { background:var(--primary); color:#fff; padding:.9rem 2rem; border:none; cursor:pointer; font-family:'Playfair Display',serif; font-size:.95rem; letter-spacing:.08em; text-decoration:none; display:inline-block; transition:background .3s; }
    .btn-primary:hover { background:#5e2030; }
    .btn-outline { background:transparent; color:var(--fg); padding:.9rem 2rem; border:1px solid var(--border); cursor:pointer; font-family:'Playfair Display',serif; font-size:.95rem; letter-spacing:.08em; text-decoration:none; display:inline-block; transition:all .3s; }
    .btn-outline:hover { border-color:var(--primary); color:var(--primary); }
    .hero-img img { width:100%; height:560px; object-fit:cover; border-radius:50% 50% 4px 4px; box-shadow:0 30px 80px rgba(28,16,7,.18); }

    /* SECTIONS */
    section { padding:6rem 3rem; }
    .container { max-width:1200px; margin:0 auto; }
    .sec-heading { font-size:clamp(2rem,3.5vw,3rem); margin-bottom:1rem; }
    .sec-heading em { color:var(--primary); font-style:italic; font-weight:400; }
    .divider { width:64px; height:3px; background:var(--gold); margin:0 auto 3.5rem; }

    /* ABOUT */
    #about { background:var(--card); }
    .about-grid { display:grid; grid-template-columns:5fr 7fr; gap:5rem; align-items:center; }
    .about-img { position:relative; }
    .about-img img { width:100%; aspect-ratio:4/5; object-fit:cover; box-shadow:0 16px 48px rgba(28,16,7,.12); }
    .about-badge { position:absolute; bottom:-2rem; right:-2rem; background:var(--white); padding:2rem; box-shadow:0 8px 32px rgba(28,16,7,.12); border:1px solid var(--border); }
    .about-badge .num { font-family:'Playfair Display',serif; font-size:2.5rem; color:var(--primary); }
    .about-badge .lbl { font-size:.72rem; font-weight:600; letter-spacing:.15em; text-transform:uppercase; color:var(--muted); }
    .about-text p { color:var(--muted); font-weight:300; line-height:1.9; font-size:1.05rem; margin-bottom:1.25rem; }
    .signature { font-family:'Playfair Display',serif; font-style:italic; font-size:1.5rem; color:var(--primary); margin-top:1.5rem; }

    /* SERVICES */
    #services { background:var(--bg); }
    .services-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:2rem; }
    .svc-card { background:var(--card); border:1px solid var(--border); padding:2.5rem; position:relative; overflow:hidden; transition:border-color .3s,box-shadow .3s; }
    .svc-card:hover { border-color:rgba(124,45,62,.3); box-shadow:0 16px 40px rgba(28,16,7,.08); }
    .svc-num { font-family:'Playfair Display',serif; font-size:5rem; color:var(--gold); opacity:.15; position:absolute; top:-1rem; right:-.5rem; line-height:1; transition:opacity .3s; }
    .svc-card:hover .svc-num { opacity:.25; }
    .svc-title { font-size:1.4rem; margin-bottom:1rem; position:relative; z-index:1; }
    .svc-desc { color:var(--muted); font-weight:300; line-height:1.8; position:relative; z-index:1; }
    .svc-arrow { margin-top:1.5rem; padding-top:1.25rem; border-top:1px solid var(--border); text-align:right; color:var(--primary); opacity:0; transform:translateX(-8px); transition:all .3s; }
    .svc-card:hover .svc-arrow { opacity:1; transform:translateX(0); }

    /* PORTFOLIO */
    #portfolio { background:var(--card); }
    .port-header { display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:3rem; gap:2rem; flex-wrap:wrap; }
    .port-sub { color:var(--muted); font-weight:300; max-width:380px; text-align:right; line-height:1.7; }
    .port-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.5rem; }
    .port-item { position:relative; overflow:hidden; background:var(--border); }
    .port-item img { width:100%; aspect-ratio:3/4; object-fit:cover; display:block; transition:transform .7s; }
    .port-item:hover img { transform:scale(1.06); }
    .port-overlay { position:absolute; inset:0; background:linear-gradient(to top,rgba(28,16,7,.88),rgba(28,16,7,.1) 50%,transparent); opacity:0; transition:opacity .5s; display:flex; flex-direction:column; justify-content:flex-end; padding:2rem; }
    .port-item:hover .port-overlay { opacity:1; }
    .port-overlay h4 { font-size:1.2rem; color:#fff; margin-bottom:.4rem; }
    .port-overlay p { font-size:.75rem; color:var(--gold); text-transform:uppercase; letter-spacing:.18em; }

    /* PROCESS */
    #process { background:var(--primary); color:#fff; }
    #process .sec-heading em { color:var(--gold); }
    #process .divider { background:var(--gold); }
    .proc-list { max-width:860px; margin:0 auto; position:relative; }
    .proc-list::before { content:''; position:absolute; left:19px; top:0; bottom:0; width:1px; background:rgba(255,255,255,.15); }
    .proc-item { display:flex; gap:2.5rem; padding-bottom:3.5rem; }
    .proc-step { width:40px; height:40px; border-radius:50%; background:var(--gold); color:var(--primary); font-weight:700; font-size:.85rem; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 0 0 8px var(--primary); }
    .proc-content h3 { font-size:1.4rem; margin-bottom:.75rem; }
    .proc-content p { color:rgba(255,255,255,.75); font-weight:300; line-height:1.9; }

    /* TESTIMONIALS */
    #testimonials { background:var(--bg); }
    .testi-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:2rem; }
    .testi-card { background:var(--card); border:1px solid var(--border); padding:2.5rem; }
    .testi-card blockquote { color:var(--muted); font-style:italic; font-weight:300; line-height:1.9; margin-bottom:1.5rem; }
    .testi-name { font-family:'Playfair Display',serif; font-weight:700; }
    .testi-title { font-size:.75rem; color:var(--primary); text-transform:uppercase; letter-spacing:.15em; margin-top:.25rem; }

    /* CONTACT */
    #contact { background:var(--card); border-top:1px solid var(--border); }
    .contact-grid { display:grid; grid-template-columns:1fr 1fr; gap:5rem; align-items:start; }
    .contact-sub { color:var(--muted); font-weight:300; line-height:1.8; max-width:400px; margin:1rem 0 2.5rem; }
    .info-item { display:flex; align-items:center; gap:1.25rem; margin-bottom:1.5rem; }
    .info-icon { width:48px; height:48px; border-radius:50%; border:1px solid var(--border); display:flex; align-items:center; justify-content:center; color:var(--primary); font-size:1.1rem; flex-shrink:0; }
    .info-lbl { font-size:.72rem; text-transform:uppercase; letter-spacing:.15em; color:var(--muted); font-weight:600; }
    .info-val { font-family:'Playfair Display',serif; font-size:1.05rem; margin-top:.1rem; }
    .contact-form { background:var(--white); padding:2.5rem; box-shadow:0 16px 48px rgba(28,16,7,.08); border:1px solid var(--border); }
    .form-row { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }
    .form-group { margin-bottom:1.5rem; }
    .form-lbl { font-size:.72rem; text-transform:uppercase; letter-spacing:.18em; color:var(--muted); font-weight:600; display:block; margin-bottom:.5rem; }
    .form-input, .form-textarea, .form-select { width:100%; background:transparent; border:none; border-bottom:1px solid var(--border); padding:.75rem 0; font-family:'Outfit',sans-serif; font-size:1rem; color:var(--fg); outline:none; transition:border-color .3s; }
    .form-input:focus, .form-textarea:focus, .form-select:focus { border-bottom-color:var(--primary); }
    .form-textarea { resize:vertical; min-height:110px; }
    .btn-submit { width:100%; background:var(--primary); color:#fff; border:none; padding:1rem 2rem; font-family:'Playfair Display',serif; font-size:1rem; letter-spacing:.1em; cursor:pointer; transition:background .3s; margin-top:.5rem; }
    .btn-submit:hover { background:#5e2030; }
    .form-success { display:none; text-align:center; padding:1rem; color:var(--primary); font-family:'Playfair Display',serif; font-size:1.1rem; }

    /* FOOTER */
    footer { background:var(--fg); color:rgba(255,255,255,.6); padding:2.5rem 3rem; text-align:center; }
    footer .brand { font-family:'Playfair Display',serif; font-size:1.5rem; color
