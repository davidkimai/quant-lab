/**
 * API client for Quant Lab backend.
 * 
 * Provides methods for:
 * - Fetching available strategies
 * - Running backtests with Server-Sent Events (SSE) streaming
 */

import type { Strategy, BacktestRequest, BacktestEvent } from '../types';

const API_BASE_URL = '/api';

/**
 * Fetch all available trading strategies.
 */
export async function fetchStrategies(): Promise<Strategy[]> {
  const response = await fetch(`${API_BASE_URL}/strategies`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch strategies');
  }
  
  return response.json();
}

/**
 * Run a backtest with Server-Sent Events (SSE) streaming.
 * 
 * Yields progress events as the backtest executes, followed by final results.
 * 
 * @param request - Backtest parameters
 * @param onEvent - Callback for each SSE event
 */
export async function runBacktest(
  request: BacktestRequest,
  onEvent: (event: BacktestEvent) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/backtest/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('Failed to start backtest');
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  // Parse SSE stream
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // Process complete SSE messages
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      // Parse SSE format: "event: type\ndata: payload"
      const eventMatch = line.match(/event:\s*(\w+)/);
      const dataMatch = line.match(/data:\s*(.+)/);
      
      if (!eventMatch || !dataMatch) continue;
      
      const eventType = eventMatch[1];
      const eventData = dataMatch[1];
      
      try {
        const parsedData = JSON.parse(eventData);
        
        if (eventType === 'progress') {
          onEvent({ type: 'progress', data: parsedData });
        } else if (eventType === 'complete') {
          onEvent({ type: 'complete', data: parsedData });
        } else if (eventType === 'error') {
          onEvent({ type: 'error', data: eventData });
        }
      } catch (error) {
        console.error('Failed to parse SSE data:', error);
      }
    }
  }
}
