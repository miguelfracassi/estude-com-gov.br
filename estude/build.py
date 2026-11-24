# -*- coding: utf-8 -*-
# Gera o site de estudos (várias páginas). Rode: python3 build.py
import os, json, shutil, re
from conteudo import TOPICOS, GLOSSARIO, LINHA

NOME = "estudos.6b"
BASE = "/gustavoteixeira/6b"
OUT = "dist"
PROVA = "2026-11-25"
AVISO = "Resumo feito a partir dos temas do caderno. Confira sempre com o seu caderno e com a professora."

IC = {
 "logo": '<path d="M8 21V11l8-4 8 4v10l-8 4z" transform="translate(-2 -3) scale(.95)"/>',
 "face": '<circle cx="12" cy="12" r="9"/><path d="M8 9l2 1M16 9l-2 1M9 16c1-2 5-2 6 0M12 10v3"/>',
 "dome": '<path d="M3 20h18M5 20v-7M19 20v-7M5 13a7 7 0 0 1 14 0M12 3v3M9 20v-4h6v4"/>',
 "mask": '<path d="M4 5c5 2 11 2 16 0v7c0 4-3.5 8-8 8s-8-4-8-8z"/><path d="M8 10h2M14 10h2M9 15c2 1.5 4 1.5 6 0"/>',
 "book": '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11"/>',
 "quiz": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 1-1 1.7M12 17v.5"/>',
 "cards": '<rect x="5" y="4" width="14" height="16" rx="2"/><path d="M9 9h6M9 13h4"/>',
 "ai": '<path d="M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
 "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 "list": '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
 "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
 "table": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M9 5v14"/>',
 "art": '<path d="M12 3a9 9 0 0 0 0 18c1.1 0 1.8-.9 1.8-1.9 0-.5-.2-.9-.5-1.3-.3-.4-.5-.8-.5-1.3 0-1 .8-1.8 1.8-1.8H17a4 4 0 0 0 4-4c0-4.4-4-8.7-9-8.7z"/><circle cx="7.5" cy="11.5" r="1"/><circle cx="10" cy="7.5" r="1"/><circle cx="14.5" cy="7.5" r="1"/>',
}
def svg(n): return '<svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % IC[n]
def sj(o): return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")

# ---------- helpers de corpo ----------
def render(blocks):
    o = ""
    for b in blocks:
        k = b[0]
        if k == "h2": o += "<h2>%s</h2>" % b[1]
        elif k == "p": o += "<p>%s</p>" % b[1]
        elif k == "ul": o += "<ul>%s</ul>" % "".join("<li>%s</li>" % x for x in b[1])
        elif k == "ol": o += "<ol>%s</ol>" % "".join("<li>%s</li>" % x for x in b[1])
        elif k == "alert": o += '<div class="alert">%s</div>' % b[1]
        elif k == "tabela":
            th = "".join("<th>%s</th>" % x for x in b[1])
            tr = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in b[2])
            o += '<div class="table"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, tr)
        elif k == "cartoes":
            o += '<div class="pcards">%s</div>' % "".join('<div class="pcard"><h3>%s</h3><p>%s</p></div>' % x for x in b[1])
    return o

def plain(blocks):
    t = []
    for b in blocks:
        if b[0] in ("h2", "p", "alert"): t.append(b[1])
        elif b[0] in ("ul", "ol"): t += ["- " + x for x in b[1]]
        elif b[0] == "tabela": t += [" | ".join(r) for r in b[2]]
        elif b[0] == "cartoes": t += ["%s: %s" % x for x in b[1]]
    return re.sub(r"<[^>]+>", "", "\n".join(t))

# ---------- páginas ----------
PAGES = {}   # url -> dict(title, desc, group, body, extra)
def add(url, title, desc, group, body, extra="", side=None): PAGES[url] = dict(t=title, d=desc, g=group, b=body, x=extra, s=side)
def U(*p): return BASE + "/" + "".join(x + "/" for x in p)

