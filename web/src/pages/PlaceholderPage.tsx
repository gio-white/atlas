import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription className="mt-1">
            This section ships with the matching domain cycle.
          </CardDescription>
        </div>
      </CardHeader>
    </Card>
  )
}
