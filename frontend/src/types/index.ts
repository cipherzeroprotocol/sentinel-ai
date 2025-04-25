/**
 * TypeScript definitions for Sentinel AI
 */

// ==========================================
// Base and Common Types
// ==========================================

export type Timestamp = string; // ISO format timestamp
export type RiskLevel = 'low' | 'medium' | 'high' | 'very_high' | 'unknown';
export type RiskScore = number; // 0-100 scale
export type ConfidenceScore = number; // 0-10 scale
export type AnalysisType = 'ico' | 'rugpull' | 'money_laundering' | 'mixer' | 'dusting' | 'wallet' | 'transaction' | 'all';
export type TargetType = 'address' | 'token';

export interface Evidence {
  description: string;
  confidence?: number;
  [key: string]: any; // Additional evidence fields
}

export interface Pattern {
  name: string;
  description: string;
  score: number;
  evidence?: Evidence | Evidence[];
}

export interface ProgramInteraction {
  program_id: string;
  program_name?: string;
  count: number;
  first_interaction: Timestamp;
  last_interaction: Timestamp;
}

export interface EntityInfo {
  address: string;
  name?: string;
  tags?: string[];
  risk_score?: RiskScore;
  risk_level?: RiskLevel;
  description?: string;
}

export interface Transaction {
  signature: string;
  block_time: Timestamp;
  slot?: number;
  success: boolean;
  fee: number;
  fee_payer: string;
  amount?: number;
  amount_usd?: number;
  token_address?: string;
  token_symbol?: string;
  sender: {
    wallet: string;
    is_contract?: boolean;
    labels?: string[];
  };
  receiver: {
    wallet: string;
    is_contract?: boolean;
    labels?: string[];
  };
  program_id?: string;
  program_name?: string;
  instructions?: any[];
  inner_instructions?: any[];
}

export interface TokenData {
  mint: string;
  name: string;
  symbol: string;
  decimals: number;
  supply: number;
  supply_usd?: number;
  creator?: string;
  mint_authority?: string;
  freeze_authority?: string;
  image_uri?: string;
  website?: string;
  twitter?: string;
  description?: string;
  tags?: string[];
  price_usd?: number;
  market_cap?: number;
}

// ==========================================
// Analysis Results Interfaces
// ==========================================

interface BaseAnalysisResult {
  timestamp: Timestamp;
  target: string;
  target_type: TargetType;
  analysis_type: AnalysisType;
  model?: string; // AI model used
}

// ICO Analysis
export interface ICOAnalysisResult extends BaseAnalysisResult {
  token_data: TokenData;
  creator_data: {
    creator_address: string;
    other_tokens_count: number;
    is_suspicious: boolean;
    created_tokens?: any[];
  };
  funding_flow: {
    total_raised: number;
    investor_count: number;
    distribution_fairness_score?: number;
    distribution_data?: any;
  };
  patterns: {
    detected_patterns: Pattern[];
  };
  team_analysis?: {
    known_team_members: number;
    transparency_score: number;
    total_team_holdings_pct: number;
  };
  risk_assessment: {
    risk_score: RiskScore;
    risk_level: RiskLevel;
    risk_factors: string[];
    confidence: ConfidenceScore;
  };
  visualizations?: {
    funding_distribution?: string; // Path or base64 image
    token_price_chart?: string;
  };
}

// Rugpull Analysis
export interface RugpullAnalysisResult extends BaseAnalysisResult {
  token_data: TokenData;
  token_mint: string;
  creator_analysis: {
    creator_address: string;
    other_tokens_count: number;
    is_suspicious: boolean;
    previous_rugpulls?: number;
  };
  holder_analysis: {
    holder_count: number;
    top_10_concentration: number;
    top_holders: Array<{
      address: string;
      percentage: number;
      tags?: string[];
    }>;
  };
  liquidity_data: {
    total_liquidity_usd: number;
    liquidity_to_mcap_ratio: number;
    locked_percentage: number;
    lock_expiration?: Timestamp;
  };
  risk_factors: string[];
  risk_score: RiskScore;
  rugcheck_analysis?: {
    risk_score: number;
    flags: string[];
  };
  patterns: {
    detected_patterns: Pattern[];
  };
  is_rugpull?: boolean;
  visualizations?: {
    holder_distribution?: string;
    liquidity_chart?: string;
  };
}

