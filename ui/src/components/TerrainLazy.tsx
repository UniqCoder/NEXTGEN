import { lazy, Suspense } from 'react'
import type { TerrainProps } from './Terrain'

const Model = lazy(() => import('./Terrain').then((m) => ({ default: m.Terrain })))

export function Terrain(props: TerrainProps) {
  return <Suspense fallback={null}><Model {...props} /></Suspense>
}
