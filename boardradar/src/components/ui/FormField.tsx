import type { ReactNode } from 'react';
export default function FormField({id,label,labelHidden=false,hint,error,children}:{id:string;label:string;labelHidden?:boolean;hint?:string;error?:string;children:ReactNode}){
 return <div className="ui-field"><label className={labelHidden?'sr-only':undefined} htmlFor={id}>{label}</label>{children}{hint&&<small id={id+'-hint'}>{hint}</small>}{error&&<small id={id+'-error'} role="alert">{error}</small>}</div>;
}
