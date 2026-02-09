const API_BASE_URL = 'http://localhost:8000/api';

export const searchProducts = async (query) => {
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

export const getProductsByCategory = async (category) => {
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

export const getProductById = async (id) => {
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
