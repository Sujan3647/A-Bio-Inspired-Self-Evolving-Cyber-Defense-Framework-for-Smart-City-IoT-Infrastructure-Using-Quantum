/**
 * ImmunoGrid — Simulation State Store
 * Zustand store for live simulation state shared across components.
 */

import { create } from 'zustand'

interface AttackEvent {
  id: string
  type: string
  sector: string
  severity: string
  detected: boolean
  timestamp: string
}

interface SimulationState {
  running: boolean
  devicesActive: number
  messagesPerSecond: number
  attacksPerMinute: number
  recentAttacks: AttackEvent[]
  totalAttacksToday: number
  detectionRate: number
  setRunning: (running: boolean) => void
  setDevicesActive: (count: number) => void
  addAttackEvent: (event: AttackEvent) => void
  updateStats: (stats: Partial<SimulationState>) => void
  reset: () => void
}

export const useSimulationStore = create<SimulationState>((set) => ({
  running: false,
  devicesActive: 0,
  messagesPerSecond: 0,
  attacksPerMinute: 0,
  recentAttacks: [],
  totalAttacksToday: 0,
  detectionRate: 97.3,

  setRunning: (running) => set({ running }),
  setDevicesActive: (count) => set({ devicesActive: count }),

  addAttackEvent: (event) =>
    set((state) => ({
      recentAttacks: [event, ...state.recentAttacks].slice(0, 50),
      totalAttacksToday: state.totalAttacksToday + 1,
    })),

  updateStats: (stats) => set(stats),

  reset: () =>
    set({
      running: false,
      devicesActive: 0,
      messagesPerSecond: 0,
      attacksPerMinute: 0,
      recentAttacks: [],
      totalAttacksToday: 0,
    }),
}))
