import { Plus } from 'lucide-react'
import { useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'

import { LibraryTable } from '@/components/entertainment/LibraryTable'
import { SectionHeader, useCarriedSearch } from '@/components/entertainment/SectionHeader'
import { TitleDialog } from '@/components/entertainment/TitleDialog'
import { useLibrary } from '@/components/entertainment/useLibrary'
import { PageLoading, PageUnavailable } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import type { EntertainmentTitle } from '@/lib/api'
import { categoryFor, categoryFromPath, inCategory } from '@/lib/entertainment'

export function EntertainmentCategoryPage() {
  const { category: raw } = useParams()
  const category = categoryFromPath(raw)
  const search = useCarriedSearch()
  const { titles, topics, error, refresh } = useLibrary()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<EntertainmentTitle | null>(null)

  if (category === null) return <Navigate to={{ pathname: '/entertainment', search }} replace />
  const meta = categoryFor(category)
  if (error !== null) return <PageUnavailable title={meta.label} message={error} />
  if (titles === null) return <PageLoading />

  const count = titles.filter((title) => inCategory(title, category)).length

  function openDialog(title: EntertainmentTitle | null) {
    setEditing(title)
    setDialogOpen(true)
  }

  return (
    <div className="flex flex-col gap-6">
      <SectionHeader
        icon={category}
        title={meta.label}
        description={`${meta.tagline} ${count} saved.`}
      >
        <Button type="button" onClick={() => openDialog(null)}>
          <Plus className="size-4" aria-hidden />
          Add
        </Button>
      </SectionHeader>
      <LibraryTable
        key={category}
        titles={titles}
        category={category}
        onOpen={openDialog}
        onRefresh={refresh}
      />
      <TitleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing}
        defaultKind={meta.kinds[0]}
        topics={topics}
        takenSlugs={titles.map((title) => title.slug)}
        onSaved={refresh}
      />
    </div>
  )
}
