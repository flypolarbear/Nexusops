import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface DiagramConfig {
  id: string
  name: string
  type: 'drawio' | 'svg' | 'png'
  content: string // Base64 encoded content or URL
  lastUpdated: string
  uploadedBy: string
}

interface DiagramState {
  diagrams: DiagramConfig[]
  activeDiagramId: string | null
  addDiagram: (diagram: DiagramConfig) => void
  updateDiagram: (id: string, content: string) => void
  removeDiagram: (id: string) => void
  setActiveDiagram: (id: string | null) => void
  getActiveDiagram: () => DiagramConfig | null
}

// Helper to encode SVG to data URL (handles Unicode properly)
function svgToDataUrl(svg: string): string {
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

// Default SVG content (without Unicode symbols that cause issues)
const defaultSvgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#f8fafc"/>
      <stop offset="100%" style="stop-color:#e2e8f0"/>
    </linearGradient>
  </defs>
  <rect width="800" height="400" fill="url(#bg)"/>
  <text x="400" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#1e293b">Global Infrastructure Overview</text>
  <g transform="translate(100, 80)">
    <rect x="0" y="0" width="150" height="120" rx="8" fill="#ffffff" stroke="#22c55e" stroke-width="2"/>
    <text x="75" y="25" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#1e293b">US East</text>
    <text x="75" y="45" text-anchor="middle" font-family="Arial" font-size="10" fill="#64748b">AWS</text>
    <circle cx="75" cy="75" r="20" fill="#dcfce7" stroke="#22c55e" stroke-width="2"/>
    <text x="75" y="80" text-anchor="middle" font-family="Arial" font-size="14" fill="#16a34a">OK</text>
    <text x="75" y="110" text-anchor="middle" font-family="Arial" font-size="9" fill="#64748b">3 Clusters</text>
  </g>
  <g transform="translate(100, 220)">
    <rect x="0" y="0" width="150" height="120" rx="8" fill="#ffffff" stroke="#22c55e" stroke-width="2"/>
    <text x="75" y="25" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#1e293b">US West</text>
    <text x="75" y="45" text-anchor="middle" font-family="Arial" font-size="10" fill="#64748b">AWS</text>
    <circle cx="75" cy="75" r="20" fill="#dcfce7" stroke="#22c55e" stroke-width="2"/>
    <text x="75" y="80" text-anchor="middle" font-family="Arial" font-size="14" fill="#16a34a">OK</text>
    <text x="75" y="110" text-anchor="middle" font-family="Arial" font-size="9" fill="#64748b">2 Clusters</text>
  </g>
  <g transform="translate(325, 80)">
    <rect x="0" y="0" width="150" height="120" rx="8" fill="#ffffff" stroke="#eab308" stroke-width="2"/>
    <text x="75" y="25" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#1e293b">EU West</text>
    <text x="75" y="45" text-anchor="middle" font-family="Arial" font-size="10" fill="#64748b">GCP</text>
    <circle cx="75" cy="75" r="20" fill="#fef3c7" stroke="#eab308" stroke-width="2"/>
    <text x="75" y="80" text-anchor="middle" font-family="Arial" font-size="14" fill="#ca8a04">WARN</text>
    <text x="75" y="110" text-anchor="middle" font-family="Arial" font-size="9" fill="#64748b">2 Clusters</text>
  </g>
  <g transform="translate(325, 220)">
    <rect x="0" y="0" width="150" height="120" rx="8" fill="#ffffff" stroke="#22c55e" stroke-width="2"/>
    <text x="75" y="25" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#1e293b">EU Central</text>
    <text x="75" y="45" text-anchor="middle" font-family="Arial" font-size="10" fill="#64748b">AWS</text>
    <circle cx="75" cy="75" r="20" fill="#dcfce7" stroke="#22c55e" stroke-width="2"/>
    <text x="75" y="80" text-anchor="middle" font-family="Arial" font-size="14" fill="#16a34a">OK</text>
    <text x="75" y="110" text-anchor="middle" font-family="Arial" font-size="9" fill="#64748b">1 Cluster</text>
  </g>
  <g transform="translate(550, 140)">
    <rect x="0" y="0" width="150" height="120" rx="8" fill="#ffffff" stroke="#ef4444" stroke-width="2"/>
    <text x="75" y="25" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#1e293b">Asia Pacific</text>
    <text x="75" y="45" text-anchor="middle" font-family="Arial" font-size="10" fill="#64748b">AliCloud</text>
    <circle cx="75" cy="75" r="20" fill="#fee2e2" stroke="#ef4444" stroke-width="2"/>
    <text x="75" y="80" text-anchor="middle" font-family="Arial" font-size="12" fill="#dc2626">ERR</text>
    <text x="75" y="110" text-anchor="middle" font-family="Arial" font-size="9" fill="#64748b">2 Clusters</text>
  </g>
  <g transform="translate(550, 320)">
    <circle cx="10" cy="10" r="6" fill="#dcfce7" stroke="#22c55e" stroke-width="1"/>
    <text x="22" y="14" font-family="Arial" font-size="9" fill="#64748b">Healthy</text>
    <circle cx="70" cy="10" r="6" fill="#fef3c7" stroke="#eab308" stroke-width="1"/>
    <text x="82" y="14" font-family="Arial" font-size="9" fill="#64748b">Warning</text>
    <circle cx="130" cy="10" r="6" fill="#fee2e2" stroke="#ef4444" stroke-width="1"/>
    <text x="142" y="14" font-family="Arial" font-size="9" fill="#64748b">Critical</text>
  </g>
  <line x1="175" y1="140" x2="175" y2="220" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4"/>
  <line x1="400" y1="140" x2="400" y2="220" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4"/>
  <line x1="250" y1="140" x2="325" y2="140" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4"/>
  <line x1="475" y1="200" x2="550" y2="200" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4"/>
</svg>`

// Mock default diagram (a simple SVG for demo)
const defaultDiagram: DiagramConfig = {
  id: 'default-infra',
  name: 'Global Infrastructure',
  type: 'svg',
  content: svgToDataUrl(defaultSvgContent),
  lastUpdated: new Date().toISOString(),
  uploadedBy: 'system',
}

export const useDiagramStore = create<DiagramState>()(
  persist(
    (set, get) => ({
      diagrams: [defaultDiagram],
      activeDiagramId: 'default-infra',
      addDiagram: (diagram) =>
        set((state) => ({
          diagrams: [...state.diagrams, diagram],
        })),
      updateDiagram: (id, content) =>
        set((state) => ({
          diagrams: state.diagrams.map((d) =>
            d.id === id ? { ...d, content, lastUpdated: new Date().toISOString() } : d
          ),
        })),
      removeDiagram: (id) =>
        set((state) => ({
          diagrams: state.diagrams.filter((d) => d.id !== id),
          activeDiagramId: state.activeDiagramId === id ? null : state.activeDiagramId,
        })),
      setActiveDiagram: (id) => set({ activeDiagramId: id }),
      getActiveDiagram: () => {
        const state = get()
        return state.diagrams.find((d) => d.id === state.activeDiagramId) || null
      },
    }),
    {
      name: 'nexusops-diagrams',
    }
  )
)