TKEYS = list(TOPICOS)
ALLQ = []
for k, t in TOPICOS.items():
    for q in t["quiz"]: ALLQ.append(dict(q=q[0], o=q[1], c=q[2], e=q[3]))
ALLC = []
for k, t in TOPICOS.items():
    for c in t["cartas"]: ALLC.append(dict(t=t["nome"], f=c[0], v=c[1]))

def topic_side(k):
    t = TOPICOS[k]
    items = [(U("artes", k, s), n) for s, n, _ in t["paginas"]] + [(U("artes", k, "questoes"), "Questões"), (U("artes", k, "cartas"), "Cartas de estudo")]
    return (t["nome"], items)

TOOLS = [(U("artes"), "Artes (início)"), (U("artes", "simulado"), "Simulado geral"), (U("artes", "cartas"), "Todas as cartas"), (U("artes", "linha-do-tempo"), "Linha do tempo"), (U("artes", "comparar"), "Comparar os temas"), (U("artes", "glossario"), "Glossário"), (U("artes", "ia"), "Tirar dúvidas com IA")]

def pager(prev, nxt):
    h = '<div class="pager">'
    h += '<a class="cardlink" href="%s"><small>Anterior</small><b>%s</b></a>' % prev if prev else "<span></span>"
    h += '<a class="cardlink" href="%s"><small>Próxima</small><b>%s</b></a>' % nxt if nxt else ""
    return h + "</div>"

# páginas de cada tema
for k, t in TOPICOS.items():
    seq = [(U("artes", k, s), n) for s, n, _ in t["paginas"]] + [(U("artes", k, "questoes"), "Questões"), (U("artes", k, "cartas"), "Cartas de estudo")]
    for i, (s, n, d) in enumerate(t["paginas"]):
        u = U("artes", k, s)
        body = render(t["corpo"][s]) + pager(seq[i-1] if i else None, seq[i+1])
        add(u, "%s: %s" % (t["nome"], n) if s != "resumo" else "%s: resumo" % t["nome"], d, "t:" + k, body)
    u = U("artes", k, "questoes")
    add(u, "%s: questões" % t["nome"], "Teste o que você aprendeu com %d questões e veja a explicação de cada uma." % len(t["quiz"]), "t:" + k,
        '<p>Escolha uma alternativa. Depois de responder, você vê a explicação. No final, dá para refazer só as que errou.</p><div class="quiz" id="quiz" data-key="%s"></div>' % k + pager(seq[-3], seq[-1]),
        '<script type="application/json" id="quiz-data">%s</script>' % sj([dict(q=q[0], o=q[1], c=q[2], e=q[3]) for q in t["quiz"]]))
    u = U("artes", k, "cartas")
    add(u, "%s: cartas de estudo" % t["nome"], "Cartas para virar e memorizar os conceitos de %s." % t["nome"], "t:" + k,
        '<p>Leia a pergunta, tente lembrar a resposta e clique na carta para conferir.</p><div class="deck" id="deck"></div>' + pager(seq[-2], None),
        '<script type="application/json" id="deck-data">%s</script>' % sj([dict(t=t["nome"], f=c[0], v=c[1]) for c in t["cartas"]]))

# hub de Artes
tiles = "".join('<a class="tile t-%s" href="%s">%s<h3>%s</h3><p>%s</p></a>' % (t["cor"], U("artes", k), svg(t["icone"]), t["nome"], t["resumo_curto"]) for k, t in TOPICOS.items())
tools = "".join('<li><a href="%s"><i>%d</i>%s</a></li>' % (u, i + 1, n) for i, (u, n) in enumerate(TOOLS[1:]))
add(U("artes"), "Artes", "Expressionismo, Renascimento, Commedia dell'Arte e Mímica: resumo e questões do caderno.", "tools",
    '<div class="alert i"><strong>Prova de Artes:</strong> <span data-date="%s">25/11</span>. Comece pelo resumo de cada tema e depois faça as questões e o simulado.</div><h2>Os 3 temas</h2><div class="tiles" style="grid-template-columns:repeat(auto-fill,minmax(230px,1fr))">%s</div><h2>Ferramentas de estudo</h2><ol class="gv-list">%s</ol><h2>Plano rápido para estudar</h2><ol><li>Leia o <strong>resumo</strong> dos três temas.</li><li>Veja a página <strong>Para lembrar na prova</strong> de cada tema.</li><li>Faça as <strong>questões</strong> e refaça as que errar.</li><li>Treine com as <strong>cartas</strong> e com o <strong>simulado geral</strong>.</li></ol>' % (PROVA, tiles, tools))

