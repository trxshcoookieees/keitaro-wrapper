export interface StreamOffer {
  id: number;
  offer_id: number;
  offer_name: string;
  share: number;
  is_active: boolean;
  is_pinned: boolean;
}

export interface Campaign {
  id: number;
  keitaro_id: number | null;
  name: string;
  domain_id: number | null;
  group_id: number | null;
  traffic_source_id: number | null;
  is_active: boolean;
  is_dirty: boolean;
  streams: Stream[];
}

export interface Stream {
  id: number;
  keitaro_id: number | null;
  campaign_id: number;
  name: string;
  type: string;
  schema: string;
  action_type: string;
  action_payload: string | null;
  is_active: boolean;
  is_dirty: boolean;
  offers: StreamOffer[];
}

export interface CampaignCreate {
  name: string;
  geo_codes: string[];
  offer_ids: number[];
  domain_id: number;
  group_id: number;
  traffic_source_id: number;
}

export interface CatalogOption {
  id: number;
  name: string;
}

export interface Offer {
  id: number;
  name: string;
}