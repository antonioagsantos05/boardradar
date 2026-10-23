import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
const local=resolve('..','.tools','python-3.13.7','python.exe');
const python=process.env.PYTHON_EXECUTABLE||(existsSync(local)?local:process.platform==='win32'?'python':'python3');
for(const [program,args] of [
 [python,['scripts/validate-poc-data.py']],
 [process.execPath,['--import','tsx','--test','tests/poc-v3.test.ts']],
 [python,['-m','unittest','discover','-s','chatbot','-p','test_poc_v3.py','-v']],
]){
 const result=spawnSync(program,args,{windowsHide:true,stdio:'inherit',env:{...process.env,PYTHONUTF8:'1'}});
 if(result.error)console.error(result.error.message);
 if(result.status!==0){process.exitCode=result.status??1;break;}
}
