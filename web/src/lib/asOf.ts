import { useOutletContext } from 'react-router-dom'

export type ShellContext = {
  asOf: string
  displayName: string
  openLog: () => void
}

export function useShell(): ShellContext {
  return useOutletContext<ShellContext>()
}

export function useAsOf(): string {
  return useShell().asOf
}
