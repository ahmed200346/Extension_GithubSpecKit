import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * WebSocket hook for real-time updates from the backend.
 * Falls back to polling if WebSocket is not available.
 */
export const useWebSocket = (url, options = {}) => {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectInterval = 5000,
    enabled = true,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const messageHandlerRef = useRef(onMessage);

  // Keep message handler updated
  useEffect(() => {
    messageHandlerRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = (event) => {
        setIsConnected(true);
        if (onOpen) onOpen(event);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          if (messageHandlerRef.current) {
            messageHandlerRef.current(data);
          }
        } catch (err) {
          console.warn('WebSocket message parse error:', err);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        if (onClose) onClose(event);
        
        // Reconnect logic
        if (reconnect && enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (event) => {
        if (onError) onError(event);
      };
    } catch (err) {
      console.error('WebSocket connection error:', err);
      setIsConnected(false);
    }
  }, [url, enabled, reconnect, reconnectInterval, onOpen, onClose, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => {
      disconnect();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect, disconnect, enabled]);

  return {
    isConnected,
    lastMessage,
    send,
    connect,
    disconnect,
  };
};

export default useWebSocket;