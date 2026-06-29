interface CurrencyInputProps {
  value: number;
  onChange: (value: number) => void;
  placeholder?: string;
  min?: number;
  className?: string;
  autoFocus?: boolean;
}

export function CurrencyInput({
  value,
  onChange,
  placeholder,
  className,
  autoFocus,
}: CurrencyInputProps) {
  return (
    <input
      type="text"
      inputMode="numeric"
      value={value || ""}
      onChange={e => {
        const digits = e.target.value.replace(/\D/g, "");
        onChange(digits === "" ? 0 : Number(digits));
      }}
      placeholder={placeholder}
      className={className}
      autoFocus={autoFocus}
    />
  );
}
