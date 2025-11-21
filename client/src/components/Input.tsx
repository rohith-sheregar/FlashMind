import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  className = "",
  ...props
}) => (
  <div className="w-full">
    {label && (
      <label className="block text-sm font-medium text-slate-700 mb-1">
        {label}
      </label>
    )}
    <input
      className={`w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all ${className}`}
      {...props}
    />
  </div>
);
