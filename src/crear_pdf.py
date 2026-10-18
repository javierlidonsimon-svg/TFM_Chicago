"""Convierte el informe Markdown del proyecto a un PDF legible e ilustrado."""
from pathlib import Path
import re, html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]

def main():
    font='Helvetica'
    fonts=Path('C:/Windows/Fonts')
    if (fonts/'arial.ttf').exists():
        for name,file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf'),('Arial-Italic','ariali.ttf')]:
            pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
        pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-Bold')
        font='Arial'
    styles=getSampleStyleSheet()
    for s in ['Normal','BodyText','Title','Heading1','Heading2','Heading3']:
        styles[s].fontName=font
        styles[s].textColor=colors.HexColor('#17365D') if s!='BodyText' else colors.HexColor('#253245')
    styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=7
    styles['Title'].fontSize=23;styles['Title'].leading=29;styles['Title'].alignment=TA_LEFT;styles['Title'].spaceAfter=16
    styles['Heading1'].fontSize=15;styles['Heading1'].leading=20;styles['Heading1'].spaceBefore=15;styles['Heading1'].spaceAfter=9
    styles['Heading2'].fontSize=12;styles['Heading2'].leading=17
    for heading in ['Title','Heading1','Heading2','Heading3']:
        styles[heading].keepWithNext=True
    styles['BodyText'].allowOrphans=0
    styles['BodyText'].allowWidows=0
    small=ParagraphStyle('Table',parent=styles['BodyText'],fontSize=8.5,leading=11,spaceAfter=0)
    width=A4[0]-96
    def inline(s):
        s=html.escape(s)
        s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
        s=re.sub(r'`([^`]+)`',r'<font color="#2457A7">\1</font>',s)
        s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#2457A7">\1</link>',s)
        return s
    story=[]; lines=(ROOT/'reports/informe.md').read_text(encoding='utf-8').splitlines();i=0
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line:continue
        if line.startswith('!['):
            m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
            img=Image(str(ROOT/'reports'/m.group(2)))
            ratio=min(width/img.imageWidth,260/img.imageHeight)
            img.drawWidth=img.imageWidth*ratio;img.drawHeight=img.imageHeight*ratio
            story.append(KeepTogether([Spacer(1,5),img,Spacer(1,8)]));continue
        if line.startswith('|'):
            rows=[line]
            while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
            cells=[]
            for row in rows:
                if re.fullmatch(r'[|:\-\s]+',row):continue
                cells.append([Paragraph(inline(c.strip()),small) for c in row.strip('|').split('|')])
            n=len(cells[0]); widths=[width*.31]+[width*.69/(n-1)]*(n-1)
            table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7EDF6')),
                ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#17365D')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FC')])]))
            story.extend([KeepTogether([table,Spacer(1,10)])]);continue
        if line.startswith('### '):style=styles['Heading2'];line=line[4:]
        elif line.startswith('## '):style=styles['Heading1'];line=line[3:]
        elif line.startswith('# '):style=styles['Title'];line=line[2:]
        else:style=styles['BodyText']
        if line.startswith('- '):line='• '+line[2:]
        story.append(Paragraph(inline(line),style))
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#CBD5E1'));canvas.line(48,42,A4[0]-48,42)
        canvas.setFont(font,8);canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(48,28,'ThePower · Análisis de datos · Chicago 2024')
        canvas.drawRightString(A4[0]-48,28,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(ROOT/'reports/Informe_Chicago_2024.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=44,bottomMargin=57,
        title='Seguridad vial en Chicago y meteorología diaria',author='')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':main()
