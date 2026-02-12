export type Screen = 'home' | 'loading' | 'results' | 'map';

export interface Product {
  id: number;
  rank: number;
  name: string;
  price: number;
  image_url: string;
  category_major: string | null;
  category_middle: string | null;
  score: number;
}

export interface MapInfo {
  floor: string;
  section: string;
  map_image: string;
}

export interface QueryInfo {
  original: string;
  intent: string;
  keywords: string[];
}

export interface SearchResponse {
  results: Product[];
  map_info: MapInfo | null;
  query_info: QueryInfo | null;
  message?: string | null;
}

export interface Category {
  major: string;
  middles: string[];
}

export interface HealthStatus {
  status: string;
  services: Record<string, boolean>;
}
