import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

function parseInline(text: string): React.ReactNode[] {
  // Split text on **bold** and `code` spans so we can render them as React elements
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-extrabold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={index} className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-red-600 font-mono text-[10px]">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const lines = content.split('\n');
  const renderedElements: React.ReactNode[] = [];
  
  let listType: 'ul' | 'ol' | null = null;
  let listItems: React.ReactNode[] = [];

  const flushList = (key: string | number) => {
    if (listItems.length > 0) {
      if (listType === 'ul') {
        renderedElements.push(
          <ul key={`ul-${key}`} className="list-style-none my-1.5 space-y-1.5">
            {listItems}
          </ul>
        );
      } else if (listType === 'ol') {
        renderedElements.push(
          <ol key={`ol-${key}`} className="list-style-none my-1.5 space-y-1.5">
            {listItems}
          </ol>
        );
      }
      listItems = [];
      listType = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      flushList(i);
      continue;
    }

    // Headings: ###, ##, #
    if (trimmed.startsWith('### ')) {
      flushList(i);
      renderedElements.push(
        <h3 key={i} className="font-bold text-slate-800 text-[12px] mt-4 mb-1">
          {parseInline(trimmed.substring(4))}
        </h3>
      );
    } else if (trimmed.startsWith('## ')) {
      flushList(i);
      renderedElements.push(
        <h2 key={i} className="font-extrabold text-slate-900 text-sm mt-5 mb-1.5">
          {parseInline(trimmed.substring(3))}
        </h2>
      );
    } else if (trimmed.startsWith('# ')) {
      flushList(i);
      renderedElements.push(
        <h1 key={i} className="font-black text-slate-900 text-base mt-6 mb-2">
          {parseInline(trimmed.substring(2))}
        </h1>
      );
    }
    // Unordered list item starting with * or -
    else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (listType !== 'ul') {
        flushList(i);
        listType = 'ul';
      }
      const itemContent = trimmed.substring(2);
      listItems.push(
        <li key={`li-${i}`} className="flex items-start gap-2 text-slate-650 leading-relaxed pl-1">
          <span className="text-blue-500 mt-1 select-none font-bold text-[10px]">•</span>
          <span className="flex-1">{parseInline(itemContent)}</span>
        </li>
      );
    }
    // Ordered list item starting with a number (e.g. 1. item)
    else if (/^\d+\.\s+/.test(trimmed)) {
      if (listType !== 'ol') {
        flushList(i);
        listType = 'ol';
      }
      const match = trimmed.match(/^(\d+)\.\s+/);
      const num = match ? match[1] : '1';
      const itemContent = trimmed.substring(match ? match[0].length : 3);
      listItems.push(
        <li key={`li-${i}`} className="flex items-start gap-2 text-slate-650 leading-relaxed pl-1">
          <span className="text-blue-500 font-bold select-none text-[11px]">{num}.</span>
          <span className="flex-1">{parseInline(itemContent)}</span>
        </li>
      );
    }
    // Regular paragraph
    else {
      flushList(i);
      renderedElements.push(
        <p key={i} className="my-1.5 text-slate-650 leading-relaxed">
          {parseInline(trimmed)}
        </p>
      );
    }
  }

  // Flush remaining list items at the end of the content
  flushList('end');

  return <div className="text-[12px] text-slate-750 font-sans space-y-1.5">{renderedElements}</div>;
}
