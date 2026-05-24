

interface CodeBlockProps {
  code: string;
  language?: string;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, className = '' }) => {
  return (
    <pre className={`code-block ${className}`}>
      <code>{code}</code>
    </pre>
  );
};
