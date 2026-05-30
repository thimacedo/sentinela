import React from 'react';

type ButtonProps = {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
};

export default function Button({ children, onClick, disabled = false, className = '' }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        px-4 py-2 rounded-xl
        bg-white/10 backdrop-blur-sm border border-white/20
        text-white font-medium transition-all duration-200
        hover:bg-white/20 hover:border-white/40 hover:shadow-lg hover:shadow-white/10
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    >
      {children}
    </button>
  );
}
