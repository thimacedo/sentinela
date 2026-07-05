/**
 * Tipos compartilhados para o frontend do Sentinela
 * Centraliza todas as interfaces e types para evitar duplicação
 */

// ============================================
// TIPOS DE ALERTAS
// ============================================

export interface Alert {
  id: string;
  data_coleta: string;
  candidatos?: {
    username: string;
    nome_completo?: string;
    cargo?: string;
    partido?: string;
  };
  candidato_id?: string;
  categoria_ia: 'CRITICO' | 'ELEVADO' | 'MEDIO' | 'BAIXO' | string;
  texto_bruto?: string;
  autor_username?: string;
  post_shortcode?: string;
  plataforma?: 'INSTAGRAM' | 'TWITTER' | string;
  is_hate?: boolean;
  is_bot?: boolean;
  analise_pericial?: string;
  tier_used?: number;
}

export type AlertLevel = 'critical' | 'high' | 'medium' | 'low';

// ============================================
// TIPOS DE ESTATÍSTICAS
// ============================================

export interface DashboardStats {
  resiliencia?: number;
  total_amostra?: number;
  total_alertas?: number;
  total_monitorados?: number;
  total_classificados?: number;
  total_pendentes?: number;
  health_score?: number;
}

// ============================================
// TIPOS DE EVENTOS DA TIMELINE
// ============================================

export interface TimelineEvent {
  id: string;
  timestamp: string;
  candidate: string;
  title: string;
  description: string;
  alertLevel: AlertLevel;
  postsCount: number;
  engagementMetric: number;
}

// ============================================
// TIPOS DE CANDIDATOS
// ============================================

export interface Candidate {
  username: string;
  nome_completo?: string;
  cargo?: string;
  partido?: string;
  estado?: string;
  identidade_validada?: boolean;
  status_monitoramento?: 'ATIVO' | 'DESATIVADO' | 'ANALISE_SOLICITADA' | string;
  motivo_desativacao?: string;
  avatar_url?: string;
  bio?: string;
  seguidores?: number;
  data_criacao?: string;
}

// ============================================
// TIPOS DE COMENTÁRIOS
// ============================================

export interface Comment {
  id_externo: string;
  texto_bruto: string;
  autor_username?: string;
  data_publicacao?: string;
  data_coleta?: string;
  candidato_id?: string;
  post_shortcode?: string;
  plataforma?: string;
  categoria_ia?: string;
  processado_ia?: boolean;
  confidence?: number;
  analise_linguistica?: any;
  is_hate?: boolean;
  is_bot?: boolean;
  bot_pattern?: string;
}

// ============================================
// TIPOS DE RESPOSTAS DA API
// ============================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
}

// ============================================
// TIPOS DE FILTROS
// ============================================

export interface FilterParams {
  page?: number;
  perPage?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  search?: string;
  platform?: string;
  category?: string;
  dateFrom?: string;
  dateTo?: string;
  status?: string;
}
