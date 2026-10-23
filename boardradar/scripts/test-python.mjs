import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
const bundled=resolve('..','.tools','python-3.13.7','python.exe');
const python=process.env.PYTHON_EXECUTABLE||(existsSync(bundled)?bundled:process.platform==='win32'?'python':'python3');
const result=spawnSync(python,['-m','unittest','discover','-s','chatbot','-p','test_*.py','-v'],{stdio:'inherit',windowsHide:true,env:{...process.env,PYTHONUTF8:'1'}});
if(result.error)console.error(result.error.message);
process.exitCode=result.status??1;
