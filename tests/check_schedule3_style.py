"""Check Schedule 3 style."""
from docx import Document
from docx.oxml.ns import qn

doc = Document('tests/temp_new_attachment.docx')

for i, para in enumerate(doc.paragraphs):
    if 'Schedule 3' in para.text:
        print(f"Para {i}: style_id={para.style.style_id if para.style else None}")
        print(f"  para_id={para._element.get(qn('w14:paraId'))}")
        print(f"  text={para.text[:80]}")
        
        # Check the XML
        pPr = para._element.pPr
        if pPr is not None:
            pStyle = pPr.find(qn('w:pStyle'))
            if pStyle is not None:
                print(f"  XML style value: {pStyle.get(qn('w:val'))}")
