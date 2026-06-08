'use client';

import { useQuery } from '@tanstack/react-query';
import { 
  getSummaryStats, 
  getTargets, 
  getActiveAlerts, 
  getDossiers, 
  getTemporalSeries 
} from '@/lib/api';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getSummaryStats,
    refetchInterval: 15000, // 15 segundos (Real-time Warroom)
    staleTime: 5000,
  });
}

export function useCandidates(limit = 10) {
  return useQuery({
    queryKey: ['candidates', limit],
    queryFn: () => getTargets(limit),
    refetchInterval: 30000, // 30 segundos
    staleTime: 10000,
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

export function useTemporalSeries() {
  return useQuery({
    queryKey: ['temporal-series'],
    queryFn: getTemporalSeries,
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useGeoUf() {
  return useQuery({
    queryKey: ['geo-uf'],
    queryFn: async () => {
      const { fetchApi } = await import('@/lib/api');
      return fetchApi('/api/v1/geo/uf');
    },
    refetchInterval: 120000,
    staleTime: 60000,
  });
}

export function useDemographics() {
  return useQuery({
    queryKey: ['demographics'],
    queryFn: async () => {
      const { fetchApi } = await import('@/lib/api');
      return fetchApi('/api/v1/analytics/demographics');
    },
    refetchInterval: 120000,
    staleTime: 60000,
  });
}
