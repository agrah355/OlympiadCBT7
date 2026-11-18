import json, os
from datetime import datetime
from fastapi import FastAPI, Depends, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import fitz
from .db import Base, engine, get_db
from .models import Paper, Question, Attempt
from .schemas import PaperIn, QuestionIn, SubmitIn
from .ingest import sanitize_text, parse_questions, parse_answer_csv

Base.metadata.create_all(bind=engine)
app = FastAPI(title='OlympiadCBT API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://localhost:3000').split(','), allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
ADMIN_KEY = os.getenv('ADMIN_KEY', 'change-me-admin-key')
def admin_guard(x_admin_key: str = Header(default='')):
    if x_admin_key != ADMIN_KEY: raise HTTPException(401, 'Invalid admin key')

def question_dict(q):
    return {'id':q.id,'number':q.number,'body':q.body,'options':json.loads(q.options or '[]'),'answer':q.answer,'solution':q.solution,'reviewed':q.reviewed}
def paper_dict(p, include_questions=False):
    d={'id':p.id,'title':p.title,'subject':p.subject,'year':p.year,'duration_minutes':p.duration_minutes,'positive_marks':p.positive_marks,'negative_marks':p.negative_marks,'published':p.published,'question_count':len(p.questions)}
    if include_questions: d['questions']=[question_dict(q) for q in sorted(p.questions,key=lambda x:x.number)]
    return d

@app.get('/api/health')
def health(): return {'status':'ok','service':'OlympiadCBT'}

@app.get('/api/papers')
def papers(subject: str|None=None, db: Session=Depends(get_db)):
    query=db.query(Paper).filter(Paper.published == True)
    if subject: query=query.filter(Paper.subject==subject)
    return [paper_dict(p) for p in query.order_by(Paper.year.desc()).all()]

@app.get('/api/papers/{paper_id}')
def get_paper(paper_id:int, db:Session=Depends(get_db)):
    p=db.get(Paper,paper_id)
    if not p or not p.published: raise HTTPException(404,'Paper not found')
    d=paper_dict(p,True)
    # Never expose answer keys or solutions in the test payload.
    for q in d['questions']: q.pop('answer',None); q.pop('solution',None)
    return d

@app.post('/api/admin/papers', dependencies=[Depends(admin_guard)])
def create_paper(payload:PaperIn, db:Session=Depends(get_db)):
    p=Paper(**payload.model_dump()); db.add(p); db.commit(); db.refresh(p); return paper_dict(p)

@app.post('/api/admin/papers/{paper_id}/upload-pdf', dependencies=[Depends(admin_guard)])
async def upload_pdf(paper_id:int, file:UploadFile=File(...), db:Session=Depends(get_db)):
    p=db.get(Paper,paper_id)
    if not p: raise HTTPException(404,'Paper not found')
    if not file.filename.lower().endswith('.pdf'): raise HTTPException(400,'Upload a PDF file')
    raw=await file.read()
    doc=fitz.open(stream=raw,filetype='pdf')
    text='\n'.join(page.get_text('text') for page in doc)
    parsed=parse_questions(sanitize_text(text))
    for item in parsed:
        exists=db.query(Question).filter_by(paper_id=paper_id,number=item['number']).first()
        if not exists: db.add(Question(paper_id=paper_id,number=item['number'],body=item['body'],options=json.dumps(item['options'])))
    db.commit()
    return {'extracted_pages':len(doc),'parsed_questions':len(parsed),'message':'Extraction is a draft; review every question before publishing.'}

@app.post('/api/admin/papers/{paper_id}/upload-key', dependencies=[Depends(admin_guard)])
async def upload_key(paper_id:int, file:UploadFile=File(...), db:Session=Depends(get_db)):
    if not db.get(Paper,paper_id): raise HTTPException(404,'Paper not found')
    raw=await file.read()
    if file.filename.lower().endswith('.pdf'):
        doc=fitz.open(stream=raw,filetype='pdf'); raw='\n'.join(pg.get_text() for pg in doc).encode()
        import re
        pairs=re.findall(r'(?m)^\s*(\d{1,3})\s*[.)-]?\s*[:=]?\s*([A-E])\b',raw.decode(errors='ignore').upper())
        answers=dict(pairs)
    else: answers=parse_answer_csv(raw)
    updated=0
    for num,ans in answers.items():
        q=db.query(Question).filter_by(paper_id=paper_id,number=int(num)).first()
        if q: q.answer=ans; updated+=1
    db.commit(); return {'keys_found':len(answers),'questions_updated':updated}

