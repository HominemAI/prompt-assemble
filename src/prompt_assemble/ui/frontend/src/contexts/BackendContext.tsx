import React, { createContext, useContext } from 'react';
import { PromptBackend } from '../utils/api';

interface BackendContextType {
  backend: PromptBackend;
  backendMode: 'local' | 'remote' | 'filesystem';
}

const BackendContext = createContext<BackendContextType | undefined>(undefined);

export const BackendProvider: React.FC<{
  children: React.ReactNode;
  backend: PromptBackend;
  backendMode: 'local' | 'remote' | 'filesystem';
}> = ({ children, backend, backendMode }) => {
  return (
    <BackendContext.Provider value={{ backend, backendMode }}>
      {children}
    </BackendContext.Provider>
  );
};

export const useBackend = (): BackendContextType => {
  const context = useContext(BackendContext);
  if (!context) {
    throw new Error('useBackend must be used within a BackendProvider');
  }
  return context;
};

export default BackendContext;