// Money Laundering Analysis
export interface MoneyLaunderingResult extends BaseAnalysisResult {
  transaction_patterns: {
    layering_detected: boolean;
    smurfing_detected: boolean;
    round_trip_detected: boolean;
    obfuscation_techniques: string[];
  };
  fund_flow: {
    source_entities: EntityInfo[];
    destination_entities: EntityInfo[];
    total_value_usd: number;
    flow_complexity_score: number;
    multi_hop_count: number;
  };
  counterparties: {
    high_risk_entities: EntityInfo[];
    relationships: Record<string, string>;
  };
  mixer_interaction: {
    detected: boolean;
    mixer_addresses?: string[];
    mixed_amount_usd?: number;
  };
  risk_assessment: {
    risk_score: RiskScore;
    risk_level: RiskLevel;
    confidence: ConfidenceScore;
    laundering_stage?: 'placement' | 'layering' | 'integration';
  };
  patterns: {
    detected_patterns: Pattern[];
  };
  is_money_laundering?: boolean;
  visualizations?: {
    fund_flow_diagram?: string;
    heatmap?: string;
  };
}

// Mixer Analysis
export interface MixerAnalysisResult extends BaseAnalysisResult {
  operational_pattern: {
    mixing_technique: string;
    anonymity_level: number;
    transaction_structure: string;
  };
  user_behavior: {
    deposit_patterns: string[];
    withdrawal_patterns: string[];
    unique_users: number;
    recurring_users: number;
  };
  volume_analysis: {
    total_volume_usd: number;
    average_transaction_usd: number;
    denomination_patterns: string[];
    temporal_patterns: string[];
    growth_trend: string;
  };
  mixer_characteristics: string[];
  comparison: {
    similarity_to_known_mixers: number;
    sophistication_level: number;
    unique_features: string[];
  };
  transactions: Transaction[];
  is_known_mixer: boolean;
  confidence_score: ConfidenceScore;
  visualizations?: {
    volume_chart?: string;
    user_network?: string;
  };
}

// Authentication Types
export interface User {
  id: string;
  name?: string;
  email: string;
  image?: string;
  role: UserRole;
  apiTokens?: ApiToken[];
  preferences?: UserPreferences;
  createdAt: string;
  updatedAt: string;
}

export enum UserRole {
  ADMIN = 'ADMIN',
  ANALYST = 'ANALYST',
  USER = 'USER'
}

export interface ApiToken {
  id: string;
  name: string;
  token: string;
  createdAt: string;
  lastUsedAt?: string;
  expiresAt?: string;
}

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  dashboardLayout?: string;
  defaultAnalysisType?: string;
  notifications?: {
    email?: boolean;
    inApp?: boolean;
  };
  visualizations?: {
    preferredChartType?: string;
    showRiskMetrics?: boolean;
  };
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Dusting Analysis
export interface DustingAnalysisResult extends BaseAnalysisResult {
  risk_assessment: {
    risk_score: RiskScore;
    risk_level: RiskLevel;
    severity: number; // 1-10
  };
  dusting_pattern: {
    timing: string;
    frequency: string;
    amount_characteristics: string;
    target_selection_method: string;
    campaign_scale: string;
  };
  source_analysis: {
    attacker_addresses: string[];
    sophistication_level: string;
    identity_clues: string[];
  };
  purpose_assessment: {
    likely_purpose: string;
    targeting_type: 'targeted' | 'broad-spectrum';
    follow_up_activities: string[];
  };
  similar_addresses: {
    related_patterns: string[];
    poisoning_attempts: string[];
    attack_network: string[];
  };
  poisoning_attempts: Array<{
    source_address: string;
    similarity_type: string;
    similarity_score: number;
    timestamp: Timestamp;
    tokens?: string[];
  }>;
  dusting_campaigns: Array<{
    campaign_id: string;
    source_address: string;
    target_count: number;
    total_dust_value_usd: number;
    first_seen: Timestamp;
    last_seen: Timestamp;
  }>;
  visualizations?: {
    campaign_timeline?: string;
    target_distribution?: string;
  };
}

