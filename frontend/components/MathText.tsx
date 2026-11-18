'use client';
import {InlineMath, BlockMath} from 'react-katex';
export default function MathText({text}:{text:string}) {
 const parts=text.split(/(\$\$[\s\S]*?\$\$|\$[^$\n]+\$)/g);
 return <>{parts.map((p,i)=>p.startsWith('$$')?<BlockMath key={i} math={p.slice(2,-2)}/>:p.startsWith('$')?<InlineMath key={i} math={p.slice(1,-1)}/>:<span key={i} className="whitespace-pre-wrap">{p}</span>)}</>;
}
