import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  FiSearch,
  FiPlus,
  FiX,
  FiSave,
  FiTrash2,
  FiDownload,
  FiMenu,
  FiLock,
  FiUnlock,
  FiSun,
  FiMoon,
  FiCode,
  FiClock,
  FiPlay,
} from 'react-icons/fi';
import { useTheme } from './hooks/useTheme';
import PromptExplorer from './components/PromptExplorer';
import EditorPanel from './components/EditorPanel';
import DocumentProperties from './components/DocumentProperties';
import ExportModal from './components/ExportModal';
import RevisionCommentModal from './components/RevisionCommentModal';
import VersionHistoryModal from './components/VersionHistoryModal';
import AlertModal from './components/AlertModal';
import ConfirmModal from './components/ConfirmModal';
import VariableSetsModal from './components/VariableSetsModal';
import VariableSetsSelector from './components/VariableSetsSelector';
import RenderModal from './components/RenderModal';
import './App.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface Document {
  id: string;
  name: string;
  content: string;
  metadata: {
    description: string;
    tags: string[];
    owner?: string;
    revisionComments?: string;
  };
  isDirty: boolean;
  isLocked: boolean;
  savedAt?: string;
  previousVersionId?: string;
  variableSetIds?: string[];
  variableOverrides?: Record<string, Record<string, string>>;
}

interface Prompt {
  name: string;
  content: string;
  description: string;
  tags: string[];
  owner?: string;
  source_ref?: string;
  updated_at?: string;
}

