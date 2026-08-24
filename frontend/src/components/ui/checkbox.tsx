import React from "react";

interface CheckboxProps {
  id?: string;
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ id, checked, onCheckedChange, disabled }, ref) => (
    <input
      ref={ref}
      id={id}
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      disabled={disabled}
    />
  )
);

Checkbox.displayName = "Checkbox";
