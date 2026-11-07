import { vi } from '../config';

export default function Badge({value}) { return <span className={`badge ${value}`}>{vi[value] || value}</span> }
