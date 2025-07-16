import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export async function initLangGraph() {
  try {
    const url = import.meta.env.DEV
      ? import.meta.env.VITE_API_URL
      : import.meta.env.VITE_API_URL_PROD;
    const response = await fetch(`${url}/ingest`);
    const data = await response.json();
    if (!data.message) {
      throw new Error('Failed to ingest data');
    }
  } catch (error) {
    console.error('Failed to initialize LangGraph:', error);
  }
}
