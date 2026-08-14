import { useOutletContext } from 'react-router-dom'

export type ShellContext = { asOf: string }

export function useAsOf(): string {
  return useOutletContext<ShellContext>().asOf
}