@app.get('/api/admin/papers', dependencies=[Depends(admin_guard)])
def admin_papers(db:Session=Depends(get_db)):
    return [paper_dict(p,True) for p in db.query(Paper).order_by(Paper.year.desc()).all()]

@app.put('/api/admin/questions/{question_id}', dependencies=[Depends(admin_guard)])
def update_question(question_id:int, payload:QuestionIn, db:Session=Depends(get_db)):
    q=db.get(Question,question_id)
    if not q: raise HTTPException(404,'Question not found')
    for k,v in payload.model_dump().items(): setattr(q,k,json.dumps(v) if k=='options' else v)
    db.commit(); db.refresh(q); return question_dict(q)

@app.post('/api/admin/papers/{paper_id}/questions', dependencies=[Depends(admin_guard)])
def add_question(paper_id:int, payload:QuestionIn, db:Session=Depends(get_db)):
    if not db.get(Paper,paper_id): raise HTTPException(404,'Paper not found')
    q=Question(paper_id=paper_id,number=payload.number,body=payload.body,options=json.dumps(payload.options),answer=payload.answer,solution=payload.solution,reviewed=payload.reviewed)
    db.add(q); db.commit(); db.refresh(q); return question_dict(q)

@app.post('/api/admin/papers/{paper_id}/publish', dependencies=[Depends(admin_guard)])
def publish(paper_id:int, db:Session=Depends(get_db)):
    p=db.get(Paper,paper_id)
    if not p: raise HTTPException(404,'Paper not found')
    if not p.questions: raise HTTPException(400,'Add questions before publishing')
    missing=[q.number for q in p.questions if not q.answer]
    unreviewed=[q.number for q in p.questions if not q.reviewed]
    if missing or unreviewed: raise HTTPException(400,detail={'message':'Complete review before publishing','missing_answers':missing,'unreviewed_questions':unreviewed})
    p.published=True; db.commit(); return paper_dict(p)

@app.post('/api/attempts/{paper_id}/submit')
def submit(paper_id:int, payload:SubmitIn, db:Session=Depends(get_db)):
    p=db.get(Paper,paper_id)
    if not p or not p.published: raise HTTPException(404,'Paper not found')
    qs=db.query(Question).filter_by(paper_id=paper_id).all()
    score=0.0; attempted=0; correct=0; breakdown=[]
    for q in qs:
        selected=payload.answers.get(str(q.number),'')
        is_correct=bool(selected and q.answer and selected.upper()==q.answer.upper())
        if selected:
            attempted+=1
            if is_correct: score+=p.positive_marks; correct+=1
            else: score-=p.negative_marks
        breakdown.append({'number':q.number,'selected':selected or None,'correct_answer':q.answer,'is_correct':is_correct if selected else None,'body':q.body,'options':json.loads(q.options or '[]'),'solution':q.solution})
    max_score=len(qs)*p.positive_marks
    accuracy=(correct/attempted*100) if attempted else 0
    a=Attempt(student=payload.student,paper_id=paper_id,answers=json.dumps(payload.answers),score=score,max_score=max_score,accuracy=accuracy,time_taken_seconds=payload.time_taken_seconds)
    db.add(a); db.commit(); db.refresh(a)
    return {'attempt_id':a.id,'score':score,'max_score':max_score,'percentage':round((score/max_score*100) if max_score else 0,2),'accuracy':round(accuracy,2),'correct':correct,'attempted':attempted,'unattempted':len(qs)-attempted,'time_taken_seconds':payload.time_taken_seconds,'breakdown':breakdown}

@app.get('/api/attempts')
def attempts(student:str='Student', db:Session=Depends(get_db)):
    rows=db.query(Attempt).filter_by(student=student).order_by(Attempt.submitted_at.desc()).all()
    return [{'id':a.id,'paper':paper_dict(db.get(Paper,a.paper_id))['title'],'paper_id':a.paper_id,'score':a.score,'max_score':a.max_score,'accuracy':a.accuracy,'time_taken_seconds':a.time_taken_seconds,'submitted_at':a.submitted_at.isoformat()} for a in rows]
