import type { ComponentPropsWithRef } from 'react';
export function buttonClass(variant:'primary'|'secondary'|'quiet'='primary'){
 return `ui-button ${variant==='primary'?'ui-button-primary':variant==='secondary'?'ui-button-secondary':'ui-button-quiet'}`;
}
export default function Button({variant='primary',className='',type='button',...props}:ComponentPropsWithRef<'button'>&{variant?:'primary'|'secondary'|'quiet'}){
 return <button {...props} type={type} className={buttonClass(variant)+' '+className}/>;
}