add(U("artes", "simulado"), "Simulado geral", "15 questões sorteadas dos três temas. Cada vez que você abre, muda.", "tools",
    '<p>As questões são sorteadas entre todos os temas, como numa prova de verdade.</p><div class="quiz" id="quiz" data-key="simulado" data-n="15"></div><p style="margin-top:1rem"><button class="btn ghost" id="quiz-new" type="button">Sortear outro simulado</button></p>',
    '<script type="application/json" id="quiz-data">%s</script>' % sj(ALLQ))
add(U("artes", "cartas"), "Todas as cartas", "Cartas de estudo dos três temas, misturadas.", "tools",
    '<p>Cartas de todos os temas. Use <strong>Embaralhar</strong> para misturar.</p><div class="deck" id="deck"></div>',
    '<script type="application/json" id="deck-data">%s</script>' % sj(ALLC))
add(U("artes", "linha-do-tempo"), "Linha do tempo", "Veja em que ordem aconteceram os principais fatos.", "tools",
    '<ol class="tl">%s</ol>' % "".join('<li><time>%s</time><h3>%s</h3><p>%s</p></li>' % (a, b, c) for a, b, c, _ in LINHA))
add(U("artes", "comparar"), "Comparar os temas", "Tabela com as diferenças entre Renascimento, Expressionismo, Commedia dell'Arte e Mímica.", "tools",
    render([("tabela", ["", "Renascimento", "Expressionismo", "Commedia dell'Arte", "Mímica"], [
        ["Época", "Séc. XIV a XVI", "Início do séc. XX", "Séc. XVI", "Antiguidade; famosa no séc. XX"],
        ["Lugar", "Itália (Florença)", "Alemanha", "Itália", "Grécia, Roma, França"],
        ["Ideia central", "Ser humano e razão", "Emoção e sentimento", "Comédia improvisada", "Expressar sem palavras"],
        ["Marca", "Perspectiva, proporção", "Cores fortes, formas distorcidas", "Máscaras, personagens fixos", "Gestos, parede invisível"],
        ["Nomes", "Leonardo, Michelangelo, Rafael", "Munch, Kandinsky, Anita Malfatti", "Arlequim, Colombina, Pantaleão", "Marceau, Chaplin"],
    ]), ("alert", "<strong>Dica:</strong> Renascimento = razão e equilíbrio. Expressionismo = emoção e distorção. Commedia = improviso e máscaras. Mímica = silêncio e gestos.")]))
add(U("artes", "glossario"), "Glossário", "Palavras importantes dos temas, em ordem alfabética.", "tools",
    '<dl class="gl">%s</dl>' % "".join('<dt>%s</dt><dd>%s <a href="%s">ver tema</a></dd>' % (a, b, U("artes", c)) for a, b, c in sorted(GLOSSARIO, key=lambda x: x[0].lower())))
add(U("artes", "ia"), "Tirar dúvidas com IA", "Pergunte ao assistente sobre os temas de Artes.", "tools",
    '<div class="sugs"><button type="button">Explique o Expressionismo de forma simples</button><button type="button">Faça uma pergunta de quiz sobre o Renascimento</button><button type="button">Quem é o Arlequim?</button></div><div class="chat" id="chat"><div class="chat-log" aria-live="polite"></div><form><input aria-label="Sua pergunta" placeholder="Digite sua dúvida..." maxlength="500" autocomplete="off"><button class="btn b" type="submit">Enviar</button></form></div><p style="font-size:.85rem;color:var(--mute)">A IA pode errar. Confira no resumo e no caderno.</p>')
