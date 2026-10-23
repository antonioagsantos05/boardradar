import type { ReactNode } from 'react';
export function StatusMessage({children,error=false}:{children:ReactNode;error?:boolean}){
 return <p className={'ui-status '+(error?'ui-status-error':'')} role={error?'alert':'status'}>{children}</p>;
}
export function EmptyState({title,children}:{title:string;children?:ReactNode}){
 return <div className="ui-empty"><h3>{title}</h3>{children&&<p>{children}</p>}</div>;
}
export function LoadingSkeleton({label='Carregando…'}:{label?:string}){
 return <div className="ui-loading" role="status"><span className="sr-only">{label}</span><span aria-hidden="true"/><span aria-hidden="true"/><span aria-hidden="true"/></div>;
}
