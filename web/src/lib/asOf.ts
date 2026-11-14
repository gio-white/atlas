import { useOutletContext } from 'react-router-dom'

export type ShellContext = {
  asOf: string
  displayName: string
  /** Saves the name on this device and updates every page that shows it. */
  setDisplayName: (name: string) => void
  /** Tasks in the Inbox still to sort, for the Inbox tab's badge. */
  inboxCount: number
  openLog: () => void
}

export function useShell(): ShellContext {
  return useOutletContext<ShellContext>()
}

export function useAsOf(): string {
  return useShell().asOf
}