add(U("busca"), "Busca", "Pesquise páginas do site.", None,
    '<form class="f" action="%s" role="search"><label>Buscar<input id="bq" name="q" autofocus></label><button class="btn b" type="submit">Buscar</button></form><p id="scount" role="status"></p><ul class="sres" id="sres"></ul>' % U("busca"))
add(U("mapa-do-site"), "Mapa do site", "Todas as páginas.", None, "@@MAPA@@")

# ---------- template ----------
NAV = [(BASE + "/", "Início"), (U("artes"), "Artes")] + [(U("artes", k), TOPICOS[k]["nome"].replace(" e Mímica", " e Mímica")) for k in TKEYS] + [(U("artes", "simulado"), "Simulado"), (U("artes", "ia"), "IA")]

def head(t, d):
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s — %s</title><meta name="description" content="%s"><meta name="theme-color" content="#071d41"><meta name="robots" content="noindex"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="preload" href="/assets/fonts/rawline-700.ttf" as="font" type="font/ttf" crossorigin><link rel="stylesheet" href="/assets/css/style.css"></head><body><a class="skip" href="#main">Ir para o conteúdo</a>' % (t, NOME, d.replace('"', "&quot;"))

def header(cur):
    nav = "".join('<li><a href="%s"%s>%s</a></li>' % (u, ' aria-current="page"' if u == cur else "", n) for u, n in NAV)
    s = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">%s</svg>' % IC["search"]
    return '<header class="site"><div class="wrap hrow"><a class="brand" href="%s/"><span class="lg">%s</span><div><span>%s</span><small>Site de estudos do 6º B</small></div></a><form class="hsearch" action="%s" role="search"><input name="q" placeholder="O que você procura?" aria-label="Buscar"><button aria-label="Buscar">%s</button></form><a class="hs-ico" href="%s" aria-label="Buscar">%s</a><button class="menu-btn" data-act="menu" aria-expanded="false" aria-controls="nav"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>Menu</button></div><nav class="nav" id="nav" aria-label="Principal"><div class="wrap"><ul>%s</ul></div></nav></header>' % (BASE, svg("book"), NOME, U("busca"), s, U("busca"), s, nav)

def footer():
    col = lambda t, it: "<div><h2>%s</h2><ul>%s</ul></div>" % (t, "".join('<li><a href="%s">%s</a></li>' % x for x in it))
    return '<div class="stripe"><i></i><i></i><i></i><i></i></div><footer class="site"><div class="wrap fgrid"><div><a class="brand" href="%s/"><span class="lg">%s</span><div><span>%s</span><small>6º ano B</small></div></a><p>Resumos, questões e cartas para estudar para a prova.</p></div>%s%s%s</div><div class="acc"><div class="wrap"><strong>Acessibilidade</strong><div class="tools"><button data-act="fm" aria-label="Diminuir letra">A-</button><button data-act="fp" aria-label="Aumentar letra">A+</button><button data-act="hc">Alto contraste</button></div></div></div><div class="fict"><div class="wrap"><p><strong>Aviso:</strong> %s Este site é feito por aluno e não é oficial da escola.</p></div></div></footer><script src="/assets/js/main.js"></script></body></html>' % (
        BASE, svg("book"), NOME,
        col("Temas", [(U("artes", k), TOPICOS[k]["nome"]) for k in TKEYS]),
        col("Estudar", [(U("artes", "simulado"), "Simulado"), (U("artes", "cartas"), "Cartas"), (U("artes", "glossario"), "Glossário"), (U("artes", "linha-do-tempo"), "Linha do tempo")]),
        col("Site", [(U("artes", "ia"), "Tirar dúvidas com IA"), (U("busca"), "Busca"), (U("mapa-do-site"), "Mapa do site")]), AVISO)

