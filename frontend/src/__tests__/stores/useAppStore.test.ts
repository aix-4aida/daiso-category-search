import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAppStore } from '../../stores/useAppStore';

vi.mock('../../services/api', () => ({
  fetchSearch: vi.fn(),
}));

import { fetchSearch } from '../../services/api';

const mockedFetchSearch = vi.mocked(fetchSearch);

beforeEach(() => {
  useAppStore.getState().reset();
  vi.clearAllMocks();
});

describe('useAppStore', () => {
  it('should start with home screen', () => {
    const state = useAppStore.getState();
    expect(state.screen).toBe('home');
    expect(state.query).toBe('');
    expect(state.results).toEqual([]);
  });

  it('should set screen', () => {
    useAppStore.getState().setScreen('loading');
    expect(useAppStore.getState().screen).toBe('loading');
  });

  it('should set query', () => {
    useAppStore.getState().setQuery('물티슈');
    expect(useAppStore.getState().query).toBe('물티슈');
  });

  it('should set listening state', () => {
    useAppStore.getState().setListening(true);
    expect(useAppStore.getState().isListening).toBe(true);
  });

  it('should search and update results', async () => {
    mockedFetchSearch.mockResolvedValue({
      results: [
        {
          id: 1, rank: 1, name: '물티슈', price: 1000,
          image_url: '/img.jpg', category_major: '뷰티/위생',
          category_middle: '화장지/물티슈', score: 0.9,
        },
      ],
      map_info: { floor: '1F', section: '뷰티/위생', map_image: '/map.png' },
      query_info: { original: '물티슈', intent: 'search', keywords: ['물티슈'] },
    });

    await useAppStore.getState().search('물티슈');
    const state = useAppStore.getState();
    expect(state.screen).toBe('results');
    expect(state.results).toHaveLength(1);
    expect(state.mapInfo?.section).toBe('뷰티/위생');
  });

  it('should go back to home on empty results', async () => {
    mockedFetchSearch.mockResolvedValue({
      results: [],
      map_info: null,
      query_info: { original: 'xyz', intent: 'search', keywords: ['xyz'] },
    });

    await useAppStore.getState().search('xyz');
    const state = useAppStore.getState();
    expect(state.screen).toBe('home');
    expect(state.error).toBe('검색 결과가 없습니다.');
  });

  it('should show server message for non-search intent', async () => {
    mockedFetchSearch.mockResolvedValue({
      results: [],
      map_info: null,
      query_info: { original: '안녕하세요', intent: 'not_search', keywords: [] },
      message: '상품 위치 검색만 도와드릴 수 있어요. 찾으시는 상품명을 말씀해 주세요!',
    });

    await useAppStore.getState().search('안녕하세요');
    const state = useAppStore.getState();
    expect(state.screen).toBe('home');
    expect(state.error).toBe('상품 위치 검색만 도와드릴 수 있어요. 찾으시는 상품명을 말씀해 주세요!');
  });

  it('should handle search error', async () => {
    mockedFetchSearch.mockRejectedValue(new Error('Network error'));

    await useAppStore.getState().search('test');
    const state = useAppStore.getState();
    expect(state.screen).toBe('home');
    expect(state.error).toBe('검색 중 오류가 발생했습니다.');
  });

  it('should select product and go to map', () => {
    const product = {
      id: 1, rank: 1, name: '물티슈', price: 1000,
      image_url: '/img.jpg', category_major: '뷰티/위생',
      category_middle: '화장지/물티슈', score: 0.9,
      counter_number: null, destination_x: null, destination_y: null,
      location_floor: null, location_description: null,
    };

    useAppStore.getState().selectProduct(product);
    const state = useAppStore.getState();
    expect(state.screen).toBe('map');
    expect(state.selectedProduct?.name).toBe('물티슈');
  });

  it('should recalculate mapInfo when selecting product with location', () => {
    // First set up mapInfo from a search
    useAppStore.setState({
      mapInfo: {
        floor: 'B1', section: '뷰티/위생', map_image: '/maps/map_b1.jpg',
        counter_number: 1, section_description: '화장품 코너',
        destination: { x: 0.82, y: 0.18 }, start: { x: 0.45, y: 0.05 },
        waypoints: [{ x: 0.45, y: 0.05 }, { x: 0.82, y: 0.05 }, { x: 0.82, y: 0.18 }],
      },
    });

    const product = {
      id: 5, rank: 2, name: '샴푸', price: 2000,
      image_url: '/img2.jpg', category_major: '뷰티/위생',
      category_middle: '헤어/바디', score: 0.8,
      counter_number: 6, destination_x: 0.82, destination_y: 0.20,
      location_floor: 'B1', location_description: '화장품 코너',
    };

    useAppStore.getState().selectProduct(product);
    const state = useAppStore.getState();
    expect(state.mapInfo?.counter_number).toBe(6);
    expect(state.mapInfo?.destination?.x).toBe(0.82);
    expect(state.mapInfo?.destination?.y).toBe(0.20);
    expect(state.mapInfo?.waypoints?.length).toBeGreaterThanOrEqual(3);
  });

  it('should reset all state', () => {
    useAppStore.getState().setScreen('results');
    useAppStore.getState().setQuery('물티슈');
    useAppStore.getState().reset();
    const state = useAppStore.getState();
    expect(state.screen).toBe('home');
    expect(state.query).toBe('');
    expect(state.results).toEqual([]);
  });
});
