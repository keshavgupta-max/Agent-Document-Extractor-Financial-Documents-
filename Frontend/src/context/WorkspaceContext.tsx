"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { DEFAULT_WORKSPACE_ID, WORKSPACE_STORAGE_KEY } from "@/lib/constants";

interface WorkspaceContextType {
  workspaceId: string;
  setWorkspaceId: (id: string) => void;
  selectedDocumentIds: string[];
  setSelectedDocumentIds: (ids: string[]) => void;
  isInitialized: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaceId, setWorkspaceIdState] = useState<string>(DEFAULT_WORKSPACE_ID);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [isInitialized, setIsInitialized] = useState<boolean>(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(WORKSPACE_STORAGE_KEY);
      if (stored && stored.trim()) {
        setWorkspaceIdState(stored.trim());
      } else {
        localStorage.setItem(WORKSPACE_STORAGE_KEY, DEFAULT_WORKSPACE_ID);
      }
    } catch {
      // Fallback gracefully if localStorage is unavailable
    } finally {
      setIsInitialized(true);
    }
  }, []);

  const setWorkspaceId = (id: string) => {
    const cleanId = id.trim() || DEFAULT_WORKSPACE_ID;
    setWorkspaceIdState(cleanId);
    setSelectedDocumentIds([]); // Reset selection when switching workspace
    try {
      localStorage.setItem(WORKSPACE_STORAGE_KEY, cleanId);
    } catch {
      // Ignore storage errors
    }
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaceId,
        setWorkspaceId,
        selectedDocumentIds,
        setSelectedDocumentIds,
        isInitialized,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace(): WorkspaceContextType {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}