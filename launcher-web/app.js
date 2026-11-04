(() => {
 const $=id=>document.getElementById(id), editor=$("editor"), output=$("output"), file=$("file");
 let currentName="Untitled.rost", pendingInput=null;
 const status=s=>$("status").textContent=s;
 const log=s=>{output.textContent+=String(s)+"\n";output.scrollTop=output.scrollHeight;};
 const setName=n=>{currentName=n;$("filename").textContent=n;};
 $("new").onclick=()=>{editor.value="";setName("Untitled.rost");output.textContent="New file.";status("New file");};
 $("open").onclick=()=>file.click();
 file.onchange=async()=>{const f=file.files?.[0];if(!f)return;editor.value=await f.text();setName(f.name);status("Opened");file.value="";};
 $("save").onclick=()=>{const blob=new Blob([editor.value],{type:"text/plain;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=currentName.endsWith(".rost")?currentName:currentName+".rost";a.click();URL.revokeObjectURL(url);status("Saved");};
 $("run").onclick=()=>{output.textContent="";pendingInput=null;try{const runtime=new RostRuntime({print:log,input:prompt=>{pendingInput=prompt;log(prompt);return $("stdin").value;}});runtime.run(editor.value);status("Finished");}catch(e){log("RostLang error: "+e.message);status("Error");}};
 $("clear").onclick=()=>output.textContent="";
 $("send").onclick=()=>{if(pendingInput!==null){log($("stdin").value);pendingInput=null;}else log("No input requested by the running program.");};
 editor.addEventListener("keydown",e=>{if(e.key==="Tab"){e.preventDefault();const a=editor.selectionStart,b=editor.selectionEnd;editor.setRangeText("    ",a,b,"end");}});
})();