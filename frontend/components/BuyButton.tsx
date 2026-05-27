import React from 'react';

interface BuyButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export default function BuyButton({ onClick, disabled = false }: BuyButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="mt-auto bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-2 rounded-md hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Comprar
    </button>
  );
}
