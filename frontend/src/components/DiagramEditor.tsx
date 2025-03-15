import React from 'react';
import Editor from '@monaco-editor/react';
import { Box } from '@mui/material';
import { configureMonacoEditor } from '../utils/editorConfig';

interface DiagramEditorProps {
  value: string;
  onChange: (value: string) => void;
  syntaxType: string;
}

const DiagramEditor: React.FC<DiagramEditorProps> = ({ value, onChange, syntaxType }) => {
  // Configure editor on component mount
  React.useEffect(() => {
    configureMonacoEditor();
  }, []);

  const handleEditorWillMount = (monaco: any) => {
    // Set theme based on syntax type
    monaco.editor.setTheme(syntaxType === 'mermaid' ? 'mermaidLight' : 'plantumlLight');
  };

  return (
    <Box sx={{ height: '100%', overflow: 'hidden' }}>
      <Editor
        height="100%"
        defaultLanguage={syntaxType}
        value={value}
        onChange={(value) => onChange(value || '')}
        beforeMount={handleEditorWillMount}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          renderLineHighlight: 'all',
          matchBrackets: 'always',
          autoClosingBrackets: 'always',
          autoClosingQuotes: 'always',
          folding: true,
          foldingHighlight: true,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          wrappingIndent: 'same',
          automaticLayout: true,
          tabSize: 2,
          guides: {
            bracketPairs: true,
            indentation: true
          },
          scrollbar: {
            vertical: 'auto',
            horizontal: 'auto',
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
            useShadows: true
          },
          padding: {
            top: 8,
            bottom: 8
          },
          bracketPairColorization: {
            enabled: true
          }
        }}
      />
    </Box>
  );
};

export default DiagramEditor;