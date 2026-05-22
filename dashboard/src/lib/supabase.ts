import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://your-project-id.supabase.co";
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "your-anon-key";

export const supabase = createClient(supabaseUrl, supabaseKey);

export type Shop = {
  id: number;
  name: string;
  yandex_folder: string;
};

export type DialogScore = {
  id: number;
  shop_id: number;
  original_audio_file: string;
  dialog_index: number;
  audio_url: string;
  clean_text: string;
  speakers_involved: string[];
  score: number;
  tags: string[];
  text_analysis: string;
  audit_details?: {
    cross_sales_score?: number;
    upsell_score?: number;
    christmas_tree_score?: number;
    promo_score?: number;
    loyalty_score?: number;
    order_duplication_score?: number;
    live_service_score?: number;
    additional_service?: string;
    critical_errors?: string;
    dialogue_type?: string;
    emotion_stats?: string;
    is_conflict?: boolean;
  };
  transcript?: {
    start: number;
    end: number;
    speaker: string;
    text: string;
  }[];
  created_at: string;
};

export type AppStatus = {
  id: number;
  is_analyzing: boolean;
  status_message: string;
  last_run_at: string;
};

export type AgentTelemetry = {
  id: number;
  agent_name: string;
  status: string;
  active_task?: string;
  created_at?: string;
  updated_at?: string;
};