def sidebar(url, g):
    if g is None: return ""
    if g.startswith("t:"): title, items = topic_side(g[2:])
    else: title, items = "Artes", TOOLS
    li = "".join('<li><a href="%s"%s>%s</a></li>' % (u, ' aria-current="page"' if u == url else "", n) for u, n in items)
    other = ""
    if g.startswith("t:"):
        other = '<hr><h2>Outros temas</h2><ul>%s</ul>' % "".join('<li><a href="%s">%s</a></li>' % (U("artes", k), TOPICOS[k]["nome"]) for k in TKEYS if k != g[2:])
    return '<aside class="side"><h2>%s</h2><ul>%s</ul>%s</aside>' % (title, li, other)

def page(url, p, full=True):
    t = p["t"]; crumb = '<a href="%s/">Início</a><span>/</span>' % BASE
    if url.startswith(U("artes")) and url != U("artes"): crumb += '<a href="%s">Artes</a><span>/</span>' % U("artes")
    if p["g"] and p["g"].startswith("t:"): crumb += '<a href="%s">%s</a><span>/</span>' % (U("artes", p["g"][2:]), TOPICOS[p["g"][2:]]["nome"])
    lay = '<div class="wrap layout"%s>%s<div class="content">%s</div></div>' % ("" if p["g"] else ' style="grid-template-columns:1fr"', sidebar(url, p["g"]), p["b"])
    return head(t, p["d"]) + header(url) + '<main id="main"><div class="pagehead"><div class="wrap"><div class="crumb">%s%s</div><h1>%s</h1><p>%s</p></div></div><div class="stripe"><i></i><i></i><i></i><i></i></div>%s</main>%s' % (crumb, t.split(": ")[-1] if False else t, t, p["d"], lay, p["x"]) + footer()

def write(path, html):
    f = os.path.join(OUT, path.strip("/"), "index.html") if not path.endswith(".html") else os.path.join(OUT, path)
    os.makedirs(os.path.dirname(f), exist_ok=True); open(f, "w", encoding="utf-8").write(html)

# mapa e índice de busca
mapa = "<h2>Artes</h2><ul>%s</ul>" % "".join('<li><a href="%s">%s</a> — %s</li>' % (u, p["t"], p["d"]) for u, p in PAGES.items() if u.startswith(U("artes")))
PAGES[U("mapa-do-site")]["b"] = mapa
idx = [dict(t=p["t"], d=p["d"], u=u) for u, p in PAGES.items()] + [dict(t=a, d=b, u=U("artes", "glossario")) for a, b, c in GLOSSARIO]
PAGES[U("busca")]["x"] = "<script>window.SITE_INDEX=%s</script>" % sj(idx)

shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree("assets", os.path.join(OUT, "assets"))
open(os.path.join(OUT, "assets", "favicon.svg"), "w").write("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='7' fill='#1351b4'/><path d='M9 22V10h9a4 4 0 0 1 0 8H9M9 18h9' fill='none' stroke='#fff' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/></svg>")
for u, p in PAGES.items(): write(u, page(u, p))

# home
cats = "".join('<a href="%s">%s<span>%s</span></a>' % (u, svg(i), n) for u, i, n in [
    (U("artes", "expressionismo"), "face", "Expressionismo"), (U("artes", "renascimento"), "dome", "Renascimento"),
    (U("artes", "commedia-dellarte-e-mimica"), "mask", "Commedia e Mímica"), (U("artes", "simulado"), "quiz", "Simulado"),
    (U("artes", "cartas"), "cards", "Cartas"), (U("artes", "glossario"), "list", "Glossário"),
    (U("artes", "linha-do-tempo"), "clock", "Linha do tempo"), (U("artes", "ia"), "ai", "Tirar dúvidas com IA")])
mais = '<ol class="gv-list">%s</ol>' % "".join('<li><a href="%s"><i>%d</i>%s</a></li>' % (u, i + 1, n) for i, (u, n) in enumerate([
    (U("artes", "expressionismo", "resumo"), "Resumo de Expressionismo"), (U("artes", "renascimento", "resumo"), "Resumo de Renascimento"),
    (U("artes", "commedia-dellarte-e-mimica", "resumo"), "Resumo de Commedia dell'Arte e Mímica"), (U("artes", "simulado"), "Fazer o simulado"),
    (U("artes", "comparar"), "Comparar os temas"), (U("artes", "ia"), "Perguntar para a IA")]))
