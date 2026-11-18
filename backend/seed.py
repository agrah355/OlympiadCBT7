from app.db import Base,engine,SessionLocal
from app.models import Paper,Question
import json
Base.metadata.create_all(bind=engine); db=SessionLocal()
if not db.query(Paper).first():
 p=Paper(title='NSEP 2024 — Demo Practice Set',subject='Physics',year=2024,duration_minutes=120,positive_marks=3,negative_marks=1,published=True); db.add(p); db.flush()
 data=[(1,'A particle moves with position $x(t)=3t^2-2t$. Its velocity at $t=2\\,s$ is:', ['A. $8\\,m/s$','B. $10\\,m/s$','C. $12\\,m/s$','D. $14\\,m/s$'],'B','Differentiate: $v=\\frac{dx}{dt}=6t-2$. At $t=2$, $v=10\\,m/s$.'),(2,'For an ideal gas undergoing an isothermal expansion, which quantity remains constant?', ['A. Pressure','B. Volume','C. Temperature','D. Internal energy'],'C','An isothermal process has constant temperature by definition.')]
 for n,b,o,a,s in data: db.add(Question(paper_id=p.id,number=n,body=b,options=json.dumps(o),answer=a,solution=s,reviewed=True))
 db.commit()
db.close(); print('Seeded demo paper.')
