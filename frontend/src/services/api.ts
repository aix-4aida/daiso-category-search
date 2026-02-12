import type { SearchResponse, Product, Category, HealthStatus } from '../types';

const API_BASE = '/api';

export async function fetchSearch(query: string): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function fetchProducts(skip = 0, limit = 50): Promise<Product[]> {
  const res = await fetch(`${API_BASE}/products?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error(`Products fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchProduct(id: number): Promise<Product> {
  const res = await fetch(`${API_BASE}/products/${id}`);
  if (!res.ok) throw new Error(`Product fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error(`Categories fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}
