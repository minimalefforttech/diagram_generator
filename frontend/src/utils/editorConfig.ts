import { loader } from "@monaco-editor/react";

export const configureMonacoEditor = (darkMode: boolean = false) => {
  loader.init().then((monaco) => {
    // Register Mermaid language
    monaco.languages.register({ id: 'mermaid' });
    monaco.languages.setMonarchTokensProvider('mermaid', {
      tokenizer: {
        root: [
          [/[\{\[\(\}\]\)]/, 'delimiter'],
          [/[A-Z][a-zA-Z0-9_$]*/, 'type'],
          [/".*?"/, 'string'],
          [/'.*?'/, 'string'],
          [/(%%).*$/, 'comment'],
          [/---/, 'keyword'],
          [/--?>/, 'keyword'],
          [/===>/, 'keyword'],
          [/-\.->/, 'keyword'],
          [/==>/, 'keyword'],
          [/-->/, 'keyword'],
          [/->/, 'keyword'],
          [/graph\s+(TB|BT|RL|LR|TD)/, 'keyword'],
          [/\b(subgraph|end|style|classDef|linkStyle|class)\b/, 'keyword'],
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
          // Special tag handling
          [/(@(?:start|end))(uml|mindmap|wbs|gantt|salt)/, ['keyword', 'type']],
          
          // Declarations
          [/\b(class|interface|enum|abstract|package|namespace)\b/, 'keyword'],
          [/\b(actor|boundary|control|entity|database|collections)\b/, 'keyword'],
          [/\b(private|protected|public)\b/, 'keyword'],
          
          // Delimiters and operators
          [/[{}[\]]/, 'delimiter'],
          [/".*?"/, 'string'],
          [/'.*?'/, 'string'],
          [/!.*$/, 'comment'],
          [/'.*$/, 'comment'],
          
          // Arrows and connections
          [/<-[-.]+>/, 'keyword'],
          [/-[-.]+>/, 'keyword'],
          [/<[-.]+-/, 'keyword'],
          [/[<>*#]+/, 'operator'],
          
          // Commands and styling
          [/\b(skinparam|title|header|footer|note|legend)\b/, 'keyword'],
          [/\b(left|right|top|bottom|of|on|style)\b/, 'keyword'],
          
          // Colors and styling properties
          [/#[\da-fA-F]{3,6}/, 'color'],
          [/\b(BackgroundColor|BorderColor|FontColor|FontSize|FontStyle)\b/, 'style-prop'],
          
          // Additional PlantUML keywords
          [/\b(start|stop|if|else|endif|fork|join|split|end)\b/, 'keyword'],
          [/:[^:]+:/, 'string'],  // Activity labels
          [/(?:<<).+?(?:>>)/, 'type'],  // Stereotypes
          [/\b(?:\d+\.?\d*(?:ms|s|m|h|d|w|M|y))\b/, 'number'],  // Time units
          [/[-+]?(?:\d*\.)?\d+/, 'number'],  // Numbers
        ],
      },
    });

    // Create light and dark themes for both languages
    monaco.editor.defineTheme('mermaidLight', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '0000FF', fontStyle: 'bold' },
        { token: 'string', foreground: 'A31515' },
        { token: 'comment', foreground: '008000', fontStyle: 'italic' },
        { token: 'type', foreground: '267F99' },
        { token: 'delimiter', foreground: '000000' },
        { token: 'style-prop', foreground: 'AF00DB' },
        { token: 'color', foreground: 'B21919' },
      ],
      colors: {
        'editor.foreground': '#000000',
        'editor.background': '#FFFFFF',
      }
    });

    monaco.editor.defineTheme('plantumlLight', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '0000FF', fontStyle: 'bold' },
        { token: 'string', foreground: 'A31515' },
        { token: 'comment', foreground: '008000', fontStyle: 'italic' },
        { token: 'type', foreground: '4EC9B0' },
        { token: 'operator', foreground: 'CF1010' },
        { token: 'delimiter', foreground: '000000' },
        { token: 'style-prop', foreground: 'AF00DB' },
        { token: 'color', foreground: 'B21919' },
        { token: 'number', foreground: '098658' },
      ],
      colors: {
        'editor.foreground': '#000000',
        'editor.background': '#FFFFFF',
      }
    });

    monaco.editor.defineTheme('mermaidDark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
        { token: 'type', foreground: '4EC9B0' },
        { token: 'delimiter', foreground: 'FFFFFF' },
        { token: 'style-prop', foreground: 'C586C0' },
        { token: 'color', foreground: 'D16969' },
      ],
      colors: {
        'editor.foreground': '#D4D4D4',
        'editor.background': '#1E1E1E',
      }
    });

    monaco.editor.defineTheme('plantumlDark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
        { token: 'type', foreground: '4EC9B0' },
        { token: 'operator', foreground: 'FF6B6B' },
        { token: 'delimiter', foreground: 'FFFFFF' },
        { token: 'style-prop', foreground: 'C586C0' },
        { token: 'color', foreground: 'D16969' },
        { token: 'number', foreground: 'B5CEA8' },
      ],
      colors: {
        'editor.foreground': '#D4D4D4',
        'editor.background': '#1E1E1E',
      }
    });
  });
};