'use client';

import { useQuery } from '@tanstack/react-query';
import { getSummaryStats, getTargets, getActiveAlerts, getDossiers } from '@/lib/api';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getSummaryStats,
    refetchInterval: 60000, // 1 minuto
    staleTime: 30000,
  });
}

export function useCandidates(limit = 10) {
  return useQuery({
    queryKey: ['candidates', limit],
    queryFn: () => getTargets(limit),
    refetchInterval: 120000, // 2 minutos
    staleTime: 60000,
  });
}

export function useAlerts(limit = 20) {
  return useQuery({
    queryKey: ['alerts', limit],
    queryFn: () => getActiveAlerts(limit),
    refetchInterval: 30000, // 30 segundos - alertas frequentes
    staleTime: 15000,
  });
}

export function useDossiers(candidatoId?: string) {
  return useQuery({
    queryKey: ['dossiers', candidatoId],
    queryFn: () => getDossiers(candidatoId),
    refetchInterval: 300000, // 5 minutos
    staleTime: 120000,
  });
}
