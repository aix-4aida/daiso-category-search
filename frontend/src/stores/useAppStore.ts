import { create } from 'zustand';
import type { Screen, Product, MapInfo, QueryInfo, Waypoint } from '../types';
import { fetchSearch } from '../services/api';
import { buildWaypoints, KIOSK_POSITION } from '../utils/pathfinding';

interface AppState {
  screen: Screen;
  query: string;
  results: Product[];
  selectedProduct: Product | null;
  isListening: boolean;
  mapInfo: MapInfo | null;
  queryInfo: QueryInfo | null;
  error: string | null;

  search: (query: string) => Promise<void>;
  setScreen: (screen: Screen) => void;
  selectProduct: (product: Product) => void;
  reset: () => void;
  setListening: (listening: boolean) => void;
  setQuery: (query: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  screen: 'home',
  query: '',
  results: [],
  selectedProduct: null,
  isListening: false,
  mapInfo: null,
  queryInfo: null,
  error: null,

  search: async (query: string) => {
    set({ query, screen: 'loading', error: null });
    try {
      const response = await fetchSearch(query);
      const message = response.message
        ?? (response.results.length === 0 ? '검색 결과가 없습니다.' : null);
      set({
        results: response.results,
        mapInfo: response.map_info,
        queryInfo: response.query_info,
        screen: response.results.length > 0 ? 'results' : 'home',
        error: message,
      });
    } catch {
      set({ screen: 'home', error: '검색 중 오류가 발생했습니다.' });
    }
  },

  setScreen: (screen: Screen) => set({ screen }),

  selectProduct: (product: Product) => {
    const state = useAppStore.getState();
    let mapInfo = state.mapInfo;

    // Recalculate mapInfo if product has location data
    if (product.destination_x != null && product.destination_y != null && mapInfo) {
      const path = buildWaypoints(product.destination_x, product.destination_y);
      const waypoints: Waypoint[] = path.map(p => ({ x: p.x, y: p.y }));
      mapInfo = {
        ...mapInfo,
        floor: product.location_floor ?? mapInfo.floor,
        map_image: `/static/maps/map_${(product.location_floor ?? mapInfo.floor).toLowerCase()}.jpg`,
        counter_number: product.counter_number,
        section_description: product.location_description ?? '',
        destination: { x: product.destination_x, y: product.destination_y },
        start: { x: KIOSK_POSITION.x, y: KIOSK_POSITION.y },
        waypoints,
      };
    }

    set({ selectedProduct: product, mapInfo, screen: 'map' });
  },

  reset: () =>
    set({
      screen: 'home',
      query: '',
      results: [],
      selectedProduct: null,
      isListening: false,
      mapInfo: null,
      queryInfo: null,
      error: null,
    }),

  setListening: (listening: boolean) => set({ isListening: listening }),

  setQuery: (query: string) => set({ query }),
}));