// Wallet Profiling
export interface WalletProfileResult extends BaseAnalysisResult {
  classification: {
    primary_type: string;
    primary_confidence: ConfidenceScore;
    secondary_types?: Array<{
      type: string;
      confidence: ConfidenceScore;
    }>;
    reasoning: string;
  };
  features: {
    total_tx_count: number;
    total_volume_usd: number;
    average_tx_value: number;
    active_since: Timestamp;
    last_activity: Timestamp;
    token_diversity: number;
    program_interactions: ProgramInteraction[];
  };
  behavior: {
    dominant_activities: string[];
    unusual_patterns: string[];
    comparative_analysis: string;
  };
  risk_assessment: {
    risk_score: RiskScore;
    risk_level: RiskLevel;
    high_risk_interactions: string[];
  };
  visualizations?: {
    activity_chart?: string;
    program_usage?: string;
  };
}

// Transaction Analysis
export interface TransactionAnalysisResult extends BaseAnalysisResult {
  transaction_count: number;
  transaction_overview: {
    recent_transactions: Transaction[];
    avg_transaction_value: number;
    total_volume_usd: number;
  };
  entities: {
    involved_entities: EntityInfo[];
    frequently_interacted: EntityInfo[];
  };
  financial_aspects: {
    unusual_amounts: boolean;
    token_diversity: number;
    value_concentration: number;
  };
  technical_details: {
    common_programs: ProgramInteraction[];
    complex_transactions_count: number;
  };
  patterns: Record<string, Pattern>;
  suspicion_score: RiskScore;
  cross_chain_transfers: Array<{
    destination_chain: string;
    amount_usd: number;
    timestamp: Timestamp;
    destination_address?: string;
  }>;
  risk_assessment: {
    overall_risk_score: RiskScore;
    flagged_transactions: string[];
  };
  visualizations?: {
    transaction_timeline?: string;
    entity_interaction_network?: string;
  };
}

// Combined Analysis Result
export type AnalysisResult = 
  | ICOAnalysisResult 
  | RugpullAnalysisResult 
  | MoneyLaunderingResult 
  | MixerAnalysisResult 
  | DustingAnalysisResult
  | WalletProfileResult
  | TransactionAnalysisResult;

// ==========================================
// Security Report Interfaces
// ==========================================

export interface SecurityReport {
  id: string;
  filename: string;
  created_at: Timestamp;
  target: string;
  target_type: TargetType;
  analysis_type: AnalysisType;
  results: Record<string, AnalysisResult>;
  summary: {
    risk_score: RiskScore;
    risk_level: RiskLevel;
    key_findings: string[];
  };
  report_content?: string; // Markdown content
}

// ==========================================
// Wallet/Address Data Interfaces
// ==========================================

export interface TokenBalance {
  mint: string;
  symbol: string;
  name?: string;
  amount: number;
  decimals: number;
  usd_value?: number;
  logo_uri?: string;
}

export interface NFT {
  mint: string;
  name: string;
  image_uri?: string;
  collection?: string;
  attributes?: Record<string, any>;
}

export interface WalletData {
  address: string;
  sol_balance: number;
  sol_balance_usd: number;
  first_transaction_date?: Timestamp;
  last_transaction_date?: Timestamp;
  total_transactions: number;
  token_balances: TokenBalance[];
  nfts?: NFT[];
  program_interactions: ProgramInteraction[];
  transactions: Transaction[];
  labels?: string[];
  risk_score?: RiskScore;
  risk_level?: RiskLevel;
}

// ==========================================
// API Response Interfaces
// ==========================================

export interface ApiErrorResponse {
  success: false;
  error: string;
  status?: number;
}

export interface AnalysisApiResponse {
  success: true;
  target: string;
  target_type: TargetType;
  analysis_type: AnalysisType;
  results: Record<string, any>; // Maps analysis_type to result object
  report_path?: string;
  timestamp: Timestamp;
}

export interface ReportListApiResponse {
  reports: Array<{
    id: string;
    filename: string;
    created_at: Timestamp | null;
  }>;
}

export interface ReportApiResponse {
  id: string;
  filename: string;
  created_at: Timestamp;
  target: string;
  target_type: TargetType;
  analysis_type: AnalysisType;
  report_path: string;
}

export interface SearchApiResponse {
  success: true;
  query: string;
  results: Array<{
    address: string;
    tags: string[];
    notes?: string;
    risk_score?: RiskScore;
  }>;
}

// Unified API response type
export type ApiResponse = 
  | ApiErrorResponse
  | AnalysisApiResponse
  | ReportListApiResponse
  | ReportApiResponse
  | SearchApiResponse;
