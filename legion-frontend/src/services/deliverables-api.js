// services/deliverables-api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

export const getDeliverables = async (chatId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/research/${chatId}/deliverables`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching deliverables:', error);
    throw error;
  }
};

export const getDeliverable = async (chatId, deliverableId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/research/${chatId}/deliverables/${deliverableId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching deliverable:', error);
    throw error;
  }
};

export const downloadDeliverable = async (chatId, deliverableId, filename) => {
  try {
    const response = await fetch(`${API_BASE_URL}/research/${chatId}/deliverables/${deliverableId}/download`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename || 'deliverable.md';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading deliverable:', error);
    throw error;
  }
};