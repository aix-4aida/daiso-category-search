import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchSearch, fetchProducts, fetchHealth } from '../../services/api';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

describe('fetchSearch', () => {
  it('should POST query and return results', async () => {
    const mockResponse = {
      results: [{ id: 1, name: '물티슈', rank: 1, price: 1000 }],
      map_info: null,
      query_info: { original: '물티슈', intent: 'search', keywords: ['물티슈'] },
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchSearch('물티슈');
    expect(result.results).toHaveLength(1);
    expect(mockFetch).toHaveBeenCalledWith('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: '물티슈' }),
    });
  });

  it('should throw on error response', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500 });
    await expect(fetchSearch('test')).rejects.toThrow('Search failed: 500');
  });
});

describe('fetchProducts', () => {
  it('should GET products with pagination', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ id: 1, name: '물티슈' }]),
    });

    const result = await fetchProducts(0, 10);
    expect(result).toHaveLength(1);
    expect(mockFetch).toHaveBeenCalledWith('/api/products?skip=0&limit=10');
  });
});

describe('fetchHealth', () => {
  it('should GET health status', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok', services: { database: true } }),
    });

    const result = await fetchHealth();
    expect(result.status).toBe('ok');
  });
});
