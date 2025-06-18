// MainChatArea-api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

// Generate a simple 9-character chat ID
export const generateChatId = () => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 9; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

// Create a new chat
export const createNewChat = async () => {
  const chatId = generateChatId();
  const response = await fetch(`${API_BASE_URL}/chats`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chatId,
      title: 'New Chat',
      createdAt: new Date().toISOString(),
      messages: []
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to create new chat');
  }

  const data = await response.json();
  return { chatId, ...data };
};

// Get all chats
export const getAllChats = async () => {
  const response = await fetch(`${API_BASE_URL}/chats`);

  if (!response.ok) {
    throw new Error('Failed to fetch chats');
  }

  const data = await response.json();
  return data;
};

// Get a specific chat by ID
export const getChatById = async (chatId) => {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch chat');
  }

  const data = await response.json();
  return data;
};

// Save a message to a chat and receive AI response
export const saveMessage = async (chatId, userMessage) => {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userMessage), // Send only the user message initially
  });

  if (!response.ok) {
    throw new Error('Failed to save message or get AI response');
  }

  // The backend will now return the AI message directly
  const data = await response.json();
  return data; // This 'data' will be the AI message
};