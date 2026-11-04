/* Experimental JavaScript runtime for the RostLang WebView launcher.
 * This is a staged port. The Python runtime remains the reference implementation.
 */
(function (root) {
  "use strict";
  class RostError extends Error {}
  const tokenize = (s) => {
    const out=[]; let i=0;
    while(i<s.length){
      const c=s[i];
      if(/\s/.test(c)){i++;continue;}
      if(c==="#" ) break;
      if(c==='"'||c==="'"){const q=c;let v="";i++;while(i<s.length&&s[i]!==q){if(s[i]==="\\"){i++;const e=s[i];v+=({"n":"\n","t":"\t","r":"\r"}[e]??e);i++;}else v+=s[i++];}if(s[i]!==q)throw new RostError("Unterminated string");i++;out.push({t:"str",v});continue;}
      const n=s.slice(i).match(/^(?:\d+(?:\.\d*)?|\.\d+)/);if(n){out.push({t:"num",v:Number(n[0])});i+=n[0].length;continue;}
      const id=s.slice(i).match(/^[A-Za-z_][A-Za-z0-9_]*/);if(id){out.push({t:"id",v:id[0]});i+=id[0].length;continue;}
      const op=["==","!=","<=",">=","//","**","&&","||"].find(x=>s.startsWith(x,i))||c;
      if("+-*/%<>()[]{}:,.".includes(c)||["==","!=","<=",">=","//","**","&&","||"].includes(op)){out.push({t:"op",v:op});i+=op.length;continue;}
      throw new RostError("Unexpected character: "+c);
    }
    out.push({t:"eof",v:""});return out;
  };
  class Expr {
    constructor(source,env){this.ts=tokenize(source);this.i=0;this.env=env;}
    peek(){return this.ts[this.i];} take(){return this.ts[this.i++];}
    need(v){if(this.take().v!==v)throw new RostError("Expected "+v);}
    parse(){const v=this.expr(0);if(this.peek().t!=="eof")throw new RostError("Unexpected token "+this.peek().v);return v;}
    expr(min){
      let t=this.take(), left;
      if(t.t==="num"||t.t==="str")left=t.v;
      else if(t.t==="id"){
        if(t.v==="true"||t.v==="True")left=true;
        else if(t.v==="false"||t.v==="False")left=false;
        else if(t.v==="nothing"||t.v==="None")left=null;
        else if(this.peek().v==="("){this.take();const a=this.args(")");left=this.env.call(t.v,a);}
        else left=this.env.get(t.v);
      } else if(t.v==="("){left=this.expr(0);this.need(")");}
      else if(t.v==="["){left=this.args("]");}
      else if(t.v==="-"||t.v==="+"||t.v==="!"){const x=this.expr(80);left=t.v==="-"?-x:t.v==="+"?+x:!x;}
      else throw new RostError("Invalid expression near "+t.v);
      while(true){
        const p=this.peek().v;
        if(p==="["&&90>=min){this.take();const ix=this.expr(0);this.need("]");left=left[ix];continue;}
        if(p==="."&&90>=min){this.take();const name=this.take().v;if(left===null||typeof left!=="object")throw new RostError("Attribute access expects an object");left=left[name];continue;}
        const prec={"or":10,"||":10,"and":20,"&&":20,"==":30,"!=":30,"<":30,">":30,"<=":30,">=":30,"in":30,"+":40,"-":40,"*":50,"/":50,"//":50,"%":50,"**":60}[p]||0;
        if(!prec||prec<min)break;
        this.take();const right=this.expr(prec+(p==="**"?0:1));
        switch(p){case "+":left=typeof left==="string"||typeof right==="string"?String(left)+String(right):left+right;break;case "-":left-=right;break;case "*":left*=right;break;case "/":if(right===0)throw new RostError("division by zero");left/=right;break;case "//":left=Math.floor(left/right);break;case "%":left%=right;break;case "**":left**=right;break;case "==":left=left===right;break;case "!=":left=left!==right;break;case "<":left=left<right;break;case ">":left=left>right;break;case "<=":left=left<=right;break;case ">=":left=left>=right;break;case "and":case "&&":left=Boolean(left&&right);break;case "or":case "||":left=Boolean(left||right);break;case "in":left=Array.isArray(right)?right.includes(left):String(right).includes(String(left));}
      }
      return left;
    }
    args(end){const a=[];if(this.peek().v===end){this.take();return a;}while(true){a.push(this.expr(0));if(this.peek().v===end){this.take();break;}this.need(",");}return a;}
  }
  class RostRuntime {
    constructor(io={}){this.io=io;this.vars={};this.scopes=[];this.funcs={};this.steps=0;}
    out(v){this.io.print?.(this.str(v));}
    str(v){if(v===null)return "nothing";if(v===true)return "true";if(v===false)return "false";if(Array.isArray(v))return "["+v.map(x=>this.str(x)).join(", ")+"]";return String(v);}
    get(n){for(let i=this.scopes.length-1;i>=0;i--)if(n in this.scopes[i])return this.scopes[i][n];if(n in this.vars)return this.vars[n];throw new RostError("Unknown variable: "+n);}
    set(n,v,local=false,create=false){if(local){this.scopes[this.scopes.length-1][n]=v;return;}if(create){if(n in this.vars||this.scopes.some(s=>n in s))throw new RostError("'"+n+"' already exists; use change");this.vars[n]=v;return;}for(let i=this.scopes.length-1;i>=0;i--)if(n in this.scopes[i]){this.scopes[i][n]=v;return;}if(n in this.vars){this.vars[n]=v;return;}throw new RostError("'"+n+"' does not exist; use make or Local");}
    call(n,a){
      const b={length:x=>x.length,text:x=>String(x),number:x=>Number(x),abs:Math.abs,min:Math.min,max:Math.max,sum:x=>x.reduce((p,c)=>p+c,0),round:Math.round,floor:Math.floor,ceil:Math.ceil,sqrt:Math.sqrt,random:()=>Math.random(),random_int:(x,y)=>Math.floor(Math.random()*(y-x+1))+x,append:(x,v)=>(x.push(v),x),pop:(x,i=-1)=>x.splice(i<0?x.length+i:i,1)[0],str:x=>String(x),int:x=>Math.trunc(Number(x)),float:x=>Number(x),bool:x=>Boolean(x),range:(n)=>Array.from({length:Math.max(0,Math.min(100000,n))},(_,i)=>i),Time:()=>new Date().toISOString()};
      if(n in b)return b[n](...a);
      if(!(n in this.funcs))throw new RostError("Unknown function: "+n);
      const f=this.funcs[n];if(a.length!==f.params.length)throw new RostError(n+"() expects "+f.params.length+" argument(s)");
      const scope=Object.fromEntries(f.params.map((p,i)=>[p,a[i]]));this.scopes.push(scope);
      try{this.exec(f.body);}catch(e){if(e&&e.__return)return e.value;throw e;}finally{this.scopes.pop();}
      return null;
    }
    eval(s){return new Expr(s,this).parse();}
    parse(src){
      const lines=src.replace(/\r/g,"").split("\n");let i=0;
      const block=(top=false)=>{const out=[];while(i<lines.length){let raw=lines[i],line=raw.trim(),ln=++i;if(!line||line.startsWith("#"))continue;if(line==="}"){if(top)throw new RostError("Unexpected '}' at line "+ln);return out;}
        let m;
        if((m=line.match(/^(when|if)\s+(.+)\s*\{$/))){const yes=block(),no=[];if(i<lines.length&&/^(otherwise|else)\s*\{$/.test(lines[i].trim())){i++;no.push(...block());}out.push({k:"if",e:m[2],yes,no,ln});continue;}
        if((m=line.match(/^(repeat|while)\s+(.+)\s*\{$/))){out.push({k:m[1],e:m[2],body:block(),ln});continue;}
        if((m=line.match(/^(action|def)\s+([A-Za-z_]\w*)\s*\((.*?)\)\s*\{$/))){out.push({k:"def",n:m[2],p:m[3].trim()?m[3].split(",").map(x=>x.trim()):[],body:block(),ln});continue;}
        if((m=line.match(/^for\s+([A-Za-z_]\w*)\s+in\s+(.+)\s*\{$/))){out.push({k:"for",n:m[1],e:m[2],body:block(),ln});continue;}
        if(line==="try {"){const body=block();let handler=[];let name="error";if(i<lines.length&&(m=lines[i].trim().match(/^except(?:\s+([A-Za-z_]\w*))?\s*\{$/))){i++;name=m[1]||name;handler=block();}out.push({k:"try",body,handler,name,ln});continue;}
        if((m=line.match(/^class\s+([A-Za-z_]\w*)\s*\{$/))){out.push({k:"class",n:m[1],body:block(),ln});continue;}
        out.push({k:"line",s:line,ln});
      }if(!top)throw new RostError("Missing closing '}'");return out;};
      return block(true);
    }
    exec(nodes){for(const n of nodes){if(++this.steps>200000)throw new RostError("Execution step limit reached");try{
      if(n.k==="if"){this.scopes.push({});try{this.exec(this.eval(n.e)?n.yes:n.no);}finally{this.scopes.pop();}}
      else if(n.k==="def"){if(this.funcs[n.n])throw new RostError("Function already exists: "+n.n);this.funcs[n.n]={params:n.p,body:n.body};}
      else if(n.k==="repeat"||n.k==="while"){let count=n.k==="repeat"?this.eval(n.e):100000;if(n.k==="repeat"&&(!Number.isInteger(count)||count<0||count>100000))throw new RostError("repeat expects an integer from 0 to 100000");for(let j=0;j<count;j++){if(n.k==="while"&&!this.eval(n.e))break;this.scopes.push({});try{this.exec(n.body);}finally{this.scopes.pop();}}}
      else if(n.k==="for"){const values=this.eval(n.e);if(!values||!values[Symbol.iterator])throw new RostError("for expects an iterable");for(const v of values){this.scopes.push({[n.n]:v});try{this.exec(n.body);}finally{this.scopes.pop();}}}
      else if(n.k==="try"){try{this.scopes.push({});try{this.exec(n.body);}finally{this.scopes.pop();}}catch(e){if(!n.handler.length)throw e;this.scopes.push({[n.name]:String(e.message||e)});try{this.exec(n.handler);}finally{this.scopes.pop();}}}
      else if(n.k==="class")throw new RostError("Class support is not yet ported to the JavaScript runtime");
      else this.line(n.s);
    }catch(e){if(e&&e.__return)throw e;throw new RostError("Line "+n.ln+": "+(e.message||e));}}}
    line(s){
      let m;
      if((m=s.match(/^(?:say|print)\s+(.+)$/))){this.out(this.eval(m[1]));return;}
      if((m=s.match(/^print\((.*)\)$/))){this.out(this.eval(m[1]));return;}
      if((m=s.match(/^(?:make|let)\s+([A-Za-z_]\w*)\s*=\s*(.+)$/))){this.set(m[1],this.eval(m[2]),false,true);return;}
      if((m=s.match(/^change\s+([A-Za-z_]\w*)\s*=\s*(.+)$/))){this.set(m[1],this.eval(m[2]));return;}
      if((m=s.match(/^Local\s+([A-Za-z_]\w*)\s*=\s*(.+)$/))){this.set(m[1],this.eval(m[2]),true);return;}
      if((m=s.match(/^Period\s+([A-Za-z_]\w*)\s*=\s*(\d+(?:\.\d+)?)\s*(ms|s|m|h|d)$/))){const f={ms:.001,s:1,m:60,h:3600,d:86400};this.set(m[1],Number(m[2])*f[m[3]],true);return;}
      if((m=s.match(/^return(?:\s+(.+))?$/)))throw {__return:true,value:m[1]?this.eval(m[1]):null};
      if((m=s.match(/^ask\s+([A-Za-z_]\w*)\s*=\s*(.+)$/))){const prompt=this.str(this.eval(m[2]));this.set(m[1],this.io.input?this.io.input(prompt):"",false,true);return;}
      if(s==="stop"||s==="skip")throw new RostError(s+" is not yet supported in this runtime");
      if((m=s.match(/^([A-Za-z_]\w*)\s*=\s*(.+)$/))){const exists=this.has(m[1]);this.set(m[1],this.eval(m[2]),false,!exists);return;}
      if(/^[A-Za-z_]\w*\s*\(.*\)$/.test(s)){this.eval(s);return;}
      throw new RostError("Unknown command: "+s.split(/\s/)[0]);
    }
    has(n){return n in this.vars||this.scopes.some(s=>n in s);}
    run(source){this.vars={};this.scopes=[];this.funcs={};this.steps=0;this.exec(this.parse(source));}
  }
  root.RostRuntime=RostRuntime;
})(typeof window!=="undefined"?window:globalThis);