dest = '<ul class="gv-list gv-dest"><li><a href="%s"><small>Artes · <span data-date="%s">25/11</span><em>Prova</em></small>Prova de Artes</a></li><li><a href="%s"><small>Novo</small>Simulado com 15 questões sorteadas</a></li><li><a href="%s"><small>Revisão rápida</small>Cartas de estudo</a></li><li><a href="%s"><small>Consulta</small>Glossário das palavras importantes</a></li></ul>' % (U("artes"), PROVA, U("artes", "simulado"), U("artes", "cartas"), U("artes", "glossario"))
home = head("Início", "Site de estudos do 6º B: resumos, questões e cartas de Artes.") + header(BASE + "/") + '<div class="stripe"><i></i><i></i><i></i><i></i></div><main id="main"><section class="gv-top"><div class="wrap"><p class="gv-kicker">Estudos do 6º ano B</p><form class="bigsearch" action="%s" role="search"><input name="q" placeholder="O que você quer estudar?" aria-label="Buscar"><button aria-label="Buscar"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">%s</svg></button></form></div></section>' % (U("busca"), IC["search"]) + \
  '<section class="blk"><div class="wrap"><h2 class="gv-t">Estudar para a prova</h2><div class="gv-two"><div class="gv-panel"><h3 class="gv-h"><span>Mais acessados</span></h3>%s</div><div class="gv-panel"><h3 class="gv-h"><span>Destaques</span></h3>%s</div></div></div></section>' % (mais, dest) + \
  '<section class="blk alt"><div class="wrap"><h2 class="gv-t">Navegue por categoria</h2><p class="sub c">Escolha um tema ou uma ferramenta de estudo.</p><div class="cats">%s</div></div></section>' % cats + \
  '<section class="blk"><div class="wrap"><h2 class="gv-t">Os 3 temas de Artes</h2><div class="tiles">%s</div></div></section>' % tiles + \
  '<section class="blk" style="padding-top:0"><div class="wrap"><div class="band"><div><h2>Pronto para testar?</h2><p>Faça o simulado e descubra o que ainda precisa revisar.</p></div><a class="btn" href="%s">Fazer simulado</a></div></div></section>' % U("artes", "simulado") + \
  '<section class="blk alt"><div class="wrap"><h2 class="gv-t">Outras matérias</h2><p class="sub c">Educação Física, Inglês, Ciências, Língua Portuguesa, Matemática e Geografia: em breve.</p></div></section></main>' + footer()
write(BASE + "/", home)
write("index.html", '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=%s/"><title>%s</title><a href="%s/">Entrar</a>' % (BASE, NOME, BASE))
write("404.html", page("/404/", dict(t="Página não encontrada", d="Esse endereço não existe.", g=None, x="", s=None, b='<p>Volte para o <a href="%s/">início</a> ou veja o <a href="%s">mapa do site</a>.</p>' % (BASE, U("mapa-do-site")))))

# material para a IA
mat = "\n\n".join("## %s\n%s" % (t["nome"], "\n\n".join(plain(t["corpo"][s]) for s, _, _ in t["paginas"] if s != "para-lembrar")) for t in TOPICOS.values())
os.makedirs("content", exist_ok=True)
json.dump(dict(materia="Artes", topico="Expressionismo, Renascimento, Commedia dell'Arte e Mímica", material=mat), open("content/artes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"buildCommand": "python3 build.py", "outputDirectory": OUT, "cleanUrls": True, "trailingSlash": True, "functions": {"api/chat.js": {"maxDuration": 30, "includeFiles": "content/**"}}}, open("vercel.json", "w"), indent=1)
print(len(PAGES) + 3, "páginas geradas em", OUT)
