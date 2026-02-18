// Nginx 프록시를 통한 상대 경로 사용 (HTTPS Mixed Content 방지)
const API_BASE_URL = '/api';

interface Product {
    id: string | number;
    name: string;
    price?: number;
    location?: string;
    image_url?: string;
    category_major?: string;
    category_middle?: string;
}

export const searchProducts = async (query: string): Promise<Product[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        return [];
    }
};

export const getProductsByCategory = async (category: string): Promise<Product[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/products/category/${encodeURIComponent(category)}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        return [];
    }
};

export const getProductById = async (id: string | number): Promise<Product | null> => {
    try {
        const response = await fetch(`${API_BASE_URL}/products/${id}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        return null;
    }
};

export const getCategories = async (): Promise<{ categories: { id: string; name: string }[] }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/categories`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error("API Error (getCategories):", error);
        return { categories: [] };
    }
};

export const processTextSearch = async (text: string): Promise<any> => {
    try {
        const response = await fetch(`${API_BASE_URL}/search/process_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error("API Error (processTextSearch):", error);
        return { error: error instanceof Error ? error.message : String(error) };
    }
};