const App: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  // Initialize documents and activeDocId from localStorage
  const [documents, setDocuments] = useState<Document[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem('editor-documents');
      const docs = saved ? JSON.parse(saved) : [];
      // Filter out Untitled documents - they should not persist across sessions
      const filtered = docs.filter((doc: Document) => doc.name !== 'Untitled');
      // Clear isDirty flag when loading from localStorage (except for new/unsaved docs)
      // New documents (Untitled or never saved) should stay marked as unsaved
      // Also reset lock state - it's a session-specific UI state
      return filtered.map((doc: Document) => ({
        ...doc,
        isDirty: (doc.name === 'Untitled' || !doc.savedAt) ? true : false,
        isLocked: false, // Reset lock state when reloading from storage
      }));
    }
    return [];
  });

  const [activeDocId, setActiveDocId] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return window.localStorage.getItem('editor-active-doc-id');
    }
    return null;
  });
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(false);
  const [showProperties, setShowProperties] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showRevisionComment, setShowRevisionComment] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [pendingSaveDocId, setPendingSaveDocId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Variable Sets
  const [variableSets, setVariableSets] = useState<VariableSet[]>([]);
  const [showVariableSetsModal, setShowVariableSetsModal] = useState(false);
  const [showVariableSetSelector, setShowVariableSetSelector] = useState(false);
  const [showRenderModal, setShowRenderModal] = useState(false);

  // Modal state
  const [alertModal, setAlertModal] = useState<{ isOpen: boolean; title: string; message: string }>({
    isOpen: false,
    title: '',
    message: '',
  });
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    confirmText?: string;
    cancelText?: string;
    isDangerous?: boolean;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });

  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingSavesRef = useRef<Set<string>>(new Set());
  const isSavingRef = useRef<boolean>(false);

  // Persist ONLY saved documents to localStorage (must have savedAt timestamp)
  // This ensures closed tabs don't reopen - they must be saved to persist
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const documentsToSave = documents.filter((doc) => doc.savedAt && doc.name !== 'Untitled');
      console.log('Persisting to localStorage:', documentsToSave.length, 'saved documents');
      window.localStorage.setItem('editor-documents', JSON.stringify(documentsToSave));
    }
  }, [documents]);

  // Persist active doc ID to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (activeDocId) {
        window.localStorage.setItem('editor-active-doc-id', activeDocId);
      } else {
        window.localStorage.removeItem('editor-active-doc-id');
      }
    }
  }, [activeDocId]);

  // Load prompts on mount and setup offline/online listeners
  useEffect(() => {
    loadPrompts(true); // Show loading state on initial load only
    loadTags();
    loadVariableSets();

    // Setup offline/online listeners
    const handleOnline = () => {
      setIsOnline(true);
      // Retry pending saves
      retryPendingSaves();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);


  const loadPrompts = async (showLoadingState = false) => {
    if (showLoadingState) setLoading(true);
    try {
      const response = await fetch('/api/prompts');
      const data = await response.json();
      const loadedPrompts = data.prompts || [];

      // Filter out known invalid prompts (Untitled, empty names) - case insensitive
      const validPrompts = loadedPrompts.filter(
        (p: Prompt) => p.name && p.name.toLowerCase() !== 'untitled' && p.name.trim()
      );

      setPrompts(validPrompts);
    } catch (error) {
      console.error('Error loading prompts:', error);
    } finally {
      if (showLoadingState) setLoading(false);
    }
  };

  const loadTags = async () => {
    try {
      const response = await fetch('/api/tags');
      const data = await response.json();
      setAllTags(data.tags || []);
    } catch (error) {
      console.error('Error loading tags:', error);
    }
  };

  const loadVariableSets = async () => {
    try {
      const response = await fetch('/api/variable-sets');
      const data = await response.json();
      setVariableSets(data.variable_sets || []);
    } catch (error) {
      console.error('Error loading variable sets:', error);
    }
  };

  const getActiveDocument = (): Document | undefined => {
    return documents.find((d) => d.id === activeDocId);
  };

  const getMergedVariables = (): Record<string, string> => {
    const activeDoc = getActiveDocument();
    if (!activeDoc) return {};

    const setIds = activeDoc.variableSetIds || [];
    const overrides = activeDoc.variableOverrides || {};
    let merged: Record<string, string> = {};

    // Merge variables from each active set
    for (const setId of setIds) {
      const varSet = variableSets.find((vs) => vs.id === setId);
      if (varSet) {
        merged = { ...merged, ...varSet.variables };
      }

      // Apply overrides for this set (overrides win)
      const setOverrides = overrides[setId] || {};
      merged = { ...merged, ...setOverrides };
    }

    return merged;
  };

  const createNewDocument = () => {
    console.log('createNewDocument called, current documents count:', documents.length);
    const defaultTemplate = `#! Add a description of your prompt here

<system>
You are a helpful assistant specializing in [[DOMAIN]].
</system>

<context>
[[CONTEXT]]
</context>

<instruction>
[[PROMPT: instructions]]
</instruction>

<examples>
[[PROMPT_TAG: examples, reference]]
</examples>

<output>
[[PROMPT: output-format]]
</output>`;

    const newDoc: Document = {
      id: `doc-${Date.now()}`,
      name: 'Untitled',
      content: defaultTemplate,
      metadata: {
        description: '',
        tags: [],
      },
      isDirty: true,
      isLocked: false,
    };
    console.log('Adding new document:', newDoc);
    setDocuments([...documents, newDoc]);
    setActiveDocId(newDoc.id);
    setShowProperties(true);
    console.log('New document created, activeDocId set to:', newDoc.id, 'Properties modal opened');
  };

  const updateDocument = (id: string, updates: Partial<Document>) => {
    const oldDoc = documents.find((d) => d.id === id);

    setDocuments(
      documents.map((doc) => {
        if (doc.id === id) {
          const newIsDirty = updates.content !== undefined ? true : doc.isDirty;
          if (oldDoc && oldDoc.isDirty !== newIsDirty) {
            console.log(`[updateDocument] isDirty changed: ${oldDoc.isDirty} → ${newIsDirty} for doc ${id}`);
          }
          return {
            ...doc,
            ...updates,
            // Deep merge metadata if it's being updated
            metadata: updates.metadata
              ? { ...doc.metadata, ...updates.metadata }
              : doc.metadata,
            // Only mark dirty if content actually changed (typing)
            // isDirty is only cleared by explicit backend persistence (saveDocument)
            isDirty: newIsDirty,
          };
        }
        return doc;
      })
    );

    // Reset auto-save timer whenever user types (debounce pattern)
    const doc = documents.find((d) => d.id === id);
    if (doc && updates.content !== undefined) {
      console.log(`[updateDocument] Content changed for doc ${id}, setting debounce timer (doc is "${doc.name}")`);
      // Content changed - reset the timer
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }

      if (doc.name && doc.name !== 'Untitled') {
        autoSaveTimerRef.current = setTimeout(() => {
          const currentDoc = documents.find((d) => d.id === id);
          console.log(`[autoSaveTimer] Timer fired for doc ${id}:`, {
            exists: !!currentDoc,
            isDirty: currentDoc?.isDirty,
            isSaving: isSavingRef.current,
            name: currentDoc?.name,
          });
          if (currentDoc && currentDoc.isDirty && !isSavingRef.current) {
            console.log(`[autoSaveTimer] Calling saveDocument for ${id}`);
            saveDocument(id);
          } else if (currentDoc && !currentDoc.isDirty) {
            console.log(`[autoSaveTimer] Skipping save - isDirty is false for ${id}`);
          }
          autoSaveTimerRef.current = null;
        }, 2000);
      } else {
        console.log(`[updateDocument] Skipping timer for "${doc.name}" - is Untitled or invalid`);
      }
    }
  };

  const saveDocument = async (id: string, revisionComment?: string, skipOverwriteCheck?: boolean, updatedName?: string, isManualSave: boolean = false) => {
    // Prevent concurrent saves
    if (isSavingRef.current) {
      console.log('[saveDocument] Save already in progress, skipping');
      return;
    }

    isSavingRef.current = true;

    const doc = documents.find((d) => d.id === id);
    if (!doc) {
      console.log('[saveDocument] Document not found for id:', id);
      isSavingRef.current = false;
      return;
    }

    // Use updatedName if provided (for cases where state might not be updated yet)
    const docName = updatedName || doc.name;

    console.log('[saveDocument] CALLED with:', {
      id,
      currentName: doc.name,
      currentIsDirty: doc.isDirty,
      updatedName,
      docName,
      revisionComment,
      source: new Error().stack?.split('\n')[2]?.trim(),
    });

    // Prevent saving documents with invalid names
    if (!docName || docName.toLowerCase() === 'untitled' || !docName.trim()) {
      console.warn('BLOCKING SAVE - Invalid name:', { docName, updatedName, docActualName: doc.name });
      setAlertModal({
        isOpen: true,
        title: 'Name Required',
        message: 'Please give your prompt a name before saving.',
      });
      return;
    }

    // Check if a prompt with this name already exists (and it's not a newly created document without savedAt)
    const isNewDocument = !doc.savedAt;
    const existingPrompt = prompts.find((p) => p.name.toLowerCase() === docName.toLowerCase());

    if (existingPrompt && isNewDocument && !skipOverwriteCheck) {
      setConfirmModal({
        isOpen: true,
        title: 'Overwrite Existing Prompt?',
        message: `A prompt named "${docName}" already exists. Do you want to overwrite it?`,
        confirmText: 'Overwrite',
        cancelText: 'Rename',
        isDangerous: true,
        onConfirm: () => saveDocument(id, revisionComment, true, docName, true),
      });
      return;
    }

    try {
      const response = await fetch(`/api/prompts/${docName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: doc.content,
          metadata: {
            ...doc.metadata,
            revisionComments: revisionComment,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log(`[saveDocument] Backend save successful for ${id}, isManualSave: ${isManualSave}`);
        // Manual saves clear isDirty, auto-saves do not
        setDocuments(
          documents.map((d) => {
            if (d.id === id) {
              const newIsDirty = isManualSave ? false : d.isDirty;
              console.log(`[saveDocument] Updating doc ${id}: savedAt: ${data.timestamp}, isDirty: ${d.isDirty} → ${newIsDirty} (isManualSave: ${isManualSave})`);
              return {
                ...d,
                isDirty: newIsDirty,
                savedAt: data.timestamp,
                metadata: {
                  ...d.metadata,
                  revisionComments: revisionComment,
                },
              };
            }
            return d;
          })
        );
        // Remove from pending if it was queued
        pendingSavesRef.current.delete(id);
        // Refresh the search list so the new/updated document appears
        loadPrompts(false);
      } else {
        console.error('Save failed:', response.status, response.statusText);
        // Queue for retry if offline
        if (!isOnline) {
          pendingSavesRef.current.add(id);
          console.log('Queued for retry when online:', id);
        } else {
          setAlertModal({
            isOpen: true,
            title: 'Save Failed',
            message: `Failed to save: ${response.statusText}`,
          });
        }
      }
    } catch (error) {
      console.error('Error saving document:', error);
      // Queue for retry if offline or network error
      if (!isOnline || error instanceof TypeError) {
        pendingSavesRef.current.add(id);
        console.log('Queued for retry when online:', id);
      } else {
        setAlertModal({
          isOpen: true,
          title: 'Save Error',
          message: 'Error saving document. Check console for details.',
        });
      }
    } finally {
      isSavingRef.current = false;
    }
  };

  const retryPendingSaves = async () => {
    const pendingIds = Array.from(pendingSavesRef.current);
    if (pendingIds.length === 0) return;

    console.log(`Retrying ${pendingIds.length} pending saves...`);
    for (const docId of pendingIds) {
      const doc = documents.find((d) => d.id === docId);
      if (doc) {
        await saveDocument(docId);
      }
    }
  };

  const promptRevisionComment = (id: string) => {
    const doc = documents.find((d) => d.id === id);
    if (!doc) return;

    // If new/untitled document, open properties first
    if (doc.name === 'Untitled') {
      setActiveDocId(id);
      setShowProperties(true);
      setPendingSaveDocId(id);
    } else {
      // For existing documents, go straight to revision comment
      setPendingSaveDocId(id);
      setShowRevisionComment(true);
    }
  };

  const deleteDocument = (id: string) => {
    const doc = documents.find((d) => d.id === id);
    if (!doc) return;

    setConfirmModal({
      isOpen: true,
      title: 'Delete Prompt?',
      message: `Delete "${doc.name}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      isDangerous: true,
      onConfirm: () => {
        // Show second confirmation
        setConfirmModal({
          isOpen: true,
          title: 'Are you absolutely sure?',
          message: 'This will permanently delete the document. This cannot be undone.',
          confirmText: 'Delete Forever',
          cancelText: 'Cancel',
          isDangerous: true,
          onConfirm: async () => {
            try {
              // For unsaved documents (Untitled or never saved), just remove from editor
              if (doc.name === 'Untitled' || !doc.savedAt) {
                setDocuments(documents.filter((d) => d.id !== id));
                if (activeDocId === id) {
                  setActiveDocId(documents[0]?.id || null);
                }
                return;
              }

              // For saved documents, delete from backend first
              const response = await fetch(`/api/prompts/${encodeURIComponent(doc.name)}`, { method: 'DELETE' });

              if (!response.ok) {
                console.error('Delete response:', response.status, response.statusText);
                // Still remove from UI even if backend delete fails
                setDocuments(documents.filter((d) => d.id !== id));
                if (activeDocId === id) {
                  setActiveDocId(documents[0]?.id || null);
                }
                setPrompts(prompts.filter((p) => p.name !== doc.name));

                setAlertModal({
                  isOpen: true,
                  title: 'Delete Removed from UI',
                  message: `Document removed from editor. Note: Backend delete failed (${response.statusText}). Refresh to verify.`,
                });
                return;
              }

              setDocuments(documents.filter((d) => d.id !== id));
              if (activeDocId === id) {
                setActiveDocId(documents[0]?.id || null);
              }

              // Remove from prompts list silently (no visible refresh)
              setPrompts(prompts.filter((p) => p.name !== doc.name));
            } catch (error) {
              console.error('Error deleting document:', error);
              setAlertModal({
                isOpen: true,
                title: 'Delete Error',
                message: 'Error deleting document. Check console for details.',
              });
            }
          },
        });
      },
    });
  };

  const closeDocument = (id: string) => {
    console.log('closeDocument called for:', id);
    const doc = documents.find((d) => d.id === id);
    if (doc?.isLocked) return;

    // Clear auto-save timer for this document
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
      autoSaveTimerRef.current = null;
    }

    if (doc?.isDirty) {
      setConfirmModal({
        isOpen: true,
        title: 'Close Unsaved Document?',
        message: `Close "${doc.name}"? You have unsaved changes.`,
        confirmText: 'Close',
        cancelText: 'Keep Open',
        isDangerous: true,
        onConfirm: () => {
          setDocuments(documents.filter((d) => d.id !== id));
          if (activeDocId === id) {
            const remaining = documents.filter((d) => d.id !== id);
            setActiveDocId(remaining[0]?.id || null);
          }
        },
      });
      return;
    }

    console.log('Closing document:', id, '| Current docs before close:', documents.length);
    setDocuments(documents.filter((d) => d.id !== id));
    console.log('Documents state updated, should now be:', documents.length - 1, 'documents');
    if (activeDocId === id) {
      const remaining = documents.filter((d) => d.id !== id);
      console.log('Switching activeDocId from', activeDocId, 'to', remaining[0]?.id || null);
      setActiveDocId(remaining[0]?.id || null);
    }
  };

  const toggleLockDocument = (id: string) => {
    updateDocument(id, { isLocked: !getActiveDocument()?.isLocked });
  };

  const handlePromptSelect = async (prompt: Prompt) => {
    // Check if this prompt is already open in a document
    const existingDoc = documents.find((d) => d.name === prompt.name);
    if (existingDoc) {
      // Switch to existing document instead of opening a new one
      setActiveDocId(existingDoc.id);
      return;
    }
    // Otherwise, load it as a new document
    loadPromptIntoEditor(prompt);
  };

  const loadPromptIntoEditor = async (prompt: Prompt) => {
    // If content is not loaded, fetch it from the API
    let content = prompt.content;
    if (!content) {
      try {
        const response = await fetch(`/api/prompts/${prompt.name}`);
        if (response.ok) {
          const data = await response.json();
          content = data.content || '';
        } else if (response.status === 404) {
          setAlertModal({
            isOpen: true,
            title: 'Prompt Not Found',
            message: `Prompt "${prompt.name}" not found on server. It may have been deleted.`,
          });
          // Remove this prompt from the list immediately
          setPrompts(prompts.filter((p) => p.name !== prompt.name));
          return;
        } else {
          console.error('Error loading prompt:', response.status);
          setAlertModal({
            isOpen: true,
            title: 'Load Failed',
            message: `Failed to load prompt: ${response.statusText}`,
          });
          return;
        }
      } catch (error) {
        console.error('Error loading prompt content:', error);
        setAlertModal({
          isOpen: true,
          title: 'Load Error',
          message: 'Error loading prompt. Check console for details.',
        });
        return;
      }
    }

    const doc: Document = {
      id: `doc-${Date.now()}`,
      name: prompt.name,
      content: content || '',
      metadata: prompt as any,
      isDirty: false,
      isLocked: false,
      savedAt: new Date().toISOString(),
    };
    console.log('loadPromptIntoEditor: Adding document:', doc.id, 'name:', doc.name);
    setDocuments([...documents, doc]);
    console.log('loadPromptIntoEditor: Setting activeDocId to:', doc.id);
    setActiveDocId(doc.id);
    console.log('loadPromptIntoEditor: Complete - state updates queued');
  };

  const exportPrompts = async (filters: { tags: string[]; names: string[] }) => {
    try {
      const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters),
      });

      if (response.ok) {
        const data = await response.json();
        downloadJSON(data, 'prompts-export.json');
      }
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  const downloadJSON = (data: any, filename: string) => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const activeDoc = getActiveDocument();

  return (
    <div className="app-container">
      {/* Header with Branding and Theme Toggle */}
      <div className="app-header">
        <div className="app-branding">
          <h1>PAMBL</h1>
        </div>
        {!isOnline && (
          <div
            className="offline-indicator"
            title={`Offline - ${pendingSavesRef.current.size} pending saves`}
          >
            ⚠ Offline - Changes saved locally
          </div>
        )}
        <button
          className="btn-icon"
          onClick={() => setShowVariableSetsModal(true)}
          title="Manage Variable Sets"
        >
          <FiCode size={20} />
          Variables
        </button>
        <button
          className="btn-theme-toggle"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? <FiMoon size={20} /> : <FiSun size={20} />}
        </button>
      </div>
      <div className="app-layout">
        {/* Left Panel - Prompt Explorer */}
        <div className="left-panel">
          <PromptExplorer
            prompts={prompts}
            allTags={allTags}
            searchQuery={searchQuery}
            selectedTags={selectedTags}
            loading={loading}
            activePromptName={activeDoc?.name}
            openDocumentNames={documents.map((d) => d.name)}
            onSearchChange={setSearchQuery}
            onTagsChange={setSelectedTags}
            onPromptSelect={handlePromptSelect}
            onNewPrompt={createNewDocument}
            onRefresh={loadPrompts}
          />
        </div>

        {/* Right Panel - Editor */}
        <div className="right-panel">
          <div className="editor-header">
            <div className="tabs-container">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`tab ${activeDocId === doc.id ? 'active' : ''}`}
                  onClick={() => setActiveDocId(doc.id)}
                >
                  <span className="tab-name">{doc.name}</span>
                  {doc.isDirty && <span className="tab-dirty">●</span>}
                  <button
                    className="tab-lock"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleLockDocument(doc.id);
                    }}
                  >
                    {doc.isLocked ? <FiLock size={14} /> : <FiUnlock size={14} />}
                  </button>
                  <button
                    className="tab-close"
                    onClick={(e) => {
                      e.stopPropagation();
                      closeDocument(doc.id);
                    }}
                  >
                    <FiX size={14} />
                  </button>
                </div>
              ))}
            </div>

            {activeDoc && (
              <div className="editor-toolbar">
                <button
                  className="btn btn-primary"
                  onClick={() => setShowProperties(true)}
                  title="Document Properties"
                >
                  <FiMenu size={18} />
                  Properties
                </button>
                {activeDoc.isDirty && (
                  <button
                    className="btn btn-success"
                    onClick={() => promptRevisionComment(activeDocId!)}
                  >
                    <FiSave size={18} />
                    Save
                  </button>
                )}
                {activeDoc.savedAt && (
                  <button
                    className="btn btn-danger"
                    onClick={() => deleteDocument(activeDocId!)}
                    title="Delete this document"
                  >
                    <FiTrash2 size={18} />
                    Delete
                  </button>
                )}
                <button
                  className="btn btn-info"
                  onClick={() => setShowExport(true)}
                >
                  <FiDownload size={18} />
                  Export
                </button>
                <button
                  className="btn btn-default"
                  onClick={() => setShowVariableSetSelector(true)}
                  title="Select and override variable sets"
                >
                  <FiCode size={18} />
                  Variables
                </button>
                <button
                  className="btn btn-default"
                  onClick={() => setShowRenderModal(true)}
                  title="Render prompt with variable substitution"
                >
                  <FiPlay size={18} />
                  Render
                </button>
                <div style={{ marginLeft: 'auto' }} />
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowVersionHistory(true)}
                  title="View version history and revision comments"
                >
                  <FiClock size={18} />
                  History
                </button>
              </div>
            )}
          </div>

          {activeDoc ? (
            <EditorPanel
              document={activeDoc}
              allPrompts={prompts}
              onContentChange={(content) =>
                updateDocument(activeDocId!, { content })
              }
              onBookmarkJump={(line) => {
                // Jump to line with bookmark comment
                console.log('Jump to line:', line);
              }}
            />
          ) : (
            <div className="empty-state">
              <button className="btn btn-primary btn-large" onClick={createNewDocument}>
                <FiPlus size={24} />
                Create New Prompt
              </button>
              <p>Or select a prompt from the left panel</p>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {activeDoc && showProperties && (
        <DocumentProperties
          document={activeDoc}
          allTags={allTags}
          allPromptNames={prompts.map((p) => p.name)}
          onSave={(data) => {
            console.log('DocumentProperties onSave called with:', {
              dataName: data.name,
              dataDescription: data.description,
              activeDocId,
              currentDocName: activeDoc.name,
            });
            updateDocument(activeDocId!, {
              name: data.name,
              metadata: {
                description: data.description,
                tags: data.tags,
                owner: data.owner,
              },
            });
            setShowProperties(false);
            // If this was a pending save, proceed with actual save
            if (pendingSaveDocId === activeDocId) {
              console.log('Calling saveDocument with updatedName:', data.name);
              saveDocument(activeDocId!, undefined, undefined, data.name, true);
              setPendingSaveDocId(null);
            }
          }}
          onClose={() => {
            setShowProperties(false);
            setPendingSaveDocId(null);
          }}
        />
      )}

      {showExport && (
        <ExportModal
          onExport={exportPrompts}
          allTags={allTags}
          onClose={() => setShowExport(false)}
        />
      )}

      {showRevisionComment && pendingSaveDocId && (
        <RevisionCommentModal
          previousComment={documents.find((d) => d.id === pendingSaveDocId)?.metadata.revisionComments}
          onSave={(comment) => {
            saveDocument(pendingSaveDocId, comment, undefined, undefined, true);
            setShowRevisionComment(false);
            setPendingSaveDocId(null);
          }}
          onCancel={() => {
            setShowRevisionComment(false);
            setPendingSaveDocId(null);
          }}
        />
      )}

      {showVersionHistory && activeDoc && (
        <VersionHistoryModal
          currentRevisionComment={activeDoc.metadata.revisionComments}
          currentSavedAt={activeDoc.savedAt}
          onRevert={(revisionComment) => {
            // When reverting, the current version becomes part of history
            // For now, this will update the metadata with the selected revision
            updateDocument(activeDocId!, {
              metadata: {
                ...activeDoc.metadata,
                revisionComments: revisionComment,
              },
            });
          }}
          onClose={() => setShowVersionHistory(false)}
        />
      )}

      {/* Variable Sets Modal */}
      <VariableSetsModal
        isOpen={showVariableSetsModal}
        onClose={() => setShowVariableSetsModal(false)}
        onVariableSetsChanged={loadVariableSets}
      />

      {/* Variable Sets Selector (per-document) */}
      {activeDoc && (
        <VariableSetsSelector
          isOpen={showVariableSetSelector}
          onClose={() => setShowVariableSetSelector(false)}
          allVariableSets={variableSets}
          onSave={(ids, overrides) => {
            updateDocument(activeDocId!, {
              variableSetIds: ids,
              variableOverrides: overrides,
            });
          }}
        />
      )}

      {/* Render Modal */}
      {activeDoc && (
        <RenderModal
          isOpen={showRenderModal}
          content={activeDoc.content}
          variables={getMergedVariables()}
          allPrompts={prompts}
          documents={documents}
          variableSets={variableSets}
          onClose={() => setShowRenderModal(false)}
        />
      )}

      {/* Alert Modal */}
      <AlertModal
        isOpen={alertModal.isOpen}
        title={alertModal.title}
        message={alertModal.message}
        onClose={() => setAlertModal({ ...alertModal, isOpen: false })}
      />

      {/* Confirm Modal */}
      <ConfirmModal
        isOpen={confirmModal.isOpen}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={() => {
          confirmModal.onConfirm();
          setConfirmModal({ ...confirmModal, isOpen: false });
        }}
        onCancel={() => setConfirmModal({ ...confirmModal, isOpen: false })}
        confirmText={confirmModal.confirmText}
        cancelText={confirmModal.cancelText}
        isDangerous={confirmModal.isDangerous}
      />
    </div>
  );
};

export default App;
