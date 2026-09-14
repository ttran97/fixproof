"""Revise a copy of the supplied deck, preserving its theme and slide layouts."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.dom import minidom as M
import json, hashlib

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/Users/tonyt/OneDrive/Documents/FixProof – Video II.pptx')
OUT = ROOT / 'FixProof - Video II - Recording Copy.pptx'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
slides = json.loads((ROOT / 'video-content.json').read_text(encoding='utf-8'))
original = SOURCE.read_bytes()
with ZipFile(SOURCE) as z:
    parts = {i.filename: z.read(i) for i in z.infolist()}

def xml(data):
    return M.parseString(data)

def text_body(doc, body, lines, size=None):
    old = list(body.getElementsByTagNameNS(A, 'p'))
    style = next((p for p in old if p.getElementsByTagNameNS(A, 't')), old[0])
    props = style.getElementsByTagNameNS(A, 'pPr')
    runs = style.getElementsByTagNameNS(A, 'rPr')
    for p in old:
        body.removeChild(p)
    for line in lines:
        p = doc.createElementNS(A, 'a:p')
        if props:
            pp = props[0].cloneNode(True)
            for b in list(pp.childNodes):
                if b.nodeType == b.ELEMENT_NODE and b.localName in ('buChar','buAutoNum','buNone'):
                    pp.removeChild(b)
            pp.appendChild(doc.createElementNS(A, 'a:buNone'))
            p.appendChild(pp)
        r = doc.createElementNS(A, 'a:r')
        rp = runs[0].cloneNode(True) if runs else doc.createElementNS(A, 'a:rPr')
        if size:
            rp.setAttribute('sz', str(size))
        r.appendChild(rp)
        t = doc.createElementNS(A, 'a:t')
        t.appendChild(doc.createTextNode(line))
        r.appendChild(t)
        p.appendChild(r)
        body.appendChild(p)

content = xml(parts['[Content_Types].xml'])
for slide in slides:
    n = slide['part']
    path = f'ppt/slides/slide{n}.xml'
    doc = xml(parts[path])
    bodies = doc.getElementsByTagNameNS(P, 'txBody')
    text_body(doc, bodies[0], [slide['title']])
    text_body(doc, bodies[1], slide['lines'], 2400 if n != 1 else 2200)
    if n == 6:
        left = bodies[1].parentNode
        right = left.cloneNode(True)
        identifier = right.getElementsByTagNameNS(P, 'cNvPr')[0]
        identifier.setAttribute('id', '50')
        identifier.setAttribute('name', 'XSS comparison')
        left.parentNode.appendChild(right)
        for shape, xpos, lines in ((left, 650000, slide['lines'][:3]),
                                   (right, 6300000, slide['lines'][3:])):
            for ph in list(shape.getElementsByTagNameNS(P, 'ph')):
                ph.parentNode.removeChild(ph)
            props = shape.getElementsByTagNameNS(P, 'spPr')[0]
            for old in list(props.getElementsByTagNameNS(A, 'xfrm')):
                props.removeChild(old)
            transform = doc.createElementNS(A, 'a:xfrm')
            for tag, attrs in (('off', {'x':xpos,'y':1900000}),
                               ('ext', {'cx':5100000,'cy':4100000})):
                element = doc.createElementNS(A, 'a:'+tag)
                for k,v in attrs.items():
                    element.setAttribute(k,str(v))
                transform.appendChild(element)
            props.insertBefore(transform, props.firstChild)
            text_body(doc, shape.getElementsByTagNameNS(P, 'txBody')[0], lines, 2400)
    parts[path] = doc.toxml(encoding='UTF-8')
    notes = xml(f'''<p:notes xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/><p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes Text"/><p:cNvSpPr txBox="1"/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>''')
    text_body(notes, notes.getElementsByTagNameNS(P, 'txBody')[0], [slide['narration'], 'Evidence / references: '+slide['sources']], 1200)
    parts[f'ppt/notesSlides/notesSlide{n}.xml'] = notes.toxml(encoding='UTF-8')
    parts[f'ppt/notesSlides/_rels/notesSlide{n}.xml.rels'] = f'''<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{R}/notesMaster" Target="../notesMasters/notesMaster1.xml"/><Relationship Id="rId2" Type="{R}/slide" Target="../slides/slide{n}.xml"/></Relationships>'''.encode()
    relpath = f'ppt/slides/_rels/slide{n}.xml.rels'
    rels = xml(parts[relpath])
    for e in list(rels.documentElement.childNodes):
        if e.nodeType == e.ELEMENT_NODE and e.getAttribute('Type') == R+'/notesSlide':
            rels.documentElement.removeChild(e)
    used = {e.getAttribute('Id') for e in rels.documentElement.childNodes if e.nodeType == e.ELEMENT_NODE}
    rid = 1
    while f'rId{rid}' in used:
        rid += 1
    rel = rels.createElementNS(REL, 'Relationship')
    for k,v in {'Id':f'rId{rid}','Type':R+'/notesSlide','Target':f'../notesSlides/notesSlide{n}.xml'}.items():
        rel.setAttribute(k,v)
    rels.documentElement.appendChild(rel)
    parts[relpath] = rels.toxml(encoding='UTF-8')
    partname = f'/ppt/notesSlides/notesSlide{n}.xml'
    if not any(e.getAttribute('PartName') == partname for e in content.documentElement.childNodes if e.nodeType == e.ELEMENT_NODE):
        e = content.createElement('Override')
        e.setAttribute('PartName', partname)
        e.setAttribute('ContentType','application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml')
        content.documentElement.appendChild(e)
parts['[Content_Types].xml'] = content.toxml(encoding='UTF-8')
presentation = xml(parts['ppt/presentation.xml'])
lst = presentation.getElementsByTagNameNS(P,'sldIdLst')[0]
ids = list(lst.getElementsByTagNameNS(P,'sldId'))
for node in ids:
    lst.removeChild(node)
for slide in slides:
    lst.appendChild(ids[slide['part']-1])
parts['ppt/presentation.xml'] = presentation.toxml(encoding='UTF-8')
for name,data in parts.items():
    if name.endswith(('.xml','.rels')):
        xml(data)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,data in parts.items():
        z.writestr(name,data)
with ZipFile(OUT) as z:
    assert z.testzip() is None
assert SOURCE.read_bytes() == original
script = ['# Video II recording script — September 13, 2026', '', 'Use with the reviewed copy of your seven-slide deck. Target approximately five minutes, depending on speaking pace; this is a rehearsal target, not a verified course time limit. The supplied 15-minute limit applies to the final presentation. Narration is also embedded in PowerPoint speaker notes.', '']
for i,s in enumerate(slides,1):
    script += [f"## Slide {i}: {s['title']}", '', s['narration'], '', 'Evidence / references: '+s['sources'], '']
(ROOT/'Video-II-recording-script.md').write_text('\n'.join(script),encoding='utf-8')
(ROOT/'recording-deck-verification.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':hashlib.sha256(original).hexdigest(),'output':str(OUT),'slides':7,'notes':7,'xml_parse':'pass','zip_crc':'pass','original_unchanged':True,'visual_render_checked':False},indent=2),encoding='utf-8')
print(f'Created {OUT}; seven slides and seven speaker-note parts; original unchanged.')
