import { loader } from '@monaco-editor/react';

// Define language configurations for Monaco editor
export const configureMonacoEditor = (isDarkMode = true) => {
  loader.init().then((monaco) => {
    // Register Mermaid language
    monaco.languages.register({ id: 'mermaid' });
    monaco.languages.setMonarchTokensProvider('mermaid', {
      tokenizer: {
        root: [
          [/^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|mindmap|timeline)/, 'keyword'],
          [/[{}[\]]/, 'delimiter'],
          [/[<>]+/, 'angle'],
          [/".*?"/, 'string'],
          [/'.*?'/, 'string'],
          [/-->|==>|-.->|===>|-.->/, 'arrow'],
          [/\|[\w\s]*\|/, 'actor'],
          [/\[[^\]]*\]/, 'square-bracket'],
          [/\([^)]*\)/, 'parenthesis'],
          [/style\s+\w+/, 'style'],
          [/class\s+\w+/, 'class'],
          [/\b(participant|actor|boundary|control|entity|database)\b/, 'keyword'],
          [/#[\da-fA-F]{3,6}/, 'color'],
          [/\b(fill|stroke|color|background)\b/, 'style-prop'],
        ],
      },
    });

    // Register PlantUML language
    monaco.languages.register({ id: 'plantuml' });
    monaco.languages.setMonarchTokensProvider('plantuml', {
      tokenizer: {
        root: [
          [/@start(uml|mindmap|wbs|gantt|salt)/, 'keyword'],
          [/@end(uml|mindmap|wbs|gantt|salt)/, 'keyword'],
          [/\b(class|interface|enum|abstract|package|namespace)\b/, 'keyword'],
          [/\b(actor|boundary|control|entity|database|collections)\b/, 'keyword'],
          [/[{}[\]]/, 'delimiter'],
          [/".*?"/, 'string'],
          [/'.*?'/, 'string'],
          [/-[->]+|<[=-]+|=[=>]+/, 'arrow'],
          [/:[^:]+:/, 'stereotype'],
          [/\b(public|private|protected|static|final)\b/, 'modifier'],
          [/#[\da-fA-F]{3,6}/, 'color'],
          [/\b(skinparam|style)\b/, 'style'],
        ],
      },
    });

    // Configure light theme
    monaco.editor.defineTheme('mermaidLight', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '0D47A1', fontStyle: 'bold' },
        { token: 'arrow', foreground: '1976D2' },
        { token: 'actor', foreground: '00695C' },
        { token: 'string', foreground: '2E7D32' },
        { token: 'style', foreground: '9C27B0' },
        { token: 'style-prop', foreground: '0277BD' },
        { token: 'color', foreground: '2E7D32' },
        { token: 'delimiter', foreground: '000000' },
        { token: 'class', foreground: '00695C' },
      ],
      colors: {
        'editor.background': '#FFFFFF',
        'editor.foreground': '#000000',
        'editorLineNumber.foreground': '#6E6E6E',
        'editorLineNumber.activeForeground': '#000000',
        'editor.selectionBackground': '#ADD6FF',
        'editor.inactiveSelectionBackground': '#E5EBF1',
        'editor.lineHighlightBackground': '#F5F5F5',
        'editorCursor.foreground': '#000000',
        'editorWhitespace.foreground': '#BFBFBF',
        'editorIndentGuide.background': '#D3D3D3'
      },
    });

    // Configure dark theme
    monaco.editor.defineTheme('mermaidDark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },
        { token: 'arrow', foreground: '569CD6' },
        { token: 'actor', foreground: '4EC9B0' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'style', foreground: 'C586C0' },
        { token: 'style-prop', foreground: '9CDCFE' },
        { token: 'color', foreground: 'CE9178' },
        { token: 'delimiter', foreground: 'D4D4D4' },
        { token: 'class', foreground: '4EC9B0' },
      ],
      colors: {
        'editor.background': '#1E1E1E',
        'editor.foreground': '#D4D4D4',
        'editorLineNumber.foreground': '#858585',
        'editorLineNumber.activeForeground': '#C6C6C6',
        'editor.selectionBackground': '#264F78',
        'editor.inactiveSelectionBackground': '#3A3D41',
        'editor.lineHighlightBackground': '#2D2D2D',
        'editorCursor.foreground': '#AEAFAD',
        'editorWhitespace.foreground': '#404040',
        'editorIndentGuide.background': '#404040'
      },
    });

    // Set the active theme based on mode
    monaco.editor.setTheme(isDarkMode ? 'mermaidDark' : 'mermaidLight');
  });
};